from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.formats import date_format
from datetime import timedelta, datetime
from .models import FechamentoCaixa, Movimentacao
from .forms import MovimentacaoRapidaForm, FechamentoSaldoForm

# === LÓGICA DE PROTEÇÃO DE SALDO E PULAR DIA ===
def transportar_saldo_anterior(fechamento_atual):
    """
    Regra 1: Saldo Inicial de Hoje = Saldo Final de Ontem.
    Regra 2: Se Ontem foi pulado (Domingo/Feriado), o dinheiro passa direto (Final=Inicial).
    """
    # 1. Pega ou cria o dia de ontem
    data_ontem = fechamento_atual.data - timedelta(days=1)
    fechamento_ontem, _ = FechamentoCaixa.objects.get_or_create(data=data_ontem)
    
    # 2. Se ontem foi Domingo, marca como fechado automaticamente
    if data_ontem.weekday() == 6: 
        fechamento_ontem.loja_fechada = True
    
    # 3. REGRA DA PONTE: Se ontem estava fechado, o saldo sai igual entrou
    if fechamento_ontem.loja_fechada:
        if fechamento_ontem.saldo_final_fisico != fechamento_ontem.saldo_inicial:
            fechamento_ontem.saldo_final_fisico = fechamento_ontem.saldo_inicial
            fechamento_ontem.save()
            # Recursividade: garante a corrente verificando o dia antes de ontem
            transportar_saldo_anterior(fechamento_ontem)

    # 4. REGRA UNIVERSAL: Traz o saldo de ontem para hoje
    if fechamento_atual.saldo_inicial != fechamento_ontem.saldo_final_fisico:
        fechamento_atual.saldo_inicial = fechamento_ontem.saldo_final_fisico
        fechamento_atual.save()

    # 5. Verifica se hoje é Domingo
    if fechamento_atual.data.weekday() == 6:
        fechamento_atual.loja_fechada = True
    
    # 6. Se hoje está fechado, já deixa o saldo final igual ao inicial
    if fechamento_atual.loja_fechada:
        if fechamento_atual.saldo_final_fisico != fechamento_atual.saldo_inicial:
            fechamento_atual.saldo_final_fisico = fechamento_atual.saldo_inicial
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
    
    dia_anterior = data_atual - timedelta(days=1)
    proximo_dia = data_atual + timedelta(days=1)

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    
    # Aplica as regras ao carregar a página
    transportar_saldo_anterior(fechamento)

    form_mov = MovimentacaoRapidaForm()
    form_saldo = FechamentoSaldoForm(instance=fechamento)

    if request.method == 'POST':
        # --- Botão Pular Dia ---
        if 'toggle_status' in request.POST:
            status = request.POST.get('toggle_status')
            fechamento.loja_fechada = (status == 'true')
            transportar_saldo_anterior(fechamento) # Recalcula com o novo status
            fechamento.save()
            return redirect(request.path)

        # --- Adicionar Movimentação ---
        elif 'btn_movimentacao' in request.POST:
            form_mov = MovimentacaoRapidaForm(request.POST)
            if form_mov.is_valid():
                nova_mov = form_mov.save(commit=False)
                nova_mov.fechamento = fechamento
                nova_mov.save()
                # Se lançou algo, abre a loja automaticamente
                if fechamento.loja_fechada:
                    fechamento.loja_fechada = False
                    fechamento.save()
                return redirect(request.path)
        
        # --- Salvar Saldos ---
        elif 'btn_saldos' in request.POST:
            form_saldo = FechamentoSaldoForm(request.POST, instance=fechamento)
            if form_saldo.is_valid():
                obj = form_saldo.save(commit=False)
                # Garante que o usuário não burlou o saldo inicial (Regra 1)
                transportar_saldo_anterior(obj) 
                obj.save()
                return redirect(request.path)

    movs = fechamento.movimentacoes.all().order_by('id')
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    entradas_esp = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    
    miudos = (retiradas + fechamento.saldo_final_fisico) - (fechamento.saldo_inicial + entradas_esp)
    if miudos < 0: miudos = 0
    total_geral = vendas_cartao + miudos + entradas_esp

    return render(request, 'financeiro/caderno.html', {
        'fechamento': fechamento,
        'movimentacoes': movs,
        'dia_anterior': dia_anterior,
        'proximo_dia': proximo_dia,
        'data_atual': data_atual,
        'data_atual_iso': data_atual.strftime('%Y-%m-%d'),
        'form_mov': form_mov,
        'form_saldo': form_saldo,
        'totais': {'cartao': vendas_cartao, 'entradas_esp': entradas_esp, 'retiradas': retiradas, 'dinheiro_miudo': miudos, 'geral': total_geral}
    })

@login_required
def api_dados_caixa(request, data_iso):
    try:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'erro': 'Data inválida'}, status=400)

    dia_anterior_str = (data_atual - timedelta(days=1)).strftime('%Y-%m-%d')
    proximo_dia_str = (data_atual + timedelta(days=1)).strftime('%Y-%m-%d')

    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    # Garante as regras também na navegação AJAX
    transportar_saldo_anterior(fechamento)
    
    movs = fechamento.movimentacoes.all()
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    entradas_esp = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    miudos = (retiradas + fechamento.saldo_final_fisico) - (fechamento.saldo_inicial + entradas_esp)
    if miudos < 0: miudos = 0
    total_geral = vendas_cartao + miudos + entradas_esp

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
        
    data_texto = date_format(data_atual, format='l, d \d\e F', use_l10n=True)
    
    data_texto = data_texto.capitalize()
    
    return JsonResponse({
        'data_formatada': data_texto,
        'data_formatada': data_atual.strftime('%d de %B'),
        'data_iso': data_iso,
        'loja_fechada': fechamento.loja_fechada, # Envia estado para o botão
        'nav': {'anterior': dia_anterior_str, 'proximo': proximo_dia_str, 'atual': data_iso},
        'saldos': {'inicial': float(fechamento.saldo_inicial), 'final': float(fechamento.saldo_final_fisico)},
        'totais': {'cartao': float(vendas_cartao), 'entradas_esp': float(entradas_esp), 'dinheiro_miudo': float(miudos), 'retiradas': float(retiradas), 'geral': float(total_geral)},
        'movimentacoes': lista_movs
    })

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