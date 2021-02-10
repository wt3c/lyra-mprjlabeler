import re

from django import forms
from .models import (
    Filtro,
    ClasseFiltro,
    ItemFiltro
)


class BaseModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for key in self.fields:
            field = self.fields[key]
            if type(field.widget) == forms.TextInput:
                field.widget.attrs['class'] = 'form-control'
            elif (type(field.widget) == forms.SelectMultiple
                    or type(field.widget) == forms.Select):
                field.widget.attrs['class'] = 'selectpicker form-control'
                field.widget.attrs['data-style'] = 'form-control'
                field.widget.attrs['title'] = 'Selecione as Opções Desejadas'


class AdicionarFiltroForm(BaseModelForm):
    prefix = 'adicionar_filtro'

    class Meta:
        model = Filtro
        fields = ['nome']

    estrutura = forms.FileField(required=False)


class FiltroForm(BaseModelForm):
    prefix = 'filtro'

    class Meta:
        model = Filtro
        fields = [
            'nome',
            'tipo_raspador',
            'tipos_movimento',
            'arquivo_documentos'
        ]


class AdicionarClasseForm(BaseModelForm):
    prefix = 'classe'
    idclasse = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput()
    )

    class Meta:
        model = ClasseFiltro
        fields = ['nome']


class ItemFiltroForm(BaseModelForm):
    prefix = 'itemfiltro'
    idclasse = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput()
    )
    idfiltro = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput()
    )
    iditemfiltro = forms.CharField(
        required=False,
        widget=forms.widgets.HiddenInput()
    )

    def clean(self):
        cleaned_data = super().clean()
        regex = cleaned_data["regex"]
        termos = cleaned_data["termos"]
        if regex:
            try:
                re.compile(termos)
            except re.error:
                raise forms.ValidationError(
                    "A expressão regular contém um ou mais erros"
                )

        return cleaned_data

    class Meta:
        model = ItemFiltro
        fields = ['termos', 'tipo', 'regex']
