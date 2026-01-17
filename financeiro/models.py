# financeiro/models.py
from django.db import models
from django.utils import timezone

class FechamentoCaixa(models.Model):
    data = models.DateField(default=timezone.now, unique=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_final_fisico = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Fechamento {self.data}"

class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('CARTAO', 'Vendas no Cartão/Pix'),      # Entra na receita, NÃO mexe no caixa físico
        ('DINHEIRO', 'Entrada em Dinheiro'), # Entra na receita e SOMA no caixa físico (Ex: Pagamento Grande)
        ('SAIDA', 'Saídas em Dinheiro'),          # SUBTRAI do caixa físico
    ]
    fechamento = models.ForeignKey(FechamentoCaixa, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='CARTAO')
    nome = models.CharField(max_length=100) 
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nome}: R$ {self.valor}"