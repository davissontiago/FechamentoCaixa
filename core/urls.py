from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from financeiro.views import *
urlpatterns = [
    path('admin/', admin.site.urls),
    
    # === RELATÓRIOS E CATEGORIAS ===
    path('resumo/', resumo_financeiro, name='resumo_financeiro'),
    path('categorias/', gerenciar_categorias, name='gerenciar_categorias'),
    path('categorias/nova/', salvar_categoria, name='nova_categoria'),
    path('categorias/editar/<int:id>/', editar_categoria, name='editar_categoria'),
    path('categorias/deletar/<int:id>/', deletar_categoria, name='deletar_categoria'),

    # === API (Usada pelo Javascript) ===
    path('api/dados/<str:data_iso>/', api_dados_caixa, name='api_dados_caixa'),

    # === MOVIMENTAÇÕES (Formulários) ===
    # O erro mostrou um 'salvar/' solto antes, removi ele para evitar confusão
    path('movimentacao/salvar/<str:data_iso>/', salvar_movimentacao, name='salvar_movimentacao'),
    path('movimentacao/editar/<int:id>/', editar_movimentacao, name='editar_movimentacao'),
    path('movimentacao/deletar/<int:id>/', deletar_movimentacao, name='deletar_movimentacao'),

    # === SISTEMA DE LOGIN ===
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('accounts/', include('django.contrib.auth.urls')), 

    # === PWA (Funcionalidades Offline) ===
    path('', include('pwa.urls')),

    # === CAIXA DIÁRIO (Home e Datas) ===
    path('', diario_caixa, name='home'),
    
    # CORREÇÃO AQUI: Adicionado 'caixa/' antes da data para bater com o JavaScript
    path('caixa/<str:data_iso>/', diario_caixa, name='caixa_dia'),
]