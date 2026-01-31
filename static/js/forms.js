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

        // Auto-save específico para o campo de saldo final
        if (input.id === 'id_saldo_final') {
             // CORREÇÃO: Removemos o bloqueio do 'keypress' (Enter) para o botão "Ir" funcionar.
             
             // Mantemos apenas o auto-save ao sair do campo (clicar fora)
             input.addEventListener('blur', function () {
                setTimeout(() => {
                    const form = this.closest('form');
                    // Só dispara o auto-save se o formulário JÁ NÃO estiver sendo enviado (pelo Enter)
                    if (form && !form.dataset.isSubmitting) {
                        dispararSubmitLimpo(form);
                    }
                }, 200);
            });
        }
    });

    // 2. INTERCEPTAÇÃO DE SUBMIT (Limpa R$)
    document.querySelectorAll('form').forEach(form => {
        if (form.querySelector('.money-mask')) {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); 
                dispararSubmitLimpo(this);
            });
        }
    });

    function dispararSubmitLimpo(form) {
        // Proteção contra envio duplo (Enter + Blur ao mesmo tempo)
        if (form.dataset.isSubmitting === 'true') return;
        form.dataset.isSubmitting = 'true';

        // Feedback Visual (Bloqueia botão e mostra loading)
        const btn = form.querySelector('button[type="submit"]');
        if (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.7';
            // Se o botão não tiver ícone, coloca um spinner, senão mantém o layout
            if (!btn.innerHTML.includes('fa-spinner')) {
                // Salva largura para não pular
                const width = btn.offsetWidth;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                btn.style.width = width + 'px';
            }
        }

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
        const categoriaPreSelecionada = selCat.value; 

        function atualizarSelect(ehCarregamentoInicial = false) {
            const tipoTransacao = selTipo.value;
            
            selCat.innerHTML = '';

            const defaultOption = document.createElement('option');
            defaultOption.value = "";
            defaultOption.text = "--- Selecione a Categoria ---";
            defaultOption.disabled = true; 
            defaultOption.selected = true; 
            selCat.appendChild(defaultOption);

            if (!tipoTransacao) {
                defaultOption.text = "← Escolha o tipo antes";
                selCat.disabled = true;
                selCat.style.backgroundColor = "#f3f4f6";
                return;
            }

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

                if (ehCarregamentoInicial && categoriaPreSelecionada) {
                    const existe = catsFiltradas.some(c => c.id == categoriaPreSelecionada);
                    if (existe) {
                        selCat.value = categoriaPreSelecionada;
                    }
                }
            }
        }
        
        selTipo.addEventListener('change', function() {
            atualizarSelect(false);
        });
        
        atualizarSelect(true);
    }
});