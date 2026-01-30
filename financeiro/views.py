from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.db.models import Sum, Q
from datetime import timedelta, datetime
from .models import FechamentoCaixa, Movimentacao, Categoria
from .forms import MovimentacaoRapidaForm, FechamentoSaldoForm, CategoriaForm, FiltroResumoForm

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
        if fechamento_atual.saldo_inicial != fechamento_anterior.saldo_final_fisico:
            fechamento_atual.saldo_inicial = fechamento_anterior.saldo_final_fisico
            fechamento_atual.save()
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

    dia_anterior = obter_dia_anterior(data_atual)
    proximo_dia = obter_proximo_dia(data_atual)

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)

    form_mov = MovimentacaoRapidaForm()
    form_saldo = FechamentoSaldoForm(instance=fechamento)

    if request.method == 'POST':
        if 'btn_movimentacao' in request.POST:
            form_mov = MovimentacaoRapidaForm(request.POST)
            if form_mov.is_valid():
                nova_mov = form_mov.save(commit=False)
                nova_mov.fechamento = fechamento
                nova_mov.save()
                return redirect(request.path)
        
        elif 'btn_saldos' in request.POST:
            form_saldo = FechamentoSaldoForm(request.POST, instance=fechamento)
            if form_saldo.is_valid():
                obj = form_saldo.save(commit=False)
                transportar_saldo_anterior(obj)
                obj.save()
                return redirect(request.path)

    movs = fechamento.movimentacoes.all().select_related('categoria').order_by('id')
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    suprimentos = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    
    dinheiro_disponivel = fechamento.saldo_inicial + suprimentos
    miudos = (retiradas + fechamento.saldo_final_fisico) - dinheiro_disponivel
    if miudos < 0: miudos = 0
    total_geral = vendas_cartao + miudos

    # API de Categorias para o JS
    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/caderno.html', {
        'fechamento': fechamento,
        'movimentacoes': movs,
        'dia_anterior': dia_anterior,
        'proximo_dia': proximo_dia,
        'data_atual': data_atual,
        'data_atual_iso': data_atual.strftime('%Y-%m-%d'),
        'form_mov': form_mov,
        'form_saldo': form_saldo,
        'cats_json': categorias_json,
        'totais': {'cartao': vendas_cartao, 'entradas_esp': suprimentos, 'retiradas': retiradas, 'dinheiro_miudo': miudos, 'geral': total_geral}
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
    
    movs = fechamento.movimentacoes.all().select_related('categoria')
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    suprimentos = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    miudos = (retiradas + fechamento.saldo_final_fisico) - (fechamento.saldo_inicial + suprimentos)
    if miudos < 0: miudos = 0
    total_geral = vendas_cartao + miudos

    lista_movs = []
    for mov in movs.order_by('id'):
        lista_movs.append({
            'id': mov.id,
            'categoria': mov.categoria.nome, # Nome da Categoria
            'descricao': mov.descricao,      # Descrição opcional
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
        'saldos': {'inicial': float(fechamento.saldo_inicial), 'final': float(fechamento.saldo_final_fisico)},
        'totais': {'cartao': float(vendas_cartao), 'entradas_esp': float(suprimentos), 'dinheiro_miudo': float(miudos), 'retiradas': float(retiradas), 'geral': float(total_geral)},
        'movimentacoes': lista_movs
    })

