/* ============================================================
   FORMS.JS - Máscaras, Submit Seguro e Lógica de Categorias
   ============================================================ */

document.addEventListener("DOMContentLoaded", function() {
    
    // 1. MÁSCARAS DE DINHEIRO NOS INPUTS
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
    });

    // 2. INTERCEPTAÇÃO DE SUBMIT (Limpa R$)
    document.querySelectorAll('form').forEach(form => {
        if (form.querySelector('.money-mask')) {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); 
                const btn = this.querySelector('button[type="submit"]');
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
        form.submit();
    }

    // 3. LÓGICA DE CATEGORIAS (SEGURANÇA ATIVADA)
    const selTipo = document.getElementById('select-tipo');
    const selCat = document.getElementById('select-categoria');
    
    if (selTipo && selCat) {
        // Pega o valor que veio do banco (apenas para EDIÇÃO)
        // Se for novo cadastro, isso será vazio.
        const categoriaPreSelecionada = selCat.value; 

        function atualizarSelect(ehCarregamentoInicial = false) {
            const tipoTransacao = selTipo.value;
            
            // 1. LIMPA TUDO PRIMEIRO
            selCat.innerHTML = '';

            // 2. OPÇÃO PADRÃO DE SEGURANÇA (Sempre aparece primeiro)
            const defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.text = "--- Selecione a Categoria ---";
            defaultOption.disabled = true; // O usuário não pode clicar para "escolher" vazio
            defaultOption.selected = true; // Mas ela começa selecionada visualmente
            selCat.appendChild(defaultOption);

            // 3. SE NÃO TIVER TIPO, BLOQUEIA E PARA
            if (!tipoTransacao) {
                defaultOption.text = "← Escolha o tipo antes";
                selCat.disabled = true;
                selCat.style.backgroundColor = "#f3f4f6";
                return;
            }

            // 4. SE TIVER TIPO, LIBERA E FILTRA
            selCat.disabled = false;
            selCat.style.backgroundColor = "#fff";
            
            let tipoFiltro = 'SAIDA'; 
            if (tipoTransacao === 'DINHEIRO') tipoFiltro = 'ENTRADA';
            else if (tipoTransacao === 'CARTAO') tipoFiltro = 'CARTAO';
            
            if (typeof categoriasDados !== 'undefined') {
                const catsFiltradas = categoriasDados.filter(c => c.tipo === tipoFiltro);
                
                if (catsFiltradas.length > 0) {
                    catsFiltradas.forEach(c => {
                        const opt = document.createElement('option');
                        opt.value = c.id;
                        opt.text = c.nome;
                        selCat.appendChild(opt);
                    });
                } else {
                    defaultOption.text = "--- Nenhuma categoria encontrada ---";
                }

                // 5. LÓGICA DE PREENCHIMENTO (Só seleciona se for EDIÇÃO)
                if (ehCarregamentoInicial && categoriaPreSelecionada) {
                    // Verifica se a categoria salva ainda é compatível com o filtro atual
                    const existe = catsFiltradas.some(c => c.id == categoriaPreSelecionada);
                    if (existe) {
                        selCat.value = categoriaPreSelecionada;
                    }
                }
                // Se NÃO for edição (novo), ele mantém a defaultOption selecionada
            }
        }
        
        selTipo.addEventListener('change', function() {
            // Quando troca o tipo manualmente, força reset (passa false)
            atualizarSelect(false);
        });
        
        // No carregamento da página, tenta recuperar valor (passa true)
        atualizarSelect(true);
    }
});