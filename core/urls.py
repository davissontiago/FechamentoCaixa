from django.contrib import admin
from django.urls import path, include
from financeiro.views import (
    diario_caixa, api_dados_caixa, deletar_movimentacao, 
    editar_movimentacao, resumo_financeiro, gerenciar_categorias, deletar_categoria, editar_categoria
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('resumo/', resumo_financeiro, name='resumo_financeiro'),
    path('categorias/', gerenciar_categorias, name='gerenciar_categorias'), # NOVA ROTA
    path('categorias/deletar/<int:id>/', deletar_categoria, name='deletar_categoria'), # NOVA ROTA
    path('categorias/editar/<int:id>/', editar_categoria, name='editar_categoria'),
    
    path('api/dados/<str:data_iso>/', api_dados_caixa, name='api_dados_caixa'),
    path('deletar/<int:id>/', deletar_movimentacao, name='deletar_movimentacao'),
    path('editar/<int:id>/', editar_movimentacao, name='editar_movimentacao'),
    
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('pwa.urls')),
    
    path('', diario_caixa, name='home'),
    path('<str:data_iso>/', diario_caixa, name='caixa_dia'),
]