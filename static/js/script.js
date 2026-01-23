document.addEventListener("DOMContentLoaded", function() {
    // Submeter formulário de saldos ao sair do campo (onblur)
    const saldoInputs = document.querySelectorAll('.saldo-input input');
    const formSaldos = document.getElementById('form-saldos');

    if (saldoInputs.length > 0 && formSaldos) {
        saldoInputs.forEach((input) => {
            input.addEventListener('blur', function () {
                // Pequeno delay ou verificação para evitar envios duplos desnecessários pode ser adicionado aqui
                formSaldos.submit();
            });
        });
    }

    // Confirmação para deletar (agora generalizado)
    const deleteLinks = document.querySelectorAll('.btn-delete');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja apagar?')) {
                e.preventDefault();
            }
        });
    });
});