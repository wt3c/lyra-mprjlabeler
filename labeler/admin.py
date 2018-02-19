"Admin config"
from django.contrib import admin
from .models import Campanha, Formulario, Tarefa, Trabalho


admin.site.register(Campanha)
admin.site.register(Formulario)
admin.site.register(Tarefa)
admin.site.register(Trabalho)

admin.site.site_header = "Lyra Labeling System"
