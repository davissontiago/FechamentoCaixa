from django.contrib import admin
from django.urls import path, include
from financeiro.views import diario_caixa, api_dados_caixa, deletar_movimentacao, editar_movimentacao, resumo_financeiro

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # === IMPORTANTE: O Resumo deve vir ANTES da rota de data ===
    path('resumo/', resumo_financeiro, name='resumo_financeiro'),
    
    # Rotas da API e Ações
    path('api/dados/<str:data_iso>/', api_dados_caixa, name='api_dados_caixa'),
    path('deletar/<int:id>/', deletar_movimentacao, name='deletar_movimentacao'),
    path('editar/<int:id>/', editar_movimentacao, name='editar_movimentacao'),
    
    # Autenticação e PWA
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('pwa.urls')),

    # === Rotas de Navegação (Devem ficar por último) ===
    path('', diario_caixa, name='home'),
    
    # ESTA É A CORREÇÃO: Removemos o 'caixa/' do início para aceitar '/2026-01-26/'
    path('<str:data_iso>/', diario_caixa, name='caixa_dia'),
]