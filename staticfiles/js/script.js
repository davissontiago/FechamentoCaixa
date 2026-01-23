document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Caixa Iniciado.");

    // === Navegação Rápida (AJAX) ===
    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');

    function handleNavegacao(e) {
        // Se segurar Ctrl, deixa abrir em nova aba
        if (e.metaKey || e.ctrlKey) return;
        
        e.preventDefault();
        const novaData = this.dataset.dest;
        carregarDia(novaData);
    }

    if(btnAnt && btnProx) {
        btnAnt.addEventListener('click', handleNavegacao);
        btnProx.addEventListener('click', handleNavegacao);
    }

    async function carregarDia(dataIso) {
        try {
            document.querySelector('.content-area').style.opacity = '0.5';
            
            // Busca dados JSON
            const response = await fetch(`/api/dados/${dataIso}/`);
            if (!response.ok) throw new Error('Erro na API');
            
            const dados = await response.json();

            // 1. Atualiza Cabeçalho
            document.getElementById('display-data').innerText = dados.data_formatada;
            
            btnAnt.dataset.dest = dados.nav.anterior;
            btnProx.dataset.dest = dados.nav.proximo;
            btnAnt.href = `/${dados.nav.anterior}/`;
            btnProx.href = `/${dados.nav.proximo}/`;

            // Atualiza URL do navegador
            window.history.pushState({path: dataIso}, '', `/${dataIso}/`);

            // 2. Atualiza Saldos
            const inputInicial = document.getElementById('saldo-inicial');
            const inputFinal = document.getElementById('saldo-final');
            
            if(inputInicial) inputInicial.value = dados.saldos.inicial.toFixed(2);
            if(inputFinal) inputFinal.value = dados.saldos.final.toFixed(2);

            // 3. Atualiza Resumo
            const fmt = (v) => v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            
            document.getElementById('val-cartao').innerText = fmt(dados.totais.cartao);
            document.getElementById('val-entrada-esp').innerText = fmt(dados.totais.entradas_esp);
            document.getElementById('val-dinheiro-calc').innerText = fmt(dados.totais.dinheiro_miudo);
            document.getElementById('val-geral').innerText = fmt(dados.totais.geral);

            // Atualiza Fórmula
            const txtFormula = `*Dinheiro = (${dados.totais.retiradas} Retirou + ${dados.saldos.final} Sobrou) - (${dados.saldos.inicial} Início + ${dados.totais.entradas_esp} Extra)`;
            const formulaElem = document.getElementById('txt-formula');
            if(formulaElem) formulaElem.innerText = txtFormula;

            // 4. Reconstrói a Lista
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
                        <div class="info-box">
                            <div class="item-name">${mov.nome}</div>
                            <div class="item-sub">${subtexto}</div>
                        </div>
                        <div class="valor">
                            ${sinal} R$ ${mov.valor.toFixed(2)}
                        </div>
                        <a href="${mov.url_editar}" class="btn-action"><i class="fas fa-pen"></i></a>
                        <a href="${mov.url_deletar}" class="btn-action btn-delete"><i class="fas fa-trash"></i></a>
                    </div>
                `;
                listaDiv.insertAdjacentHTML('beforeend', htmlItem);
            });

            ativarListenersDelete();

        } catch (error) {
            console.error("Erro ao carregar dados:", error);
        } finally {
            document.querySelector('.content-area').style.opacity = '1';
        }
    }

    // === Salvar Saldo Automaticamente (Apenas o Final) ===
    const inputSaldoFinal = document.getElementById('saldo-final');
    const formSaldos = document.getElementById('form-saldos');

    if (inputSaldoFinal && formSaldos) {
        inputSaldoFinal.addEventListener('blur', function () {
            // Pequeno delay para garantir UX suave
            setTimeout(() => {
                console.log("Salvando saldo final...");
                formSaldos.submit();
            }, 200);
        });
    }

    // === Confirmação de Exclusão ===
    function ativarListenersDelete() {
        const deleteLinks = document.querySelectorAll('.btn-delete');
        deleteLinks.forEach(link => {
            link.onclick = function(e) {
                if (!confirm('Tem certeza que deseja apagar?')) {
                    e.preventDefault();
                }
            };
        });
    }

    // Inicializa listeners na carga da página
    ativarListenersDelete();
});