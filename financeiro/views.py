from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from datetime import timedelta, datetime
from .models import FechamentoCaixa, Movimentacao
from .forms import MovimentacaoRapidaForm, FechamentoSaldoForm
from django.db.models import Sum

# === FUNÇÕES DE NAVEGAÇÃO (PULA DOMINGO) ===
def obter_dia_anterior(data):
    # Retrocede 1 dia
    anterior = data - timedelta(days=1)
    # Se cair no Domingo (6), retrocede mais um (para Sábado)
    while anterior.weekday() == 6:
        anterior -= timedelta(days=1)
    return anterior

def obter_proximo_dia(data):
    # Avança 1 dia
    proximo = data + timedelta(days=1)
    # Se cair no Domingo (6), avança mais um (para Segunda)
    while proximo.weekday() == 6:
        proximo += timedelta(days=1)
    return proximo

def transportar_saldo_anterior(fechamento_atual):
    """
    Busca o dia útil anterior (ex: Sábado se hoje for Segunda)
    e copia o saldo final dele para o inicial de hoje.
    """
    data_anterior_util = obter_dia_anterior(fechamento_atual.data)
    
    # Tenta pegar o fechamento desse dia anterior
    fechamento_anterior = FechamentoCaixa.objects.filter(data=data_anterior_util).first()
    
    if fechamento_anterior:
        # Se o saldo inicial de hoje estiver diferente do final de "ontem", atualiza
        if fechamento_atual.saldo_inicial != fechamento_anterior.saldo_final_fisico:
            fechamento_atual.saldo_inicial = fechamento_anterior.saldo_final_fisico
            fechamento_atual.save()
            
    return fechamento_atual

@login_required
def diario_caixa(request, data_iso=None):
    if data_iso:
        try:
            data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
        except ValueError:
            return redirect('home')
    else:
        data_atual = timezone.now().date()
    
    # SE FOR DOMINGO, REDIRECIONA PARA SEGUNDA
    if data_atual.weekday() == 6:
        proximo_util = obter_proximo_dia(data_atual)
        return redirect('caixa_dia', data_iso=proximo_util.strftime('%Y-%m-%d'))

    # Calcula navegação pulando domingo
    dia_anterior = obter_dia_anterior(data_atual)
    proximo_dia = obter_proximo_dia(data_atual)

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)

    form_mov = MovimentacaoRapidaForm()
    form_saldo = FechamentoSaldoForm(instance=fechamento)

    if request.method == 'POST':
        # Removemos a lógica de 'toggle_status' pois não existe mais botão
        
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
                transportar_saldo_anterior(obj) # Garante integridade
                obj.save()
                return redirect(request.path)

    # Cálculos (Mantendo a lógica de Suprimento separada que fizemos antes)
    movs = fechamento.movimentacoes.all().order_by('id')
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    suprimentos = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    
    dinheiro_disponivel = fechamento.saldo_inicial + suprimentos
    miudos = (retiradas + fechamento.saldo_final_fisico) - dinheiro_disponivel
    if miudos < 0: miudos = 0
    
    total_geral = vendas_cartao + miudos

    return render(request, 'financeiro/caderno.html', {
        'fechamento': fechamento,
        'movimentacoes': movs,
        'dia_anterior': dia_anterior,
        'proximo_dia': proximo_dia,
        'data_atual': data_atual,
        'data_atual_iso': data_atual.strftime('%Y-%m-%d'),
        'form_mov': form_mov,
        'form_saldo': form_saldo,
        'totais': {
            'cartao': vendas_cartao,
            'entradas_esp': suprimentos,
            'retiradas': retiradas,
            'dinheiro_miudo': miudos,
            'geral': total_geral
        }
    })

