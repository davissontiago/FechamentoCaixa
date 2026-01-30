from django import forms
from .models import FechamentoCaixa, Movimentacao, Categoria

class FechamentoSaldoForm(forms.ModelForm):
    class Meta:
        model = FechamentoCaixa
        fields = ['saldo_inicial', 'saldo_final']
        widgets = {
            'saldo_inicial': forms.TextInput(attrs={
                'readonly': 'readonly', 
                'class': 'money-mask',
                'style': 'background-color: #f3f4f6; color: #6b7280; cursor: not-allowed;'
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
            'descricao': forms.TextInput(attrs={'placeholder': 'Descrição (Opcional)'}),
            'categoria': forms.Select(attrs={'id': 'select-categoria'}),
            'tipo': forms.Select(attrs={'id': 'select-tipo'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Ordena categorias
        self.fields['categoria'].queryset = Categoria.objects.all().order_by('nome')
        
        # 2. Define o texto da opção vazia para "--- Tipo ---"
        # Pegamos as escolhas originais, filtramos para tirar qualquer vazio antigo e adicionamos o nosso
        escolhas_originais = [x for x in self.fields['tipo'].choices if x[0] != '']
        self.fields['tipo'].choices = [('', '--- Tipo ---')] + escolhas_originais
        
class FiltroResumoForm(forms.Form):
    data_inicio = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="De")
    data_fim = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}), label="Até")