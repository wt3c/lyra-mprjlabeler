import nested_admin
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


class ItemFiltroInline(nested_admin.NestedTabularInline):
    model = ItemFiltro


class ClasseFiltroInline(nested_admin.NestedTabularInline):
    model = ClasseFiltro
    inlines = [ItemFiltroInline]


class FiltroAdmin(nested_admin.NestedModelAdmin):
    inlines = [ClasseFiltroInline]


# Register your models here.
admin.site.register(TipoMovimento)
admin.site.register(Filtro, FiltroAdmin)
admin.site.register(ClasseFiltro)
admin.site.register(ItemFiltro)
admin.site.register(Documento, DocumentoAdmin)