@login_required
def resumo_financeiro(request):
    # 1. Definição das Datas (Padrão: Mês Atual)
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)
    
    data_inicio = request.GET.get('data_inicio', inicio_mes.strftime('%Y-%m-%d'))
    data_fim = request.GET.get('data_fim', hoje.strftime('%Y-%m-%d'))
    
    # Validação do Filtro
    form = FiltroResumoForm(initial={'data_inicio': data_inicio, 'data_fim': data_fim})
    if request.GET:
        form = FiltroResumoForm(request.GET)
        if form.is_valid():
            data_inicio = form.cleaned_data['data_inicio']
            data_fim = form.cleaned_data['data_fim']

    # 2. Busca Dados no Banco
    # Buscamos os dias fechados nesse período
    fechamentos = FechamentoCaixa.objects.filter(data__range=[data_inicio, data_fim])
    
    # Buscamos as movimentações dentro desses dias (já otimizado com select_related)
    movimentacoes = Movimentacao.objects.select_related('categoria').filter(fechamento__data__range=[data_inicio, data_fim])

    # === 3. OTIMIZAÇÃO: CÁLCULOS MATEMÁTICOS NO BANCO ===
    # O aggregate calcula todos os totais gerais de uma só vez no banco de dados.
    # Isso é muito mais rápido do que somar listas no Python.
    totais_gerais = movimentacoes.aggregate(
        soma_cartao=Sum('valor', filter=Q(tipo='CARTAO')),
        soma_saida=Sum('valor', filter=Q(tipo__in=['SAIDA', 'REGISTRO'])),
        soma_entrada=Sum('valor', filter=Q(tipo='DINHEIRO')),
        soma_saida_real=Sum('valor', filter=Q(tipo='SAIDA')) # Apenas saídas reais para o lucro
    )
    
    # Se o resultado for None (nenhuma venda), usamos 'or 0' para virar zero
    total_cartao = totais_gerais['soma_cartao'] or 0
    total_saida = totais_gerais['soma_saida'] or 0
    total_entrada = totais_gerais['soma_entrada'] or 0
    saidas_reais = totais_gerais['soma_saida_real'] or 0

    # === 4. PROCESSAMENTO VISUAL (TABELAS) ===
    # Mantemos essas queries para preencher as tabelinhas detalhadas por categoria
    # Mas não precisamos mais percorrer elas para somar o total
    cats_cartao = movimentacoes.filter(tipo='CARTAO').values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')
    cats_saida = movimentacoes.filter(tipo__in=['SAIDA', 'REGISTRO']).values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')
    cats_entrada = movimentacoes.filter(tipo='DINHEIRO').values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')

    # === 5. CÁLCULO DA VENDA EM DINHEIRO ===
    # (Lógica Matemática: Sobra + Saidas - Inicio - Entradas)
    # Este precisa ser dia-a-dia pois depende do saldo físico diário
    total_dinheiro_calc = 0
    for dia in fechamentos:
        # Aqui usamos o related manager direto do objeto dia
        movs_dia = dia.movimentacoes.all()
        
        # Pequena otimização local: somar no Python aqui é ok pois são poucos itens por dia
        suprimentos = sum(m.valor for m in movs_dia if m.tipo == 'DINHEIRO')
        retiradas = sum(m.valor for m in movs_dia if m.tipo == 'SAIDA')
        
        # Fórmula do Dinheiro
        venda_dia = (retiradas + dia.saldo_final_fisico) - (dia.saldo_inicial + suprimentos)
        if venda_dia < 0: venda_dia = 0 # Evita valores negativos se houve erro de contagem
        total_dinheiro_calc += venda_dia

    # Total Geral de Vendas (Cartão + Dinheiro Calculado)
    receita_total = total_cartao + total_dinheiro_calc

    # Resultado Líquido (Receita - Saídas Reais)
    lucro_operacional = receita_total - saidas_reais

    return render(request, 'financeiro/resumo.html', {
        'form': form,
        'cats_cartao': cats_cartao,
        'total_cartao': total_cartao,
        'cats_saida': cats_saida,
        'total_saida': total_saida,
        'cats_entrada': cats_entrada,
        'total_entrada': total_entrada,
        'total_dinheiro': total_dinheiro_calc,
        'receita_total': receita_total,
        'lucro_operacional': lucro_operacional,
        'dias_contados': fechamentos.count()
    })

@login_required
def deletar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    url = request.META.get('HTTP_REFERER', '/')
    mov.delete()
    return redirect(url)

@login_required
def editar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    
    if request.method == 'POST':
        form = MovimentacaoRapidaForm(request.POST, instance=mov)
        if form.is_valid():
            form.save()
            return redirect('caixa_dia', data_iso=mov.fechamento.data.strftime('%Y-%m-%d'))
    else:
        form = MovimentacaoRapidaForm(instance=mov)
    
    # Precisamos enviar as categorias para o JavaScript filtrar igual na tela principal
    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/editar_movimentacao.html', {
        'form': form, 
        'mov': mov,
        'cats_json': categorias_json
    })