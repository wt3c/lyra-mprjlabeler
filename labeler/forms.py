"Forms de request"
from django import forms


class RespostaForm(forms.Form):
    "Form dinâmico de construção de campos de resposta de tarefa"
    def __init__(self, *args, **kwargs):
        if 'campos' not in kwargs:
            raise Exception(
                '"campos" não foi fornecido para a criação do form')

        campos = kwargs.pop('campos')
        super(RespostaForm, self).__init__(*args, **kwargs)

        for campo in campos:
            if 'escolha' in campo:
                campo = campo['escolha']
                opcoes = campo['opcoes']
                valores = campo['valores']
                nome = campo['nome']
                label = campo['label']
                obrigatorio = False
                if 'obrigatorio' in campo:
                    obrigatorio = campo['obrigatorio']

                if campo['cardinalidade'] == 'multipla':
                    tipo_campo = forms.MultipleChoiceField
                    widget = forms.CheckboxSelectMultiple
                else:
                    tipo_campo = forms.ChoiceField
                    widget = forms.RadioSelect

                field = tipo_campo(
                    choices=zip(valores, opcoes),
                    label=label,
                    required=obrigatorio,
                    widget=widget)

            if 'check' in campo:
                campo = campo['check']
                nome = campo['nome']
                label = campo['label']
                default = campo['default']

                field = forms.BooleanField(
                    label=label,
                    initial=default,
                    required=False)

                field.widget.attrs.update({'class': 'check'})

            if field:
                self.fields[nome] = field
