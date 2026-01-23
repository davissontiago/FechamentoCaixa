from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta, datetime
from .models import FechamentoCaixa, Movimentacao
from .forms import MovimentacaoRapidaForm, FechamentoSaldoForm

# Função auxiliar para garantir a integridade do saldo
def transportar_saldo_anterior(fechamento_atual):
    # Busca o último fechamento antes da data atual
    ultimo = FechamentoCaixa.objects.filter(data__lt=fechamento_atual.data).order_by('-data').first()
    
    if ultimo:
        # Se houver dia anterior, o inicial de hoje DEVE ser igual ao final de ontem
        if fechamento_atual.saldo_inicial != ultimo.saldo_final_fisico:
            fechamento_atual.saldo_inicial = ultimo.saldo_final_fisico
            fechamento_atual.save()
    return fechamento_atual

@login_required
def diario_caixa(request, data_iso=None):
    # 1. Definição de Datas
    if data_iso:
        try:
            data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
        except ValueError:
            return redirect('home')
    else:
        data_atual = timezone.now().date()
    
    dia_anterior = data_atual - timedelta(days=1)
    proximo_dia = data_atual + timedelta(days=1)

    # 2. Busca ou Cria o Caixa do Dia
    fechamento, created = FechamentoCaixa.objects.get_or_create(data=data_atual)
    
    # GARANTIA: Atualiza o saldo inicial baseado no dia anterior
    transportar_saldo_anterior(fechamento)

    # 3. Processamento de Formulários (POST Tradicional)
    form_mov = MovimentacaoRapidaForm()
    form_saldo = FechamentoSaldoForm(instance=fechamento)

    if request.method == 'POST':
        if 'btn_movimentacao' in request.POST:
            form_mov = MovimentacaoRapidaForm(request.POST)
            if form_mov.is_valid():
                nova_mov = form_mov.save(commit=False)
                nova_mov.fechamento = fechamento
                nova_mov.save()
                return redirect(request.path) # Recarrega para mostrar novo item
        
        elif 'btn_saldos' in request.POST:
            form_saldo = FechamentoSaldoForm(request.POST, instance=fechamento)
            if form_saldo.is_valid():
                # Apenas salvamos o saldo final, o inicial é protegido
                obj = form_saldo.save(commit=False)
                # Forçamos o inicial a manter-se correto (caso tentem burlar o HTML)
                transportar_saldo_anterior(obj) 
                obj.save()
                return redirect(request.path)

    # 4. Cálculos para Exibição
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
        'form_mov': form_mov,
        'form_saldo': form_saldo,
        'totais': {
            'cartao': vendas_cartao,
            'entradas_esp': entradas_esp,
            'retiradas': retiradas,
            'dinheiro_miudo': miudos,
            'geral': total_geral
        }
    })

@login_required
def api_dados_caixa(request, data_iso):
    # 1. Datas
    try:
        data_atual = datetime.strptime(data_iso, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'erro': 'Data inválida'}, status=400)

    dia_anterior_str = (data_atual - timedelta(days=1)).strftime('%Y-%m-%d')
    proximo_dia_str = (data_atual + timedelta(days=1)).strftime('%Y-%m-%d')

    # 2. Busca e Correção Automática
    fechamento, _ = FechamentoCaixa.objects.get_or_create(data=data_atual)
    transportar_saldo_anterior(fechamento)
    
    # 3. Cálculos
    movs = fechamento.movimentacoes.all()
    vendas_cartao = sum(m.valor for m in movs if m.tipo == 'CARTAO')
    entradas_esp = sum(m.valor for m in movs if m.tipo == 'DINHEIRO')
    retiradas = sum(m.valor for m in movs if m.tipo == 'SAIDA')
    
    miudos = (retiradas + fechamento.saldo_final_fisico) - (fechamento.saldo_inicial + entradas_esp)
    if miudos < 0: miudos = 0
    
    total_geral = vendas_cartao + miudos + entradas_esp

    # 4. JSON
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

    return JsonResponse({
        'data_formatada': data_atual.strftime('%d de %B'),
        'nav': {'anterior': dia_anterior_str, 'proximo': proximo_dia_str, 'atual': data_iso},
        'saldos': {
            'inicial': float(fechamento.saldo_inicial),
            'final': float(fechamento.saldo_final_fisico)
        },
        'totais': {
            'cartao': float(vendas_cartao),
            'entradas_esp': float(entradas_esp),
            'dinheiro_miudo': float(miudos),
            'retiradas': float(retiradas),
            'geral': float(total_geral),
        },
        'movimentacoes': lista_movs
    })

# Funções Auxiliares (Editar e Deletar)
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