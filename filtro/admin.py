import nested_admin
from django.contrib import admin
from .models import (
    TipoMovimento,
    Filtro,
    ClasseFiltro,
    ItemFiltro,
    Documento,
    UsuarioAcessoFiltro
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
    list_display = [
        'nome',
        'tipo_raspador',
        'situacao',
        'percentual_atual'
    ]
    list_filter = [
        'situacao',
        'tipo_raspador'
    ]
    search_fields = [
        'nome'
    ]

    def situacao_inicial(modeladmin, request, queryset):
        queryset.update(situacao=1)

    def documentos_baixados(modeladmin, request, queryset):
        queryset.update(situacao=3)

    situacao_inicial.short_description = 'Para Em Criação'
    documentos_baixados.short_description = 'Para Documentos Baixados'

    actions = [
        situacao_inicial,
        documentos_baixados
    ]


# Register your models here.
admin.site.register(TipoMovimento)
admin.site.register(Filtro, FiltroAdmin)
admin.site.register(ClasseFiltro)
admin.site.register(ItemFiltro)
admin.site.register(Documento, DocumentoAdmin)
admin.site.register(UsuarioAcessoFiltro)
