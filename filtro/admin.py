from django.contrib import admin
from .models import (
    TipoMovimento,
    Filtro,
    ClasseFiltro,
    ItemFiltro,
    Documento,
)

class DocumentoAdmin(admin.ModelAdmin):
    list_display = ['numero', 'tipo_movimento', 'classe_filtro']

# Register your models here.
admin.site.register(TipoMovimento)
admin.site.register(Filtro)
admin.site.register(ClasseFiltro)
admin.site.register(ItemFiltro)
admin.site.register(Documento, DocumentoAdmin)
