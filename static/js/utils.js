/* ============================================================
   UTILS.JS - Funções utilitárias e formatadores
   ============================================================ */

/**
 * Aplica máscara de moeda (R$) em um input enquanto o usuário digita
 */
function aplicarMascaraMoeda(input) {
    let value = input.value.replace(/\D/g, ""); 
    if (value === "") return;
    value = (parseInt(value) / 100).toFixed(2) + "";
    value = value.replace(".", ",");
    value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");
    input.value = value;
}

/**
 * Formata um número float para string R$ (ex: 1250.50 -> "R$ 1.250,50")
 */
function formatarMoedaParaExibicao(valor) {
    return valor.toLocaleString('pt-BR', {style: 'currency', currency: 'BRL'});
}