from datetime import timedelta, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from django.db.models import Sum

from .models import FechamentoCaixa, Movimentacao, Categoria
from .forms import MovimentacaoForm, FechamentoSaldoForm, CategoriaForm, FiltroResumoForm
from .services import GestorCaixa

# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================

def obter_dia_anterior(data):
    """Retorna o dia anterior útil (pula domingo)."""
    anterior = data - timedelta(days=1)
    while anterior.weekday() == 6:  # 6 = Domingo
        anterior -= timedelta(days=1)
    return anterior

def obter_proximo_dia(data):
    """Retorna o próximo dia útil (pula domingo)."""
    proximo = data + timedelta(days=1)
    while proximo.weekday() == 6:
        proximo += timedelta(days=1)
    return proximo

def transportar_saldo_anterior(fechamento_atual):
    """Busca o saldo final do dia anterior e aplica como inicial do atual."""
    data_anterior_util = obter_dia_anterior(fechamento_atual.data)
    fechamento_anterior = FechamentoCaixa.objects.filter(data=data_anterior_util).first()
    
    if fechamento_anterior:
        if fechamento_atual.saldo_inicial != fechamento_anterior.saldo_final:
            fechamento_atual.saldo_inicial = fechamento_anterior.saldo_final
            fechamento_atual.save(update_fields=['saldo_inicial'])
            
    return fechamento_atual

# ==============================================================================
# VIEWS PRINCIPAIS (CAIXA DIÁRIO)
# ==============================================================================

@login_required
def diario_caixa(request, data_iso=None):
    """View principal do Caderno (Lista de Movimentações e Resumo)."""
    
    # 1. Tratamento de Data
    if data_iso:
        try:
            data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
        except ValueError:
            return redirect('home')
    else:
        data_atual = timezone.now().date()
    
    # Pula domingo se cair nele
    if data_atual.weekday() == 6:
        proximo_util = obter_proximo_dia(data_atual)
        return redirect('caixa_dia', data_iso=proximo_util.strftime('%Y-%m-%d'))

    # 2. Garante o Fechamento do dia
    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)

    # 3. Processa Formulário de Saldo (se enviado)
    form_saldo = FechamentoSaldoForm(instance=fechamento)
    
    if request.method == 'POST' and 'btn_saldos' in request.POST:
        form_saldo = FechamentoSaldoForm(request.POST, instance=fechamento)
        if form_saldo.is_valid():
            form_saldo.save()
            return redirect(request.path)

    # 4. Prepara dados para exibição
    gestor = GestorCaixa(fechamento)
    resumo = gestor.calcular_resumo()
    
    # Busca movimentações otimizadas
    movs = fechamento.movimentacoes.all().select_related('categoria').order_by('id')
    
    # Dados para JS (se necessário)
    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/caderno.html', {
        'fechamento': fechamento,
        'movimentacoes': movs,
        'dia_anterior': obter_dia_anterior(data_atual),
        'proximo_dia': obter_proximo_dia(data_atual),
        'data_atual': data_atual,
        'data_atual_iso': data_atual.strftime('%Y-%m-%d'),
        'form_saldo': form_saldo,
        'cats_json': categorias_json,
        'totais': {
            'cartao': resumo['cartao'], 
            'entradas_esp': resumo['suprimentos'], 
            'retiradas': resumo['saidas'], 
            'dinheiro_miudo': resumo['dinheiro'], 
            'geral': resumo['total_geral']
        }
    })

# ==============================================================================
# VIEWS DE MOVIMENTAÇÃO (CRIAR, EDITAR, DELETAR)
# ==============================================================================

@login_required
def salvar_movimentacao(request, data_iso):
    try:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    except ValueError:
        return redirect('home')

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST)
        if form.is_valid():
            nova_mov = form.save(commit=False)
            nova_mov.fechamento = fechamento
            nova_mov.save()
            GestorCaixa(fechamento).atualizar_cache_do_banco()
            return redirect('caixa_dia', data_iso=data_iso)
    else:
        form = MovimentacaoForm()

    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/movimentacoes/form.html', {
        'form': form,
        'titulo': 'Nova Movimentação',
        'data_iso': data_iso,
        'mov': None,
        'cats_json': categorias_json # <--- Importante!
    })

@login_required
def editar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    data_iso = mov.fechamento.data.strftime('%Y-%m-%d')
    
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST, instance=mov)
        if form.is_valid():
            form.save()
            GestorCaixa(mov.fechamento).atualizar_cache_do_banco()
            return redirect('caixa_dia', data_iso=data_iso)
    else:
        form = MovimentacaoForm(instance=mov)

    categorias_json = list(Categoria.objects.values('id', 'nome', 'tipo').order_by('nome'))

    return render(request, 'financeiro/movimentacoes/form.html', {
        'form': form,
        'titulo': f'Editar {mov.categoria.nome if mov.categoria else "Item"}',
        'data_iso': data_iso,
        'mov': mov,
        'cats_json': categorias_json # <--- Importante!
    })

