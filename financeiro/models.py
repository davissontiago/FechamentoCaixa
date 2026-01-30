from django.db import models
from django.utils import timezone

class FechamentoCaixa(models.Model):
    data = models.DateField(default=timezone.now, unique=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    saldo_final_fisico = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    loja_fechada = models.BooleanField(default=False)
    cache_total_cartao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cache_total_saida = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        status = "Fechado" if self.loja_fechada else "Aberto"
        return f"{self.data} - {status}"

class Categoria(models.Model):
    TIPO_CAT_CHOICES = [
        ('ENTRADA', 'Entradas (Dinheiro)'),
        ('CARTAO', 'Vendas Cartão/Pix'),
        ('SAIDA', 'Saídas/Despesas'),
    ]
    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_CAT_CHOICES)

    def __str__(self):
        return f"{self.nome}"

class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('DINHEIRO', 'Entrada Dinheiro'),
        ('CARTAO', 'Cartão/Pix'),
        ('SAIDA', 'Saída do Caixa'),
        ('REGISTRO', 'Registro'),
    ]
    fechamento = models.ForeignKey(FechamentoCaixa, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(
        max_length=10, 
        choices=TIPO_CHOICES,
        db_index=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT) 
    descricao = models.CharField(max_length=200, blank=True, null=True, verbose_name="Descrição (Opcional)")

    def __str__(self):
        return f"{self.categoria.nome} - R$ {self.valor}"