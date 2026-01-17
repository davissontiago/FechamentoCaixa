# financeiro/forms.py
from django import forms
from .models import Movimentacao, FechamentoCaixa

# Formulário para as movimentações (Cartão/Sangria)
class MovimentacaoRapidaForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo', 'nome', 'valor']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Marcado Pago, Compra Jonas'}),
            'valor': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'R$ 0,00'}),
        }

# NOVO: Formulário para os Saldos do Dia
class FechamentoSaldoForm(forms.ModelForm):
    class Meta:
        model = FechamentoCaixa
        fields = ['saldo_inicial', 'saldo_final_fisico']
        widgets = {
            # Adicionei 'readonly': 'readonly' e mudei a cor de fundo para cinza (bg-gray-100)
            'saldo_inicial': forms.NumberInput(attrs={
                'class': 'form-control bg-gray-100', 
                'placeholder': '0.00',
                'readonly': 'readonly' 
            }),
            'saldo_final_fisico': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00'}),
        }