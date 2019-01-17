from django import forms
from .models import Filtro


class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in self.fields:
            field = self.fields[key]
            if type(field.widget) == forms.TextInput:
                field.widget.attrs['class'] = 'form-control'
            elif type(field.widget) == forms.SelectMultiple:
                field.widget.attrs['class'] = 'selectpicker form-control'
                field.widget.attrs['data-style'] = 'form-control'
                field.widget.attrs['title'] = 'Selecione as Opções Desejadas'
                

class AdicionarFiltroForm(BaseModelForm):
    class Meta:
        model = Filtro
        fields = ['nome']


class FiltroForm(BaseModelForm):
    class Meta:
        model = Filtro
        fields = ['nome', 'tipos_movimento', 'arquivo_documentos']
