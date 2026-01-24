from django import forms
from .models import FechamentoCaixa, Movimentacao

class FechamentoSaldoForm(forms.ModelForm):
    class Meta:
        model = FechamentoCaixa
        fields = ['saldo_inicial', 'saldo_final_fisico']
        widgets = {
            # Saldo Inicial agora é Texto com Máscara (para formatar igual dinheiro)
            'saldo_inicial': forms.TextInput(attrs={
                'readonly': 'readonly', 
                'class': 'money-mask',
                'style': 'background-color: #f3f4f6; color: #6b7280; cursor: not-allowed;'
            }),
            'saldo_final_fisico': forms.TextInput(attrs={
                'class': 'money-mask', 
                'inputmode': 'numeric',
                'placeholder': '0,00'
            }),
        }

class MovimentacaoRapidaForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo', 'valor', 'nome']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Descrição (Ex: Almoço, Sangria...)'}),
            'valor': forms.TextInput(attrs={
                'class': 'money-mask', 
                'inputmode': 'numeric', 
                'placeholder': '0,00'
            }),
        }