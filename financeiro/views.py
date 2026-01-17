# financeiro/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime
from .models import FechamentoCaixa, Movimentacao
from .forms import MovimentacaoRapidaForm, FechamentoSaldoForm

@login_required
def diario_caixa(request, data_iso=None):
    # 1. Navegação de Datas
    if data_iso:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    else:
        data_atual = timezone.now().date()
    
    dia_anterior = data_atual - timedelta(days=1)
    proximo_dia = data_atual + timedelta(days=1)

    # 2. Busca ou Cria (Com Lógica de Transporte de Saldo)
    # Tenta pegar o fechamento de hoje
    fechamento, created = FechamentoCaixa.objects.get_or_create(data=data_atual)
    
    ultimo_fechamento = FechamentoCaixa.objects.filter(data__lt=data_atual).order_by('-data').first()
    
    if ultimo_fechamento:
        # Se o saldo inicial de hoje estiver diferente do final de ontem, FORÇA a atualização
        if fechamento.saldo_inicial != ultimo_fechamento.saldo_final_fisico:
            fechamento.saldo_inicial = ultimo_fechamento.saldo_final_fisico
            fechamento.save()

    # 3. Processamento dos Formulários (POST)
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
                form_saldo.save()
                return redirect(request.path)

    # 4. Cálculos (Nova Lógica Matemática)
    
    # A. Vendas Cartão (Não afeta caixa físico)
    vendas_cartao = sum(m.valor for m in fechamento.movimentacoes.all() if m.tipo == 'CARTAO')
    
    # B. Entradas Dinheiro Específicas (Aumentam o caixa)
    entradas_dinheiro_especificas = sum(m.valor for m in fechamento.movimentacoes.all() if m.tipo == 'DINHEIRO')
    
    # C. Saídas (Diminuem o caixa)
    total_retirado = sum(m.valor for m in fechamento.movimentacoes.all() if m.tipo == 'SAIDA')
    
    # D. Venda Dinheiro "Miúdos" (Calculado por diferença)
    # Lógica: O que entrou de "miúdo" = (O que saiu + O que sobrou) - (O que tinha no início + O que entrou específico)
    vendas_dinheiro_miudos = (total_retirado + fechamento.saldo_final_fisico) - (fechamento.saldo_inicial + entradas_dinheiro_especificas)
    
    if vendas_dinheiro_miudos < 0: vendas_dinheiro_miudos = 0

    # Total de Receita Real = Cartão + Miúdos + Entradas Específicas
    total_geral = vendas_cartao + vendas_dinheiro_miudos + entradas_dinheiro_especificas

    return render(request, 'financeiro/caderno.html', {
        'fechamento': fechamento,
        'movimentacoes': fechamento.movimentacoes.all().order_by('id'),
        'dia_anterior': dia_anterior,
        'proximo_dia': proximo_dia,
        'data_atual': data_atual,
        'form_mov': form_mov,
        'form_saldo': form_saldo,
        'totais': {
            'cartao': vendas_cartao,
            'entradas_esp': entradas_dinheiro_especificas,
            'retiradas': total_retirado,
            'dinheiro_miudo': vendas_dinheiro_miudos,
            'geral': total_geral
        }
    })

# ... (Manter funções de deletar e editar, apenas cuidado que os choices mudaram) ...
# Vou reescrever as funções auxiliares para garantir que não quebrem
@login_required
def deletar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    data_iso = mov.fechamento.data.strftime('%Y-%m-%d')
    mov.delete()
    return redirect('caixa_dia', data_iso=data_iso)

@login_required
def editar_movimentacao(request, id):
    mov = get_object_or_404(Movimentacao, id=id)
    data_iso = mov.fechamento.data.strftime('%Y-%m-%d')
    if request.method == 'POST':
        form = MovimentacaoRapidaForm(request.POST, instance=mov)
        if form.is_valid():
            form.save()
            return redirect('caixa_dia', data_iso=data_iso)
    else:
        form = MovimentacaoRapidaForm(instance=mov)
    return render(request, 'financeiro/editar_movimentacao.html', {'form': form, 'mov': mov})