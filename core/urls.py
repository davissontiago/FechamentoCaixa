# core/urls.py
from django.contrib import admin
from django.urls import path, include
from financeiro.views import diario_caixa, deletar_movimentacao, editar_movimentacao

urlpatterns = [
    path('admin/', admin.site.urls),

    # Adicione isto: URLs de Auth padrão (login, logout, password_reset)
    path('accounts/', include('django.contrib.auth.urls')),

    # ... (suas rotas antigas continuam aqui) ...
    path('deletar/<int:id>/', deletar_movimentacao, name='deletar_movimentacao'),
    path('editar/<int:id>/', editar_movimentacao, name='editar_movimentacao'),
    path('', include('pwa.urls')),
    path('', diario_caixa, name='home'),
    path('<str:data_iso>/', diario_caixa, name='caixa_dia'),
]