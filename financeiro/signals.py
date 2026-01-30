from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, Q
from .models import Movimentacao

@receiver([post_save, post_delete], sender=Movimentacao)
def atualizar_cache_fechamento(sender, instance, **kwargs):
    fechamento = instance.fechamento

    # Recalcula e salva no fechamento
    resumo = fechamento.movimentacoes.aggregate(
        cartao=Sum('valor', filter=Q(tipo='CARTAO')),
        saida=Sum('valor', filter=Q(tipo='SAIDA'))
    )

    fechamento.cache_total_cartao = resumo['cartao'] or 0
    fechamento.cache_total_saida = resumo['saida'] or 0
    fechamento.save()