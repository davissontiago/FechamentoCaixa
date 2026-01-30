from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.db.models import Sum, Q
from datetime import timedelta, datetime
from .models import FechamentoCaixa, Movimentacao, Categoria
from .forms import MovimentacaoRapidaForm, FechamentoSaldoForm, CategoriaForm, FiltroResumoForm
from .services import GestorCaixa

# === FUNÇÕES AUXILIARES ===
def obter_dia_anterior(data):
    anterior = data - timedelta(days=1)
    while anterior.weekday() == 6: anterior -= timedelta(days=1)
    return anterior

def obter_proximo_dia(data):
    proximo = data + timedelta(days=1)
    while proximo.weekday() == 6: proximo += timedelta(days=1)
    return proximo

def transportar_saldo_anterior(fechamento_atual):
    data_anterior_util = obter_dia_anterior(fechamento_atual.data)
    fechamento_anterior = FechamentoCaixa.objects.filter(data=data_anterior_util).first()
    
    if fechamento_anterior:
        if fechamento_atual.saldo_inicial != fechamento_anterior.saldo_final:
            fechamento_atual.saldo_inicial = fechamento_anterior.saldo_final
            fechamento_atual.save(update_fields=['saldo_inicial'])
            
    return fechamento_atual

# === VIEWS DE CATEGORIA ===
@login_required
def gerenciar_categorias(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_categorias')
    else:
        form = CategoriaForm()
    
    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'financeiro/categorias.html', {'form': form, 'categorias': categorias})

@login_required
def editar_categoria(request, id):
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    return render(request, 'financeiro/editar_categoria.html', {'form': form})

@login_required
def deletar_categoria(request, id):
    cat = get_object_or_404(Categoria, id=id)
    try:
        cat.delete()
    except:
        pass # Não deleta se estiver em uso
    return redirect('gerenciar_categorias')

# === CAIXA DIÁRIO ===
@login_required
def diario_caixa(request, data_iso=None):
    # --- [BLOCO 1: Tratamento de Data] ---
    if data_iso:
        try:
            data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
        except ValueError:
            return redirect('home')
    else:
        data_atual = timezone.now().date()
    
    if data_atual.weekday() == 6:
        proximo_util = obter_proximo_dia(data_atual)
        return redirect('caixa_dia', data_iso=proximo_util.strftime('%Y-%m-%d'))

    # --- [BLOCO 2: Preparação do Dia] ---
    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)

    gestor = GestorCaixa(fechamento)

    # --- [BLOCO 3: Processamento de Formulários] ---
    form_mov = MovimentacaoRapidaForm()
    form_saldo = FechamentoSaldoForm(instance=fechamento)

    if request.method == 'POST':
        if 'btn_movimentacao' in request.POST:
            form_mov = MovimentacaoRapidaForm(request.POST)
            if form_mov.is_valid():
                nova_mov = form_mov.save(commit=False)
                nova_mov.fechamento = fechamento
                nova_mov.save()
                
                # TAREFA 3: Atualizar o Cache (Performance)
                gestor.atualizar_cache_do_banco()

                return redirect(request.path)
        
        elif 'btn_saldos' in request.POST:
            form_saldo = FechamentoSaldoForm(request.POST, instance=fechamento)
            if form_saldo.is_valid():
                form_saldo.save()
                return redirect(request.path)

    # --- [BLOCO 4: Preparação para Exibir na Tela] ---
    
    resumo = gestor.calcular_resumo()

    # Buscamos as movimentações para a lista visual (Mantive o select_related para ser rápido)
    movs = fechamento.movimentacoes.all().select_related('categoria').order_by('id')
    
    # API para o Javascript (Mantive igual)
    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/caderno.html', {
        'fechamento': fechamento,
        'movimentacoes': movs,
        'dia_anterior': obter_dia_anterior(data_atual),
        'proximo_dia': obter_proximo_dia(data_atual),
        'data_atual': data_atual,
        'data_atual_iso': data_atual.strftime('%Y-%m-%d'),
        'form_mov': form_mov,
        'form_saldo': form_saldo,
        'cats_json': categorias_json,
        'totais': {'cartao': resumo['cartao'], 'entradas_esp': resumo['suprimentos'], 'retiradas': resumo['saidas'], 'dinheiro_miudo': resumo['dinheiro'], 'geral': resumo['total_geral']
}
    })

