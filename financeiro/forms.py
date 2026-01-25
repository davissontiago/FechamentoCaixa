from django import forms
from .models import FechamentoCaixa, Movimentacao, Categoria

class FechamentoSaldoForm(forms.ModelForm):
    class Meta:
        model = FechamentoCaixa
        fields = ['saldo_inicial', 'saldo_final_fisico']
        widgets = {
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

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['tipo', 'nome']
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Nome da Categoria (Ex: Almoço, Ifood...)'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

class MovimentacaoRapidaForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo', 'valor', 'categoria', 'descricao']
        widgets = {
            'valor': forms.TextInput(attrs={
                'class': 'money-mask', 
                'inputmode': 'numeric', 
                'placeholder': '0,00'
            }),
            'descricao': forms.TextInput(attrs={'placeholder': 'Obs (Opcional)'}),
            'categoria': forms.Select(attrs={'id': 'select-categoria'}),
            'tipo': forms.Select(attrs={'id': 'select-tipo'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordena as categorias alfabeticamente
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')