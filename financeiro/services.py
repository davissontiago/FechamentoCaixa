from decimal import Decimal
from .models import Movimentacao, FechamentoCaixa

class GestorCaixa:
    def __init__(self, fechamento):
        """
        Ao instanciar a classe, passamos o dia (fechamento) com o qual vamos trabalhar.
        Ex: gestor = GestorCaixa(fechamento_de_hoje)
        """
        self.fechamento = fechamento

    def calcular_resumo(self):
        """
        Usa o QuerySet inteligente para pegar os totais e 
        aplica a regra de negócio do 'Dinheiro Calculado'.
        """
        # 1. Usar o nosso QuerySet novo para pegar os dados do banco
        totais = Movimentacao.objects.filter(fechamento=self.fechamento).resumo_rapido()
        
        # Tratamento de Nones (Se não tiver venda, vira 0.00)
        venda_cartao = totais['total_cartao'] or Decimal('0.00')
        suprimentos = totais['total_suprimento'] or Decimal('0.00')
        saidas = totais['total_saida'] or Decimal('0.00')
        
        # 2. A Fórmula Matemática (Regra de Negócio)
        venda_dinheiro = (self.fechamento.saldo_final + saidas) - (self.fechamento.saldo_inicial + suprimentos)
        
        if venda_dinheiro < 0:
            venda_dinheiro = Decimal('0.00')
        
        return {
            'cartao': venda_cartao,
            'dinheiro': venda_dinheiro, 
            'saidas': saidas,
            'suprimentos': suprimentos,
            'total_geral': venda_cartao + venda_dinheiro 
        }

    def atualizar_cache_do_banco(self):
        """
        Este método será chamado pelo Signals ou pela View para salvar
        os totais no modelo FechamentoCaixa (para o relatório mensal ficar rápido).
        """
        totais = Movimentacao.objects.filter(fechamento=self.fechamento).resumo_rapido()
        
        self.fechamento.cache_total_cartao = totais['total_cartao'] or 0
        self.fechamento.cache_total_saida = totais['total_saida'] or 0
        self.fechamento.cache_total_suprimento = totais['total_suprimento'] or 0
        
        self.fechamento.save(update_fields=[
            'cache_total_cartao', 
            'cache_total_saida', 
            'cache_total_suprimento'
        ])
        