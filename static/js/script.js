document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Caixa V10 - Refatorado");

    // ============================================================
    // 1. MÁSCARAS E FORMATAÇÃO (DINHEIRO)
    // ============================================================
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
        // Formata valor inicial se houver
        if (input.value) {
            let valCru = input.value.replace('.', '').replace(',', '');
            input.value = valCru;
            aplicarMascaraMoeda(input);
        }
        
        if (!input.readOnly) {
            input.addEventListener('input', function() { aplicarMascaraMoeda(this); });
            input.addEventListener('focus', function() { this.select(); });
        }

        // Auto-save específico para o campo de saldo final
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

    // ============================================================
    // 2. ENVIO SEGURO DE FORMULÁRIO (Remove pontos/vírgulas)
    // ============================================================
    function dispararSubmitLimpo(form) {
        const inputs = form.querySelectorAll('.money-mask');
        inputs.forEach(input => {
            if(input.value) {
                let valorLimpo = input.value.replace(/\./g, "").replace(",", ".");
                let hiddenName = input.name;
                if (!hiddenName) return;

                // Cria ou atualiza input hidden com valor numérico puro
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
                // Remove nome do input mascarado para não enviar duplicado
                input.removeAttribute('name');
            }
        });
        console.log("Enviando dados limpos...");
        form.submit();
    }

    // Intercepta submits normais para limpar dinheiro
    document.querySelectorAll('form').forEach(form => {
        if (form.querySelector('.money-mask')) {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); 
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

    // ============================================================
    // 3. NAVEGAÇÃO E MENU LATERAL
    // ============================================================
    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');
    const seletorData = document.getElementById('seletor-data');
    
    // Menu Mobile
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

    // Navegação entre dias
    function handleNavegacao(e) {
        if (e.metaKey || e.ctrlKey) return;
        e.preventDefault();
        carregarDia(this.dataset.dest); // Chama AJAX
    }

    if(btnAnt && btnProx) {
        btnAnt.addEventListener('click', handleNavegacao);
        btnProx.addEventListener('click', handleNavegacao);
    }

    if (seletorData) {
        seletorData.addEventListener('change', function(e) {
            carregarDia(this.value); // Chama AJAX
        });
    }

    // ============================================================
    // 4. LÓGICA DO DIA (AJAX) - O CORAÇÃO DA PÁGINA
    // ============================================================
    async function carregarDia(dataIso) {
        try {
            // Efeito visual de carregamento
            document.querySelector('.content-area').style.opacity = '0.5';
            
            // Busca dados
            const response = await fetch(`/api/dados/${dataIso}/`);
            if (!response.ok) throw new Error('Erro API');
            const dados = await response.json();

            // 1. Atualiza Data e URL
            document.getElementById('display-data').innerHTML = `${dados.data_formatada} <i class="fas fa-caret-down"></i>`;
            if(seletorData) seletorData.value = dados.data_iso;
            window.history.pushState({path: dataIso}, '', `/caixa/${dataIso}/`);

            // 2. Atualiza Botões de Navegação
            btnAnt.dataset.dest = dados.nav.anterior;
            btnProx.dataset.dest = dados.nav.proximo;
            btnAnt.href = `/caixa/${dados.nav.anterior}/`;
            btnProx.href = `/caixa/${dados.nav.proximo}/`;

            // 3. ATUALIZA O BOTÃO FLUTUANTE (NOVO!)
            const fabBtn = document.querySelector('.fab-btn');
            if (fabBtn) {
                // Aponta para a rota nova de salvar
                fabBtn.href = `/movimentacao/salvar/${dados.data_iso}/`;
            }

            // 4. Atualiza Saldos (Inputs)
            const inputInicial = document.getElementById('saldo-inicial');
            const inputFinal = document.getElementById('saldo-final');
            if(inputInicial) {
                inputInicial.value = (dados.saldos.inicial * 100).toFixed(0);
                aplicarMascaraMoeda(inputInicial);
            }
            if(inputFinal) {
                inputFinal.value = (dados.saldos.final * 100).toFixed(0);
                aplicarMascaraMoeda(inputFinal);
            }

            // 5. Atualiza Card de Resumo
            const fmt = (v) => v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            const setTxt = (id, val) => { 
                const el = document.getElementById(id); 
                if(el) el.innerText = fmt(val); 
            };

            setTxt('val-cartao', dados.totais.cartao);
            setTxt('val-entrada-esp', dados.totais.entradas_esp);
            setTxt('val-dinheiro-calc', dados.totais.dinheiro_miudo);
            setTxt('val-geral', dados.totais.geral);

            // 6. Reconstrói a Lista de Movimentações
            const listaDiv = document.getElementById('lista-movimentacoes');
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

                let descHtml = mov.descricao ? 
                    `<div class="item-desc"><i class="fas fa-quote-left"></i> ${mov.descricao}</div>` : '';

                // Link para edição (usa URL que vem da API ou monta manualmente se precisar)
                // Nota: O HTML original usa <a> envolvendo tudo. Vamos manter esse padrão.
                const htmlItem = `
                    <a href="${mov.url_editar}" class="link-item">
                        <div class="line-item ${classeCss}">
                            <div class="icon-box">${icone}</div>
                            <div class="info-box">
                                <div class="item-name">${mov.categoria}</div>
                                <div class="item-sub">${subtexto}</div>
                                ${descHtml}
                            </div>
                            <div class="valor">${sinal} R$ ${mov.valor.toFixed(2)}</div>
                        </div>
                    </a>`;
                
                listaDiv.insertAdjacentHTML('beforeend', htmlItem);
            });

        } catch (error) {
            console.error("Erro ao carregar dia:", error);
        } finally {
            document.querySelector('.content-area').style.opacity = '1';
        }
    }

    // ============================================================
    // 5. UTILITÁRIOS (Categorias e Delete)
    // ============================================================
    
    // Lógica do Select de Categorias (Para a página de Form)
    const selTipo = document.getElementById('select-tipo');
    const selCat = document.getElementById('select-categoria');
    
    if (selTipo && selCat) {
        const categoriaPreSelecionada = selCat.dataset.preselect || selCat.value; 

        function atualizarSelect(manterSelecionado = false) {
            const tipoTransacao = selTipo.value;
            
            if (!tipoTransacao) {
                selCat.innerHTML = '<option value="">← Escolha o tipo antes</option>';
                selCat.disabled = true;
                selCat.style.backgroundColor = "#f3f4f6";
                return;
            }

            selCat.disabled = false;
            selCat.style.backgroundColor = "#fff";
            
            let tipoFiltro = 'SAIDA'; 
            if (tipoTransacao === 'DINHEIRO') tipoFiltro = 'ENTRADA';
            else if (tipoTransacao === 'CARTAO') tipoFiltro = 'CARTAO';
            
            selCat.innerHTML = '';
            
            if (typeof categoriasDados !== 'undefined') {
                const catsFiltradas = categoriasDados.filter(c => c.tipo === tipoFiltro);
                
                catsFiltradas.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.id;
                    opt.text = c.nome;
                    selCat.appendChild(opt);
                });
                
                if (catsFiltradas.length === 0) {
                    selCat.innerHTML = '<option value="">--- Nenhuma categoria ---</option>';
                }

                if (manterSelecionado && categoriaPreSelecionada) {
                    const existe = catsFiltradas.some(c => c.id == categoriaPreSelecionada);
                    if (existe) selCat.value = categoriaPreSelecionada;
                }
            }
        }
        
        selTipo.addEventListener('change', () => atualizarSelect(false));
        atualizarSelect(true);
    }
});