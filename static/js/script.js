document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Caixa V5.5 - Máscara Global");

    // === MÁSCARA DE DINHEIRO GENÉRICA ===
    function aplicarMascaraMoeda(input) {
        let value = input.value.replace(/\D/g, ""); // Remove não-números
        
        if (value === "") {
            input.value = "";
            return;
        }
        
        // Converte para decimal (1000 -> 10.00)
        value = (parseInt(value) / 100).toFixed(2) + "";
        
        // Formata para PT-BR (troca ponto por vírgula, adiciona milhar)
        value = value.replace(".", ",");
        value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");
        
        input.value = value;
    }

    // Inicializa todos os campos de dinheiro
    const moneyInputs = document.querySelectorAll('.money-mask');
    
    moneyInputs.forEach(input => {
        // 1. Formata valor inicial (se vier do banco tipo 150.50 vira 150,50)
        if (input.value) {
            // Remove formatação antiga se houver e garante formato limpo
            let val = input.value.replace('.', '').replace(',', '');
            input.value = val;
            aplicarMascaraMoeda(input);
        }

        // 2. Evento de digitação
        input.addEventListener('input', function() {
            aplicarMascaraMoeda(this);
        });

        // 3. Selecionar tudo ao clicar (facilita edição)
        input.addEventListener('focus', function() {
            this.select();
        });
        
        // 4. Se for o Saldo Final, mantém o comportamento de salvar com Enter
        if (input.id === 'saldo-final') {
             input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' || e.keyCode === 13) {
                    e.preventDefault(); 
                    this.blur(); 
                }
            });
             input.addEventListener('blur', function () {
                // Pequeno delay e força o submit do formulário pai
                setTimeout(() => {
                    const form = this.closest('form');
                    if (form) dispararSubmitLimpo(form);
                }, 100);
            });
        }
    });

    // === FUNÇÃO PARA LIMPAR E ENVIAR FORMULÁRIOS ===
    // Intercepta o envio para limpar a máscara (1.000,00 -> 1000.00)
    function dispararSubmitLimpo(form) {
        const inputs = form.querySelectorAll('.money-mask');
        
        // Cria inputs hidden com os valores limpos para enviar
        inputs.forEach(input => {
            if(input.value) {
                // Remove pontos de milhar e troca vírgula decimal por ponto
                let valorLimpo = input.value.replace(/\./g, "").replace(",", ".");
                
                // Verifica se já existe um hidden input para este campo
                let hiddenName = input.name;
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
                
                // Remove o name do campo visível para não enviar duplicado
                input.removeAttribute('name');
            }
        });

        console.log("Enviando formulário com valores limpos...");
        form.submit();
    }

    // Intercepta todos os submits de botão (Adicionar / Editar)
    document.querySelectorAll('form').forEach(form => {
        // Ignora o form de toggle, foca nos que tem input de dinheiro
        if (form.querySelector('.money-mask')) {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); // Para o envio padrão
                
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

    // === NAVEGAÇÃO E SISTEMA (Código Antigo Mantido) ===
    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');
    const seletorData = document.getElementById('seletor-data');
    const checkPularDia = document.getElementById('checkbox-pular-dia');
    const formToggle = document.getElementById('form-toggle');
    const inputToggleStatus = document.getElementById('input-toggle-status');
    const labelPularDia = document.getElementById('label-pular-dia');

    function atualizarVisualToggle(ativado) {
        if (!labelPularDia) return;
        if (ativado) {
            labelPularDia.style.color = '#ef4444';
            labelPularDia.style.fontWeight = 'bold';
            labelPularDia.innerText = "Dia Pulado (Fechado)";
        } else {
            labelPularDia.style.color = '#6b7280';
            labelPularDia.style.fontWeight = 'normal';
            labelPularDia.innerText = "Pular Dia (Loja Fechada)";
        }
    }

    if (checkPularDia) {
        atualizarVisualToggle(checkPularDia.checked);
        checkPularDia.addEventListener('change', function() {
            atualizarVisualToggle(this.checked);
            inputToggleStatus.value = this.checked ? 'true' : 'false';
            setTimeout(() => { formToggle.submit(); }, 200);
        });
    }

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

            if (checkPularDia) {
                checkPularDia.checked = dados.loja_fechada;
                atualizarVisualToggle(dados.loja_fechada);
            }

            document.getElementById('display-data').innerHTML = `${dados.data_formatada} <i class="fas fa-caret-down" style="font-size: 0.8em; opacity: 0.5;"></i>`;
            if(seletorData) seletorData.value = dados.data_iso;

            btnAnt.dataset.dest = dados.nav.anterior;
            btnProx.dataset.dest = dados.nav.proximo;
            btnAnt.href = `/${dados.nav.anterior}/`;
            btnProx.href = `/${dados.nav.proximo}/`;
            window.history.pushState({path: dataIso}, '', `/${dataIso}/`);

            const inputInicial = document.getElementById('saldo-inicial');
            const inputFinal = document.getElementById('saldo-final');
            if(inputInicial) inputInicial.value = dados.saldos.inicial.toFixed(2);
            
            // Atualiza Saldo Final com Máscara
            if(inputFinal) {
                // Formata para 1000.00 -> 100000 -> 1.000,00
                let valorRaw = (dados.saldos.final * 100).toFixed(0); 
                inputFinal.value = valorRaw;
                aplicarMascaraMoeda(inputFinal);
            }

            const fmt = (v) => v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('val-cartao').innerText = fmt(dados.totais.cartao);
            document.getElementById('val-entrada-esp').innerText = fmt(dados.totais.entradas_esp);
            document.getElementById('val-dinheiro-calc').innerText = fmt(dados.totais.dinheiro_miudo);
            document.getElementById('val-geral').innerText = fmt(dados.totais.geral);

            const txtFormula = `*Dinheiro = (${dados.totais.retiradas} Saídas + ${dados.saldos.final} Sobrou) - (${dados.saldos.inicial} Início + ${dados.totais.entradas_esp} Suprimentos)`;
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

                if (mov.tipo === 'CARTAO') { classeCss = 'tipo-cartao'; icone = '<i class="fas fa-credit-card"></i>'; subtexto = 'Cartão/Pix'; sinal = '+'; } 
                else if (mov.tipo === 'DINHEIRO') { classeCss = 'tipo-dinheiro'; icone = '<i class="fas fa-coins"></i>'; subtexto = 'Suprimento/Entrada'; sinal = '+'; }

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