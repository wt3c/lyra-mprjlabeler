from django.contrib import admin
from django.forms import ModelForm
from .models import Campanha, Formulario, Tarefa, Trabalho
from .widgets import QuillEditorWidget


class FormularioForm(ModelForm):
    class Meta:
        model = Formulario
        widgets = {
            'estrutura': QuillEditorWidget
        }
        fields = '__all__'

class FormularioAdmin(admin.ModelAdmin):
    form = FormularioForm

admin.site.register(Campanha)
admin.site.register(Formulario)
admin.site.register(Tarefa)
admin.site.register(Trabalho)

admin.site.site_header = "Lyra Labeling System"