@login_required
def api_dados_caixa(request, data_iso):
    try:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'erro': 'Data inválida'}, status=400)

    # Se a API pedir domingo, redireciona a logica para segunda (ou devolve erro, mas vamos ajustar os links)
    if data_atual.weekday() == 6:
        data_atual = obter_proximo_dia(data_atual)
        data_iso = data_atual.strftime('%Y-%m-%d')

    dia_anterior_str = obter_dia_anterior(data_atual).strftime('%Y-%m-%d')
    proximo_dia_str = obter_proximo_dia(data_atual).strftime('%Y-%m-%d')

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)
    
    movs = fechamento.movimentacoes.all()
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    suprimentos = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    
    dinheiro_disponivel = fechamento.saldo_inicial + suprimentos
    miudos = (retiradas + fechamento.saldo_final_fisico) - dinheiro_disponivel
    if miudos < 0: miudos = 0
    
    total_geral = vendas_cartao + miudos

    lista_movs = []
    for mov in movs.order_by('id'):
        lista_movs.append({
            'id': mov.id,
            'nome': mov.nome,
            'valor': float(mov.valor),
            'tipo': mov.tipo,
            'url_editar': f"/editar/{mov.id}/",  
            'url_deletar': f"/deletar/{mov.id}/"
        })

    data_texto = date_format(data_atual, format='l, d \d\e F', use_l10n=True).capitalize()

    return JsonResponse({
        'data_formatada': data_texto,
        'data_iso': data_iso,
        # Removemos 'loja_fechada' daqui pois não é mais usada
        'nav': {'anterior': dia_anterior_str, 'proximo': proximo_dia_str, 'atual': data_iso},
        'saldos': {'inicial': float(fechamento.saldo_inicial), 'final': float(fechamento.saldo_final_fisico)},
        'totais': {
            'cartao': float(vendas_cartao),
            'entradas_esp': float(suprimentos),
            'dinheiro_miudo': float(miudos),
            'retiradas': float(retiradas),
            'geral': float(total_geral),
        },
        'movimentacoes': lista_movs
    })

# As views de deletar e editar permanecem iguais
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
            return redirect('caixa_dia', data_iso=mov.fechamento.data)
    else:
        form = MovimentacaoRapidaForm(instance=mov)
    return render(request, 'financeiro/editar_movimentacao.html', {'form': form})

@login_required
def resumo_financeiro(request):
    hoje = timezone.now().date()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # Filtra fechamentos do mês
    fechamentos_mes = FechamentoCaixa.objects.filter(
        data__month=mes_atual, 
        data__year=ano_atual
    ).order_by('data')

    # Filtra movimentações do mês
    movimentacoes_mes = Movimentacao.objects.filter(
        fechamento__data__month=mes_atual,
        fechamento__data__year=ano_atual
    )

    # 1. KPI: Total Vendas Cartão
    total_cartao = movimentacoes_mes.filter(tipo='CARTAO').aggregate(Sum('valor'))['valor__sum'] or 0

    # 2. KPI: Total Saídas/Despesas
    total_saidas = movimentacoes_mes.filter(tipo='SAIDA').aggregate(Sum('valor'))['valor__sum'] or 0

    # 3. KPI: Média de Saldo Final (Quanto sobra na gaveta em média)
    media_saldo = 0
    count_fechamentos = fechamentos_mes.count()
    if count_fechamentos > 0:
        soma_saldos = fechamentos_mes.aggregate(Sum('saldo_final_fisico'))['saldo_final_fisico__sum'] or 0
        media_saldo = soma_saldos / count_fechamentos

    # 4. DADOS PARA O GRÁFICO DE LINHA (Evolução do Saldo)
    labels_dias = []
    data_saldos = []
    
    for f in fechamentos_mes:
        labels_dias.append(f.data.strftime('%d/%m'))
        data_saldos.append(float(f.saldo_final_fisico))

    return render(request, 'financeiro/resumo.html', {
        'mes_ano': hoje.strftime('%B / %Y').capitalize(),
        'total_cartao': total_cartao,
        'total_saidas': total_saidas,
        'media_saldo': media_saldo,
        # Dados para JS (Charts)
        'chart_labels': labels_dias,
        'chart_data': data_saldos,
    })