/* ============================================================
   CATEGORIAS.JS - Lógica de Filtro
   ============================================================ */

document.addEventListener("DOMContentLoaded", function() {
    
    const buttons = document.querySelectorAll('.filter-btn');
    const items = document.querySelectorAll('.cat-card-link');

    buttons.forEach(btn => {
        btn.addEventListener('click', function() {
            // 1. Remove classe ativa de todos e adiciona no clicado
            buttons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');

            // 2. Pega o tipo escolhido (all, ENTRADA, SAIDA, CARTAO)
            const type = this.dataset.filter;

            // 3. Filtra a lista
            items.forEach(item => {
                if (type === 'all' || item.dataset.type === type) {
                    item.style.display = 'block'; // Mostra
                } else {
                    item.style.display = 'none'; // Esconde
                }
            });
        });
    });

});