from django.db import models
from ordered_model.models import OrderedModel
from .storages import OverwriteStorage


TIPOS_RASPADOR = (
    ('1', 'Tribunal de Justiça do Rio de Janeiro'),
    ('2', 'Arquivo Tabulado'),
)


SITUACOES_FILTRO = (
    ('1', 'Em Criação'),
    ('2', 'Baixando Documentos'),
    ('3', 'Documentos Baixados'),
    ('4', 'Executando Filtros'),
    ('5', 'Documentos Classificados'),
    ('6', 'Compactando'),
    ('7', 'Download Disponível')
)

TIPOS_FILTRO = (
    ('1', 'Expressão Principal'),
    ('2', 'Expressão Reforço'),
    ('3', 'Termos de Exclusão'),
    ('4', 'Termos de Invalidação'),
    ('5', 'Termos de Reforço'),
)


class TipoMovimento(models.Model):
    nome = models.CharField(max_length=50)
    nome_tj = models.CharField(max_length=50)

    def __str__(self):
        if self:
            return self.nome


class Filtro(models.Model):
    nome = models.CharField(max_length=50)
    tipo_raspador = models.CharField(
        max_length=1,
        choices=TIPOS_RASPADOR,
        blank=True,
        null=True
    )
    tipos_movimento = models.ManyToManyField('TipoMovimento', blank=True)
    arquivo_documentos = models.FileField(null=True, blank=True)
    situacao = models.CharField(
        max_length=1,
        choices=SITUACOES_FILTRO,
        default='1'
    )
    saida = models.FileField(null=True, blank=True, storage=OverwriteStorage())
    saida_lda = models.TextField(null=True, blank=True)
    responsavel = models.CharField(max_length=50, default='')
    percentual_atual = models.FloatField(null=True, blank=True)

    def __str__(self):
        if self:
            return self.nome


class UsuarioAcessoFiltro(models.Model):
    filtro = models.ForeignKey('Filtro', on_delete=models.CASCADE)
    usuario = models.CharField(max_length=50)

    def __str__(self):
        if self:
            return self.usuario


class ClasseFiltro(OrderedModel):
    filtro = models.ForeignKey('Filtro', on_delete=models.CASCADE)
    nome = models.CharField(max_length=50)
    order_with_respect_to = 'filtro'

    class Meta(OrderedModel.Meta):
        pass

    def __str__(self):
        if self:
            return self.nome


class ItemFiltro(models.Model):
    classe_filtro = models.ForeignKey('ClasseFiltro', on_delete=models.CASCADE)
    termos = models.CharField(max_length=255)
    tipo = models.CharField(max_length=1, choices=TIPOS_FILTRO)
    regex = models.BooleanField(default=False)


class Documento(models.Model):
    classe_filtro = models.ForeignKey(
        'ClasseFiltro',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    filtro = models.ForeignKey('Filtro', on_delete=models.CASCADE)
    numero = models.CharField(max_length=32)
    tipo_movimento = models.ForeignKey(
        'TipoMovimento',
        on_delete=models.CASCADE,
        blank=True,
        null=True
    )
    conteudo = models.TextField()
