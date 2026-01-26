document.addEventListener("DOMContentLoaded", function() {
    console.log("Sistema de Caixa V9.1 - Fix Tipo e Categoria");

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
        if (input.value) {
            let valCru = input.value.replace('.', '').replace(',', '');
            input.value = valCru;
            aplicarMascaraMoeda(input);
        }
        
        if (!input.readOnly) {
            input.addEventListener('input', function() { aplicarMascaraMoeda(this); });
            input.addEventListener('focus', function() { this.select(); });
        }

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

    // === FUNÇÃO DE ENVIO SEGURO ===
    function dispararSubmitLimpo(form) {
        const inputs = form.querySelectorAll('.money-mask');
        inputs.forEach(input => {
            if(input.value) {
                let valorLimpo = input.value.replace(/\./g, "").replace(",", ".");
                let hiddenName = input.name;
                if (!hiddenName) return;

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
                input.removeAttribute('name');
            }
        });
        console.log("Enviando dados limpos...");
        form.submit();
    }

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

    // === NAVEGAÇÃO E MENU ===
    const btnAnt = document.getElementById('btn-anterior');
    const btnProx = document.getElementById('btn-proximo');
    const seletorData = document.getElementById('seletor-data');
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

    // === LÓGICA DE CATEGORIAS (CORRIGIDA) ===
    const selTipo = document.getElementById('select-tipo');
    const selCat = document.getElementById('select-categoria');
    
    if (selTipo && selCat) {
        // Tenta pegar o valor atual (caso seja edição ou erro de form)
        const categoriaPreSelecionada = selCat.dataset.preselect || selCat.value; 

        function atualizarSelect(manterSelecionado = false) {
            const tipoTransacao = selTipo.value;
            
            // 1. SE NÃO TIVER TIPO, BLOQUEIA IMEDIATAMENTE
            if (!tipoTransacao) {
                selCat.innerHTML = '<option value="">← Escolha o tipo antes</option>';
                selCat.disabled = true;
                selCat.style.backgroundColor = "#f3f4f6";
                return;
            }

            // 2. SE TIVER TIPO, LIBERA
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

                // Tenta recuperar a seleção antiga
                if (manterSelecionado && categoriaPreSelecionada) {
                    const existe = catsFiltradas.some(c => c.id == categoriaPreSelecionada);
                    if (existe) selCat.value = categoriaPreSelecionada;
                }
            }
        }
        
        selTipo.addEventListener('change', () => atualizarSelect(false));
        
        // EXECUTA IMEDIATAMENTE AO CARREGAR A PÁGINA
        atualizarSelect(true);
    }

    // AJAX CARREGAMENTO DIA
    async function carregarDia(dataIso) {
        try {
            document.querySelector('.content-area').style.opacity = '0.5';
            const response = await fetch(`/api/dados/${dataIso}/`);
            if (!response.ok) throw new Error('Erro API');
            const dados = await response.json();

            document.getElementById('display-data').innerHTML = `${dados.data_formatada} <i class="fas fa-caret-down" style="font-size: 0.8em; opacity: 0.5;"></i>`;
            if(seletorData) seletorData.value = dados.data_iso;

            btnAnt.dataset.dest = dados.nav.anterior;
            btnProx.dataset.dest = dados.nav.proximo;
            btnAnt.href = `/${dados.nav.anterior}/`;
            btnProx.href = `/${dados.nav.proximo}/`;
            window.history.pushState({path: dataIso}, '', `/${dataIso}/`);

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

            const fmt = (v) => v.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
            document.getElementById('val-cartao').innerText = fmt(dados.totais.cartao);
            document.getElementById('val-entrada-esp').innerText = fmt(dados.totais.entradas_esp);
            document.getElementById('val-dinheiro-calc').innerText = fmt(dados.totais.dinheiro_miudo);
            document.getElementById('val-geral').innerText = fmt(dados.totais.geral);

            const txtFormula = `*Dinheiro = (${dados.totais.retiradas} Saídas + ${dados.saldos.final} Sobrou) - (${dados.saldos.inicial} Início + ${dados.totais.entradas_esp} Suprimentos)`;
            if(document.getElementById('txt-formula')) document.getElementById('txt-formula').innerText = txtFormula;

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
                    classeCss = 'tipo-cartao'; icone = '<i class="fas fa-credit-card"></i>'; subtexto = 'Cartão/Pix'; sinal = '+'; 
                } else if (mov.tipo === 'DINHEIRO') { 
                    classeCss = 'tipo-dinheiro'; icone = '<i class="fas fa-coins"></i>'; subtexto = 'Suprimento/Entrada'; sinal = '+'; 
                } else if (mov.tipo === 'REGISTRO') { 
                    classeCss = 'tipo-registro'; icone = '<i class="fas fa-file-alt"></i>'; subtexto = 'Registro'; sinal = '-'; 
                }

                let descHtml = mov.descricao ? `<div class="item-desc" style="display:none; font-size: 0.85rem; color: #6b7280; margin-top: 4px; font-style: italic;"><i class="fas fa-quote-left" style="font-size: 0.7em;"></i> ${mov.descricao}</div>` : '';

                const htmlItem = `
                    <div class="line-item ${classeCss}" onclick="toggleDesc(this)">
                        <div class="icon-box">${icone}</div>
                        <div class="info-box">
                            <div class="item-name">${mov.categoria}</div>
                            <div class="item-sub">${subtexto}</div>
                            ${descHtml}
                        </div>
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
        deleteLinks.forEach(link => link.onclick = (e) => {
            e.stopPropagation(); 
            return confirm('Tem certeza?') ? true : e.preventDefault();
        });
    }

    window.toggleDesc = function(element) {
        const desc = element.querySelector('.item-desc');
        if (desc) {
            desc.style.display = desc.style.display === 'none' ? 'block' : 'none';
        }
    }

    ativarListenersDelete();
});