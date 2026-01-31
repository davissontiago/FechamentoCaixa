from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from financeiro.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # === RELATÓRIOS E CATEGORIAS ===
    path('resumo/', resumo_financeiro, name='resumo_financeiro'),
    
    path('categorias/', gerenciar_categorias, name='gerenciar_categorias'),
    path('categorias/nova/', salvar_categoria, name='nova_categoria'), # Adicionei essa que faltava na lista anterior
    path('categorias/deletar/<int:id>/', deletar_categoria, name='deletar_categoria'),
    path('categorias/editar/<int:id>/', editar_categoria, name='editar_categoria'),

    # === API ===
    path('api/dados/<str:data_iso>/', api_dados_caixa, name='api_dados_caixa'),

    # === MOVIMENTAÇÕES ===
    path('movimentacao/salvar/<str:data_iso>/', salvar_movimentacao, name='salvar_movimentacao'),
    path('movimentacao/editar/<int:id>/', editar_movimentacao, name='editar_movimentacao'),
    path('movimentacao/deletar/<int:id>/', deletar_movimentacao, name='deletar_movimentacao'),

    # === SISTEMA DE LOGIN ===
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    
    # CORREÇÃO AQUI: Usando nossa função personalizada
    path('accounts/logout/', fazer_logout, name='logout'),
    
    path('accounts/', include('django.contrib.auth.urls')), 

    # === PWA ===
    path('', include('pwa.urls')),

    # === CAIXA DIÁRIO ===
    path('', diario_caixa, name='home'),
    path('caixa/<str:data_iso>/', diario_caixa, name='caixa_dia'),
]