from django.db import models
from django.db.models import Sum, Q

# 1. QUERYSET INTELIGENTE
class MovimentacaoQuerySet(models.QuerySet):
    def resumo_rapido(self):
        """
        Calcula os totais diretamente no banco de dados.
        Retorna um dicionário com os valores prontos.
        """
        return self.aggregate(
            total_cartao=Sum('valor', filter=Q(tipo='CARTAO')),
            total_suprimento=Sum('valor', filter=Q(tipo='DINHEIRO')),
            total_saida=Sum('valor', filter=Q(tipo='SAIDA'))
        )

# 2. MODELO DE CATEGORIA
class Categoria(models.Model):
    TIPO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
        ('CARTAO', 'Cartão/Pix'),
    ]
    nome = models.CharField(max_length=50)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    
    def __str__(self):
        return self.nome

# 3. MODELO DE FECHAMENTO
class FechamentoCaixa(models.Model):
    data = models.DateField(unique=True)
    saldo_inicial = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_final = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    cache_total_cartao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cache_total_saida = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cache_total_suprimento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"Caixa {self.data}"

# 4. MODELO DE MOVIMENTACAO
class Movimentacao(models.Model):
    TIPO_CHOICES = [
        ('DINHEIRO', 'Entrada Dinheiro'),
        ('CARTAO', 'Cartão/Pix'),
        ('SAIDA', 'Saída'),
        ('REGISTRO', 'Registro'),
    ]

    fechamento = models.ForeignKey(FechamentoCaixa, on_delete=models.CASCADE, related_name='movimentacoes')
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='SAIDA', db_index=True)
    
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=200, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    objects = MovimentacaoQuerySet.as_manager()

    def __str__(self):
        return f"{self.get_tipo_display()} - R$ {self.valor}"