from django import forms
from .models import FechamentoCaixa, Movimentacao, Categoria

class FechamentoSaldoForm(forms.ModelForm):
    class Meta:
        model = FechamentoCaixa
        fields = ['saldo_inicial', 'saldo_final']
        widgets = {
            'saldo_inicial': forms.TextInput(attrs={
                'readonly': 'readonly', 
                'class': 'money-mask input-readonly', 
            }),
            'saldo_final': forms.TextInput(attrs={
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
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Almoço, Ifood...'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

class MovimentacaoForm(forms.ModelForm):
    class Meta:
        model = Movimentacao
        fields = ['tipo', 'valor', 'categoria', 'descricao']
        widgets = {
            'valor': forms.TextInput(attrs={
                'class': 'money-mask', 
                'inputmode': 'numeric', 
                'placeholder': '0,00'
            }),
            'descricao': forms.TextInput(attrs={'placeholder': 'Descrição (Opcional)'}),
            # IDs essenciais para o script.js funcionar:
            'categoria': forms.Select(attrs={'id': 'select-categoria'}),
            'tipo': forms.Select(attrs={'id': 'select-tipo'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Ordena categorias alfabeticamente
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        
        # 2. Adiciona opção padrão "--- Tipo ---"
        escolhas_originais = [x for x in self.fields['tipo'].choices if x[0] != '']
        self.fields['tipo'].choices = [('', '--- Tipo ---')] + escolhas_originais
        
class FiltroResumoForm(forms.Form):
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), 
        label="De"
    )
    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), 
        label="Até"
    )