document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Caixa V4.0");

    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');
    const seletorData = document.getElementById('seletor-data');
    
    // Toggle Elements
    const checkPularDia = document.getElementById('checkbox-pular-dia');
    const formToggle = document.getElementById('form-toggle');
    const inputToggleStatus = document.getElementById('input-toggle-status');
    const labelPularDia = document.getElementById('label-pular-dia');

    // === Lógica do Botão Toggle ===
    function atualizarVisualToggle(ativado) {
        if (!labelPularDia) return;
        if (ativado) {
            labelPularDia.style.color = '#ef4444'; // Vermelho
            labelPularDia.style.fontWeight = 'bold';
            labelPularDia.innerText = "Dia Pulado (Fechado)";
        } else {
            labelPularDia.style.color = '#6b7280'; // Cinza
            labelPularDia.style.fontWeight = 'normal';
            labelPularDia.innerText = "Pular Dia (Loja Fechada)";
        }
    }

    if (checkPularDia) {
        // Estado inicial
        atualizarVisualToggle(checkPularDia.checked);

        // Ao clicar
        checkPularDia.addEventListener('change', function() {
            atualizarVisualToggle(this.checked);
            inputToggleStatus.value = this.checked ? 'true' : 'false';
            // Submit com pequeno delay para feedback visual
            setTimeout(() => { formToggle.submit(); }, 200);
        });
    }

    // === Navegação ===
    function handleNavegacao(e) {
        if (e.metaKey || e.ctrlKey) return;
        e.preventDefault();
        carregarDia(this.dataset.dest);
    }

    if(btnAnt && btnProx) {
        btnAnt.addEventListener('click', handleNavegacao);
        btnProx.addEventListener('click', handleNavegacao);
    }

    if (seletorData) {
        seletorData.addEventListener('change', function(e) {
            carregarDia(this.value);
        });
    }

    async function carregarDia(dataIso) {
        try {
            document.querySelector('.content-area').style.opacity = '0.5';
            
            const response = await fetch(`/api/dados/${dataIso}/`);
            if (!response.ok) throw new Error('Erro API');
            const dados = await response.json();

            // 1. Atualiza Toggle
            if (checkPularDia) {
                checkPularDia.checked = dados.loja_fechada;
                atualizarVisualToggle(dados.loja_fechada);
            }

            // 2. Cabeçalho
            document.getElementById('display-data').innerHTML = `${dados.data_formatada} <i class="fas fa-caret-down" style="font-size: 0.8em; opacity: 0.5;"></i>`;
            if(seletorData) seletorData.value = dados.data_iso;

            btnAnt.dataset.dest = dados.nav.anterior;
            btnProx.dataset.dest = dados.nav.proximo;
            btnAnt.href = `/${dados.nav.anterior}/`;
            btnProx.href = `/${dados.nav.proximo}/`;
            window.history.pushState({path: dataIso}, '', `/${dataIso}/`);

            // 3. Saldos
            const inputInicial = document.getElementById('saldo-inicial');
            const inputFinal = document.getElementById('saldo-final');
            if(inputInicial) inputInicial.value = dados.saldos.inicial.toFixed(2);
            if(inputFinal) inputFinal.value = dados.saldos.final.toFixed(2);

            // 4. Totais e Lista
            const fmt = (v) => v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('val-cartao').innerText = fmt(dados.totais.cartao);
            document.getElementById('val-entrada-esp').innerText = fmt(dados.totais.entradas_esp);
            document.getElementById('val-dinheiro-calc').innerText = fmt(dados.totais.dinheiro_miudo);
            document.getElementById('val-geral').innerText = fmt(dados.totais.geral);

            const txtFormula = `*Dinheiro = (${dados.totais.retiradas} Retirou + ${dados.saldos.final} Sobrou) - (${dados.saldos.inicial} Início + ${dados.totais.entradas_esp} Extra)`;
            const formulaElem = document.getElementById('txt-formula');
            if(formulaElem) formulaElem.innerText = txtFormula;

            const listaDiv = document.getElementById('lista-movimentacoes');
            listaDiv.innerHTML = ''; 
            
            if (dados.movimentacoes.length === 0) {
                listaDiv.innerHTML = '<div style="text-align:center; padding: 20px; color: #aaa;">Nenhum lançamento hoje</div>';
            }

            dados.movimentacoes.forEach(mov => {
                let classeCss = 'tipo-saida';
                let icone = '<i class="fas fa-arrow-down"></i>';
                let subtexto = 'Saída/Sangria';
                let sinal = '-';

                if (mov.tipo === 'CARTAO') {
                    classeCss = 'tipo-cartao';
                    icone = '<i class="fas fa-credit-card"></i>';
                    subtexto = 'Cartão/Pix';
                    sinal = '+';
                } else if (mov.tipo === 'DINHEIRO') {
                    classeCss = 'tipo-dinheiro';
                    icone = '<i class="fas fa-money-bill-wave"></i>';
                    subtexto = 'Entrada Dinheiro';
                    sinal = '+';
                }

                const htmlItem = `
                    <div class="line-item ${classeCss}">
                        <div class="icon-box">${icone}</div>
                        <div class="info-box"><div class="item-name">${mov.nome}</div><div class="item-sub">${subtexto}</div></div>
                        <div class="valor">${sinal} R$ ${mov.valor.toFixed(2)}</div>
                        <a href="${mov.url_editar}" class="btn-action"><i class="fas fa-pen"></i></a>
                        <a href="${mov.url_deletar}" class="btn-action btn-delete"><i class="fas fa-trash"></i></a>
                    </div>`;
                listaDiv.insertAdjacentHTML('beforeend', htmlItem);
            });
            ativarListenersDelete();

        } catch (error) {
            console.error(error);
        } finally {
            document.querySelector('.content-area').style.opacity = '1';
        }
    }

    // Auto-save saldo
    const inputSaldoFinal = document.getElementById('saldo-final');
    const formSaldos = document.getElementById('form-saldos');
    if (inputSaldoFinal && formSaldos) {
        inputSaldoFinal.addEventListener('blur', function () {
            setTimeout(() => formSaldos.submit(), 200);
        });
        inputSaldoFinal.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.keyCode === 13) { e.preventDefault(); this.blur(); }
        });
    }

    // Botão Adicionar Spinner
    const formAdicionar = document.querySelector('.add-area form:last-of-type');
    if (formAdicionar) {
        formAdicionar.addEventListener('submit', function(e) {
            const btn = this.querySelector('button');
            if (btn.disabled) { e.preventDefault(); return; }
            btn.disabled = true; btn.style.opacity = '0.7'; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        });
    }

    function ativarListenersDelete() {
        const deleteLinks = document.querySelectorAll('.btn-delete');
        deleteLinks.forEach(link => link.onclick = (e) => confirm('Tem certeza?') ? true : e.preventDefault());
    }
    ativarListenersDelete();
});