from django.db import models
from django.utils import timezone

class FechamentoCaixa(models.Model):
    data = models.DateField(default=timezone.now, unique=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    saldo_final_fisico = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loja_fechada = models.BooleanField(default=False)

    def __str__(self):
        status = "Fechado" if self.loja_fechada else "Aberto"
        return f"{self.data} - {status}"

class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('DINHEIRO', 'Entrada Dinheiro'),
        ('CARTAO', 'Cartão/Pix'),
        ('SAIDA', 'Saída/Sangria'),
    ]
    fechamento = models.ForeignKey(FechamentoCaixa, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.nome} - R$ {self.valor}"