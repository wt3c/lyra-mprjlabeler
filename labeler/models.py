"Domínio de Dados"
from django.db import models
from yamlfield.fields import YAMLField
from sklearn.model_selection import train_test_split


class CampanhaManager(models.Manager):
    "Manager para métodos de negócio de Campanha"
    def listar_campanhas(self):
        "Listagem de Campanhas ativas"
        return Campanha.objects.filter(ativa=True)


class Campanha(models.Model):
    "Campanha de Labeling"
    objects = CampanhaManager()
    nome = models.CharField(max_length=255, unique=True)
    tarefas_por_trabalho = models.IntegerField()
    formulario = models.ForeignKey('Formulario', on_delete=models.DO_NOTHING)
    descricao = models.TextField(
        help_text="Descrição desta campanha. Você pode inserir códigos HTML.",
        default="")
    ativa = models.BooleanField(default=False)

    def _quantidade_tarefas_respondidas(self, usuario):
        trabalho = Trabalho.objects.filter(
            tarefas__campanha__id=self.id,
            username=usuario).first()
        if not trabalho:
            return 0
        ids_tarefas = trabalho.tarefas.values_list('id', flat=True)
        ids_tarefas_respondidas = Resposta.objects.filter(
            tarefa__id__in=ids_tarefas,
            username=usuario).values_list('tarefa_id', flat=True)
        quantidade_tarefas_respondidas = self.tarefa_set.filter(
            id__in=ids_tarefas_respondidas).count()

        return quantidade_tarefas_respondidas

    def completude(self, usuario):
        """Retorna o nível de completude desta campanha por usuário"""

        return int(
            (self._quantidade_tarefas_respondidas(usuario)*100)
            / self.tarefas_por_trabalho)

    def obter_tarefa(self, usuario):
        """Obtem uma tarefa para uma campanha ativa.
Retorna nulo para campanhas com tarefas completas.
Cria um job de tarefa para um usuário caso ele não exista. """
        trabalho_ativo = Trabalho.objects.filter(
            tarefas__campanha__id=self.id,
            username=usuario).first()
        if not trabalho_ativo:

            # Caso não tenha trabalho ativo,
            # cria um set de trabalho automaticamente
            ids_tarefas = self.tarefa_set.values_list('id', flat=True)
            tarefas_trabalho = train_test_split(
                list(ids_tarefas),
                test_size=self.tarefas_por_trabalho)[1]

            tarefas = Tarefa.objects.filter(id__in=tarefas_trabalho)

            trabalho_ativo = Trabalho(
                username=usuario
            )
            trabalho_ativo.save()
            trabalho_ativo.tarefas.set(tarefas)

        ids_tarefas_realizadas = trabalho_ativo.tarefas.filter(
            resposta__username=usuario).values_list('id', flat=True)

        return trabalho_ativo.tarefas.exclude(
            id__in=ids_tarefas_realizadas).first()

    def __str__(self):
        return self.nome


class Formulario(models.Model):
    """
<pre>nome: "Nome do Formulário"
campos:
    - escolha:
        nome: "nomeprogramatico"
        label: "Label do Campo"
        cardinalidade: ("multipla"|"unica")
        tipo: ("boolean"|"int"|"string")
        opcoes:
            - "label1"
            - "label2"
            - "label3"
        valores:
            - "val1"
            - "val2"
            - "val3"
    - check:
        nome: "outronomeprogramatico"
        label: "Outro Label do Campo"
        default: false</pre>
    """
    nome = models.CharField(max_length=50, unique=True)
    estrutura = YAMLField(help_text=__doc__)

    def __str__(self):
        return self.nome


class Tarefa(models.Model):
    "Conteúdo a ser classificado"
    texto_original = models.TextField()
    texto_inteligencia = models.TextField()
    classificacao = models.CharField(max_length=500)
    campanha = models.ForeignKey('Campanha', on_delete=models.DO_NOTHING)

    def votar(self, username, respostas):
        "computa mais um voto para o usuario nesta tarefa"

        for resposta_informada in respostas:
            resposta = Resposta()
            resposta.username = username
            resposta.tarefa = self
            resposta.nome_campo = resposta_informada['nomecampo']
            resposta.valor = resposta_informada['resposta']
            resposta.save()


class Trabalho(models.Model):
    "Grupo de tarefas por campanha alocadas para um usuário classificar"
    tarefas = models.ManyToManyField('Tarefa')
    username = models.TextField(max_length=255)


class Resposta(models.Model):
    "Registro de resposta do usuário para uma tarefa"
    tarefa = models.ForeignKey('Tarefa', on_delete=models.DO_NOTHING)
    username = models.TextField(max_length=255)
    nome_campo = models.CharField(max_length=255)
    valor = models.CharField(max_length=50)
