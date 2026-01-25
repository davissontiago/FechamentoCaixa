document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Caixa V8.0 - Limpo");

    // === MÁSCARA DE DINHEIRO GENÉRICA ===
    function aplicarMascaraMoeda(input) {
        let value = input.value.replace(/\D/g, ""); 
        if (value === "") return;
        value = (parseInt(value) / 100).toFixed(2) + "";
        value = value.replace(".", ",");
        value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");
        input.value = value;
    }

    const moneyInputs = document.querySelectorAll('.money-mask');
    moneyInputs.forEach(input => {
        // 1. Formata valor inicial se houver
        if (input.value) {
            let valCru = input.value.replace('.', '').replace(',', '');
            input.value = valCru;
            aplicarMascaraMoeda(input);
        }
        
        // 2. Formata ao digitar
        if (!input.readOnly) {
            input.addEventListener('input', function() { aplicarMascaraMoeda(this); });
            input.addEventListener('focus', function() { this.select(); });
        }

        // 3. Salva Saldo Final ao sair (Blur) ou Enter
        if (input.id === 'saldo-final') {
             input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.keyCode === 13) { e.preventDefault(); this.blur(); }
            });
             input.addEventListener('blur', function () {
                setTimeout(() => {
                    const form = this.closest('form');
                    if (form) dispararSubmitLimpo(form);
                }, 100);
            });
        }
    });

    // === FUNÇÃO DE ENVIO SEGURO (LIMPA MÁSCARA ANTES DE ENVIAR) ===
    function dispararSubmitLimpo(form) {
        const inputs = form.querySelectorAll('.money-mask');
        inputs.forEach(input => {
            if(input.value) {
                // Converte 1.200,50 -> 1200.50
                let valorLimpo = input.value.replace(/\./g, "").replace(",", ".");
                
                let hiddenName = input.name;
                if (!hiddenName) return;

                // Usa ou cria input hidden para o valor limpo
                let existingHidden = form.querySelector(`input[type="hidden"][name="${hiddenName}"]`);
                if (existingHidden) {
                    existingHidden.value = valorLimpo;
                } else {
                    const hidden = document.createElement('input');
                    hidden.type = 'hidden';
                    hidden.name = hiddenName;
                    hidden.value = valorLimpo;
                    form.appendChild(hidden);
                }
                
                // Remove name do campo visível para não enviar lixo
                input.removeAttribute('name');
            }
        });
        console.log("Enviando dados limpos...");
        form.submit();
    }

    // Intercepta todos os submits para limpar valores
    document.querySelectorAll('form').forEach(form => {
        if (form.querySelector('.money-mask')) {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); 
                
                // Trava botão para evitar duplo clique
                const btn = this.querySelector('button');
                if (btn) {
                    if (btn.disabled) return;
                    btn.disabled = true;
                    btn.style.opacity = '0.7';
                    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                }
                
                dispararSubmitLimpo(this);
            });
        }
    });

    // === NAVEGAÇÃO E MENU (AJUSTADO) ===
    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');
    const seletorData = document.getElementById('seletor-data');

    // Menu Hamburguer
    const openBtn = document.getElementById('open-menu');
    const closeBtn = document.getElementById('close-menu');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    if (openBtn && closeBtn && sidebar && overlay) {
        function toggleMenu() {
            sidebar.classList.toggle('active');
            overlay.classList.toggle('active');
        }
        openBtn.addEventListener('click', toggleMenu);
        closeBtn.addEventListener('click', toggleMenu);
        overlay.addEventListener('click', toggleMenu);
    }

    // Navegação Dias
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

    // AJAX para Carregar Dia Sem Refresh
    async function carregarDia(dataIso) {
        try {
            document.querySelector('.content-area').style.opacity = '0.5';
            
            const response = await fetch(`/api/dados/${dataIso}/`);
            if (!response.ok) throw new Error('Erro API');
            const dados = await response.json();

            // Atualiza Header e URL
            document.getElementById('display-data').innerHTML = `${dados.data_formatada} <i class="fas fa-caret-down" style="font-size: 0.8em; opacity: 0.5;"></i>`;
            if(seletorData) seletorData.value = dados.data_iso;

            btnAnt.dataset.dest = dados.nav.anterior;
            btnProx.dataset.dest = dados.nav.proximo;
            btnAnt.href = `/${dados.nav.anterior}/`;
            btnProx.href = `/${dados.nav.proximo}/`;
            window.history.pushState({path: dataIso}, '', `/${dataIso}/`);

            // Atualiza Saldos (com Máscara)
            const inputInicial = document.getElementById('saldo-inicial');
            const inputFinal = document.getElementById('saldo-final');
            
            if(inputInicial) {
                let valRaw = (dados.saldos.inicial * 100).toFixed(0);
                inputInicial.value = valRaw;
                aplicarMascaraMoeda(inputInicial);
            }
            if(inputFinal) {
                let valRaw = (dados.saldos.final * 100).toFixed(0);
                inputFinal.value = valRaw;
                aplicarMascaraMoeda(inputFinal);
            }

            // Atualiza Resumo
            const fmt = (v) => v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('val-cartao').innerText = fmt(dados.totais.cartao);
            document.getElementById('val-entrada-esp').innerText = fmt(dados.totais.entradas_esp);
            document.getElementById('val-dinheiro-calc').innerText = fmt(dados.totais.dinheiro_miudo);
            document.getElementById('val-geral').innerText = fmt(dados.totais.geral);

            const txtFormula = `*Dinheiro = (${dados.totais.retiradas} Saídas + ${dados.saldos.final} Sobrou) - (${dados.saldos.inicial} Início + ${dados.totais.entradas_esp} Suprimentos)`;
            const formulaElem = document.getElementById('txt-formula');
            if(formulaElem) formulaElem.innerText = txtFormula;

            // Reconstrói Lista
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

                // Verificações de Tipo
                if (mov.tipo === 'CARTAO') { 
                    classeCss = 'tipo-cartao'; 
                    icone = '<i class="fas fa-credit-card"></i>'; 
                    subtexto = 'Cartão/Pix'; 
                    sinal = '+'; 
                } 
                else if (mov.tipo === 'DINHEIRO') { 
                    classeCss = 'tipo-dinheiro'; 
                    icone = '<i class="fas fa-coins"></i>'; 
                    subtexto = 'Suprimento/Entrada'; 
                    sinal = '+'; 
                }
                else if (mov.tipo === 'REGISTRO') { 
                    classeCss = 'tipo-registro'; 
                    icone = '<i class="fas fa-info"></i>'; 
                    subtexto = 'Apenas Registro'; 
                    sinal = '-';
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
    
    function ativarListenersDelete() {
        const deleteLinks = document.querySelectorAll('.btn-delete');
        deleteLinks.forEach(link => link.onclick = (e) => confirm('Tem certeza?') ? true : e.preventDefault());
    }
    ativarListenersDelete();
});