@login_required
def deletar_movimentacao(request, id):
    """Remove uma movimentação e atualiza o cache."""
    mov = get_object_or_404(Movimentacao, id=id)
    fechamento_pai = mov.fechamento
    
    # Tenta voltar para onde estava, ou para a home
    url_retorno = request.META.get('HTTP_REFERER', '/')
    
    mov.delete()
    
    # Recalcula totais
    GestorCaixa(fechamento_pai).atualizar_cache_do_banco()
    
    return redirect(url_retorno)

# ==============================================================================
# API PARA O FRONTEND (AJAX)
# ==============================================================================

@login_required
def api_dados_caixa(request, data_iso):
    """Retorna JSON com todos os dados do dia para atualização dinâmica."""
    try:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'erro': 'Data inválida'}, status=400)

    if data_atual.weekday() == 6:
        data_atual = obter_proximo_dia(data_atual)
        data_iso = data_atual.strftime('%Y-%m-%d')

    # Dados de Navegação
    dia_anterior_str = obter_dia_anterior(data_atual).strftime('%Y-%m-%d')
    proximo_dia_str = obter_proximo_dia(data_atual).strftime('%Y-%m-%d')

    # Dados Financeiros
    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)
    
    gestor = GestorCaixa(fechamento)
    resumo = gestor.calcular_resumo()
    
    # Lista de Movimentações
    movs = fechamento.movimentacoes.all().select_related('categoria').order_by('id')
    lista_movs = []
    
    for mov in movs:
        # Define URLs dinâmicas para o frontend
        url_editar = f"/movimentacao/editar/{mov.id}/"
        url_deletar = f"/movimentacao/deletar/{mov.id}/"
        
        lista_movs.append({
            'id': mov.id,
            'categoria': mov.categoria.nome if mov.categoria else 'Sem Categoria',
            'descricao': mov.descricao or '',
            'valor': float(mov.valor),
            'tipo': mov.tipo,
            'url_editar': url_editar,  
            'url_deletar': url_deletar
        })

    data_texto = date_format(data_atual, format='l, d \d\e F', use_l10n=True).capitalize()

    return JsonResponse({
        'data_formatada': data_texto,
        'data_iso': data_iso,
        'nav': {
            'anterior': dia_anterior_str, 
            'proximo': proximo_dia_str, 
            'atual': data_iso
        },
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

# ==============================================================================
# RELATÓRIOS E GERENCIAMENTO
# ==============================================================================

@login_required
def resumo_financeiro(request):
    """View do Relatório Mensal/Periódico."""
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

    # Busca otimizada usando cache do banco
    fechamentos = FechamentoCaixa.objects.filter(data__range=[data_inicio, data_fim])
    
    somas_cache = fechamentos.aggregate(
        total_cartao=Sum('cache_total_cartao'),
        total_saida=Sum('cache_total_saida'),
        total_suprimento=Sum('cache_total_suprimento')
    )

    total_cartao = somas_cache['total_cartao'] or 0
    total_saida = somas_cache['total_saida'] or 0
    total_suprimento = somas_cache['total_suprimento'] or 0
    
    # Cálculo do dinheiro real (Dia a dia)
    total_dinheiro_calc = 0
    for dia in fechamentos:
        suprimentos = dia.cache_total_suprimento
        retiradas = dia.cache_total_saida
        venda_dia = (retiradas + dia.saldo_final) - (dia.saldo_inicial + suprimentos)
        if venda_dia < 0: 
            venda_dia = 0
        total_dinheiro_calc += venda_dia

    receita_total = total_cartao + total_dinheiro_calc
    lucro_operacional = receita_total - total_saida

    # Tabelas detalhadas por categoria
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

# ==============================================================================
# CATEGORIAS (CRUD)
# ==============================================================================

@login_required
def gerenciar_categorias(request):
    """
    Lista todas as categorias cadastradas.
    URL: /categorias/
    """
    categorias = Categoria.objects.all().order_by('nome')
    return render(request, 'categorias/categorias.html', {'categorias': categorias})

@login_required
def salvar_categoria(request):
    """
    Cria uma NOVA categoria.
    URL: /categorias/nova/
    """
    if request.method == 'POST':
        form = CategoriaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_categorias')
    else:
        form = CategoriaForm()
    
    # Reutiliza o template de form genérico
    return render(request, 'categorias/form.html', {
        'form': form,
        'titulo': 'Nova Categoria'
    })

@login_required
def editar_categoria(request, id):
    """
    Edita uma categoria EXISTENTE.
    URL: /categorias/editar/<id>/
    """
    categoria = get_object_or_404(Categoria, id=id)
    
    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_categorias')
    else:
        form = CategoriaForm(instance=categoria)
    
    # Reutiliza o mesmo template, passando o objeto 'categoria' para habilitar o botão excluir se necessário
    return render(request, 'categorias/form.html', {
        'form': form,
        'titulo': 'Editar Categoria',
        'categoria': categoria
    })

@login_required
def deletar_categoria(request, id):
    """
    Remove uma categoria.
    URL: /categorias/deletar/<id>/
    """
    cat = get_object_or_404(Categoria, id=id)
    try:
        cat.delete()
    except:
        # Em caso de erro (ex: categoria protegida por Foreign Key), apenas ignora ou poderia exibir msg
        pass 
    return redirect('gerenciar_categorias')
