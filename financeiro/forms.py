from django import forms
from .models import FechamentoCaixa, Movimentacao

class FechamentoSaldoForm(forms.ModelForm):
    class Meta:
        model = FechamentoCaixa
        fields = ['saldo_inicial', 'saldo_final_fisico']
        widgets = {
            # AQUI ESTÁ A MÁGICA: Adicionamos o atributo readonly
            'saldo_inicial': forms.NumberInput(attrs={
                'readonly': 'readonly', 
                'class': 'bg-gray-100 cursor-not-allowed', # Classes visuais (opcional se usar tailwind)
                'style': 'background-color: #e5e7eb; color: #6b7280;' # Estilo inline para garantir cinza
            }),
            'saldo_final_fisico': forms.NumberInput(attrs={'step': '0.01'}),
        }

class MovimentacaoRapidaForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo', 'valor', 'nome']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Descrição (Ex: Almoço, Sangria...)'}),
        }