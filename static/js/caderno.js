/* ============================================================
   CADERNO.JS - Lógica Específica do Fluxo Diário (AJAX)
   ============================================================ */

document.addEventListener("DOMContentLoaded", function() {
    
    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');
    const seletorData = document.getElementById('seletor-data');

    // Navegação entre dias
    function handleNavegacao(e) {
        if (e.metaKey || e.ctrlKey) return;
        e.preventDefault();
        // O dataset.dest foi adicionado no HTML do caderno
        if(this.dataset.dest) {
            carregarDia(this.dataset.dest); 
        }
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
});

// A função carregarDia precisa ser global ou estar acessível
async function carregarDia(dataIso) {
    try {
        // Efeito visual de carregamento
        const contentArea = document.querySelector('.content-area');
        if(contentArea) contentArea.style.opacity = '0.5';
        
        // Busca dados na API
        const response = await fetch(`/api/dados/${dataIso}/`);
        if (!response.ok) throw new Error('Erro API');
        const dados = await response.json();

        // 1. Atualiza Data e URL
        document.getElementById('display-data').innerHTML = `${dados.data_formatada} <i class="fas fa-caret-down"></i>`;
        const seletor = document.getElementById('seletor-data');
        if(seletor) seletor.value = dados.data_iso;
        
        window.history.pushState({path: dataIso}, '', `/caixa/${dataIso}/`);

        // 2. Atualiza Botões de Navegação
        const btnAnt = document.getElementById('btn-anterior');
        const btnProx = document.getElementById('btn-proximo');
        
        if(btnAnt) {
            btnAnt.dataset.dest = dados.nav.anterior;
            btnAnt.href = `/caixa/${dados.nav.anterior}/`;
        }
        if(btnProx) {
            btnProx.dataset.dest = dados.nav.proximo;
            btnProx.href = `/caixa/${dados.nav.proximo}/`;
        }

        // 3. Atualiza o Botão Flutuante (Centralizado)
        const fabBtn = document.querySelector('.fab-btn');
        if (fabBtn) {
            fabBtn.href = `/movimentacao/salvar/${dados.data_iso}/`;
        }

        // 4. Atualiza Saldos (Inputs com IDs Corretos)
        const inputInicial = document.getElementById('id_saldo_inicial');
        const inputFinal = document.getElementById('id_saldo_final');
        
        // Usa a função global definida em utils.js
        if(inputInicial) {
            inputInicial.value = (dados.saldos.inicial * 100).toFixed(0);
            aplicarMascaraMoeda(inputInicial);
        }
        if(inputFinal) {
            inputFinal.value = (dados.saldos.final * 100).toFixed(0);
            aplicarMascaraMoeda(inputFinal);
        }

        // 5. Atualiza Card de Resumo (IDs Corretos)
        // Usa a função global formatarMoedaParaExibicao de utils.js
        const setTxt = (id, val) => { 
            const el = document.getElementById(id); 
            if(el) el.innerText = formatarMoedaParaExibicao(val); 
        };

        setTxt('val-cartao', dados.totais.cartao);
        setTxt('val-entrada-esp', dados.totais.entradas_esp);
        setTxt('val-dinheiro-calc', dados.totais.dinheiro_miudo);
        setTxt('val-geral', dados.totais.geral);

        // Fórmula Rodapé
        const txtFormula = `*Dinheiro = (${dados.totais.retiradas} Saídas + ${dados.saldos.final} Sobrou) - (${dados.saldos.inicial} Início + ${dados.totais.entradas_esp} Suprimentos)`;
        const elFormula = document.getElementById('txt-formula');
        if(elFormula) elFormula.innerText = txtFormula;

        // 6. Reconstrói a Lista de Movimentações (LAYOUT ACORDEÃO)
        const listaDiv = document.getElementById('lista-movimentacoes');
        if(listaDiv) {
            listaDiv.innerHTML = ''; 
            
            if (dados.movimentacoes.length === 0) {
                listaDiv.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-basket-shopping"></i>
                        <p>Nenhuma movimentação hoje.</p>
                    </div>`;
            }

            dados.movimentacoes.forEach(mov => {
                let classeCss = 'tipo-saida';
                let icone = '<i class="fas fa-arrow-down"></i>';
                let subtexto = 'Saída/Sangria';
                let sinal = '-';

                if (mov.tipo === 'CARTAO') { 
                    classeCss = 'tipo-cartao'; icone = '<i class="fas fa-credit-card"></i>'; subtexto = 'Cartão/Pix'; sinal = '+'; 
                } else if (mov.tipo === 'DINHEIRO') { 
                    classeCss = 'tipo-dinheiro'; icone = '<i class="fas fa-coins"></i>'; subtexto = 'Suprimento'; sinal = '+'; 
                } else if (mov.tipo === 'REGISTRO') { 
                    classeCss = 'tipo-registro'; icone = '<i class="fas fa-file-alt"></i>'; subtexto = 'Registro'; sinal = '-'; 
                }

                let descTexto = mov.descricao ? 
                    `<i class="fas fa-quote-left"></i> ${mov.descricao}` : 
                    'Sem descrição';

                // GERA HTML COMPATÍVEL COM O CSS NOVO
                const htmlItem = `
                    <div class="mov-card" onclick="this.classList.toggle('active')">
                        <div class="line-item ${classeCss}">
                            <div class="icon-box">${icone}</div>
                            <div class="info-box">
                                <div class="item-name">${mov.categoria}</div>
                                <div class="item-sub">${subtexto}</div>
                            </div>
                            <div class="valor">${sinal} R$ ${mov.valor.toFixed(2)}</div>
                        </div>

                        <div class="mov-details" onclick="event.stopPropagation()">
                            <div class="mov-desc">${descTexto}</div>
                            <div class="mov-actions">
                                <a href="${mov.url_editar}" class="btn-text-action btn-text-edit">
                                    <i class="fas fa-pen"></i> Editar
                                </a>
                                <a href="${mov.url_deletar}" class="btn-text-action btn-text-delete" onclick="return confirm('Tem certeza?')">
                                    <i class="fas fa-trash"></i> Excluir
                                </a>
                            </div>
                        </div>
                    </div>`;
                
                listaDiv.insertAdjacentHTML('beforeend', htmlItem);
            });
        }

    } catch (error) {
        console.error("Erro ao carregar dia:", error);
    } finally {
        const contentArea = document.querySelector('.content-area');
        if(contentArea) contentArea.style.opacity = '1';
    }
}