@login_required
def api_dados_caixa(request, data_iso):
    try:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'erro': 'Data inválida'}, status=400)

    if data_atual.weekday() == 6:
        data_atual = obter_proximo_dia(data_atual)
        data_iso = data_atual.strftime('%Y-%m-%d')

    dia_anterior_str = obter_dia_anterior(data_atual).strftime('%Y-%m-%d')
    proximo_dia_str = obter_proximo_dia(data_atual).strftime('%Y-%m-%d')

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)
    
    gestor = GestorCaixa(fechamento)
    resumo = gestor.calcular_resumo()
    
    movs = fechamento.movimentacoes.all().select_related('categoria').order_by('id')

    lista_movs = []
    for mov in movs.order_by('id'):
        lista_movs.append({
            'id': mov.id,
            'categoria': mov.categoria.nome if mov.categoria else 'Sem Categoria',
            'descricao': mov.descricao or '',
            'valor': float(mov.valor),
            'tipo': mov.tipo,
            'url_editar': f"/editar/{mov.id}/",  
            'url_deletar': f"/deletar/{mov.id}/"
        })

    data_texto = date_format(data_atual, format='l, d \d\e F', use_l10n=True).capitalize()

    return JsonResponse({
        'data_formatada': data_texto,
        'data_iso': data_iso,
        'nav': {'anterior': dia_anterior_str, 'proximo': proximo_dia_str, 'atual': data_iso},
        
        'saldos': {
            'inicial': float(fechamento.saldo_inicial), 
            'final': float(fechamento.saldo_final)
        },
        
        'totais': {
            'cartao': float(resumo['cartao']), 
            'entradas_esp': float(resumo['suprimentos']), 
            'dinheiro_miudo': float(resumo['dinheiro']), 
            'retiradas': float(resumo['saidas']), 
            'geral': float(resumo['total_geral'])
        },
        'movimentacoes': lista_movs
    })

@login_required
def resumo_financeiro(request):
    # 1. Datas e Filtros
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    data_inicio = request.GET.get('data_inicio', inicio_mes.strftime('%Y-%m-%d'))
    data_fim = request.GET.get('data_fim', hoje.strftime('%Y-%m-%d'))
    
    form = FiltroResumoForm(initial={'data_inicio': data_inicio, 'data_fim': data_fim})
    if request.GET:
        form = FiltroResumoForm(request.GET)
        if form.is_valid():
            data_inicio = form.cleaned_data['data_inicio']
            data_fim = form.cleaned_data['data_fim']

    # 2. Busca Otimizada
    fechamentos = FechamentoCaixa.objects.filter(data__range=[data_inicio, data_fim])
    
    # SOMA DIRETO NO BANCO
    somas_cache = fechamentos.aggregate(
        total_cartao=Sum('cache_total_cartao'),
        total_saida=Sum('cache_total_saida'),
        total_suprimento=Sum('cache_total_suprimento')
    )

    # 3. Totais Gerais (Sem loops!)
    total_cartao = somas_cache['total_cartao'] or 0
    total_saida = somas_cache['total_saida'] or 0
    total_suprimento = somas_cache['total_suprimento'] or 0
    
    # 4. Cálculo do Dinheiro (Dia a Dia)
    total_dinheiro_calc = 0
    
    for dia in fechamentos:
        # TAREFA: Aqui está a diferença! Não somamos mais as movimentações.
        # Usamos os valores que o GestorCaixa já calculou e salvou.
        
        suprimentos = dia.cache_total_suprimento
        retiradas = dia.cache_total_saida
        
        # Fórmula: (Saídas + Final) - (Inicial + Entradas)
        venda_dia = (retiradas + dia.saldo_final) - (dia.saldo_inicial + suprimentos)
        
        if venda_dia < 0: 
            venda_dia = 0
            
        total_dinheiro_calc += venda_dia

    # 5. Fechamento das Contas
    receita_total = total_cartao + total_dinheiro_calc
    lucro_operacional = receita_total - total_saida

    # Tabelinhas visuais (Mantivemos para ver os detalhes, mas não afetam o cálculo)
    movimentacoes = Movimentacao.objects.filter(fechamento__data__range=[data_inicio, data_fim])
    cats_cartao = movimentacoes.filter(tipo='CARTAO').values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')
    cats_saida = movimentacoes.filter(tipo__in=['SAIDA', 'REGISTRO']).values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')
    cats_entrada = movimentacoes.filter(tipo='DINHEIRO').values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')

    return render(request, 'financeiro/resumo.html', {
        'form': form,
        'cats_cartao': cats_cartao,
        'total_cartao': total_cartao,
        'cats_saida': cats_saida,
        'total_saida': total_saida,
        'cats_entrada': cats_entrada,
        'total_entrada': total_suprimento,
        'total_dinheiro': total_dinheiro_calc,
        'receita_total': receita_total,
        'lucro_operacional': lucro_operacional,
        'dias_contados': fechamentos.count()
    })

@login_required
def deletar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    
    fechamento_pai = mov.fechamento

    url = request.META.get('HTTP_REFERER', '/')

    mov.delete()

    gestor = GestorCaixa(fechamento_pai)
    gestor.atualizar_cache_do_banco()

    return redirect(url)

@login_required
def editar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    
    if request.method == 'POST':
        form = MovimentacaoRapidaForm(request.POST, instance=mov)
        if form.is_valid():
            mov_salva = form.save()
            
            gestor = GestorCaixa(mov_salva.fechamento)
            gestor.atualizar_cache_do_banco()
            
            return redirect('caixa_dia', data_iso=mov.fechamento.data.strftime('%Y-%m-%d'))
    else:
        form = MovimentacaoRapidaForm(instance=mov)
    
    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/editar_movimentacao.html', {
        'form': form, 
        'mov': mov,
        'cats_json': categorias_json
    })