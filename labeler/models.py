"Domínio de Dados"
from django.db import models
from yamlfield.fields import YAMLField
import random


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
        trabalho = self.obter_trabalho(usuario)
        if not trabalho:
            return 0
        ids_tarefas = trabalho.tarefas.values_list('id', flat=True)
        ids_tarefas_respondidas = Resposta.objects.filter(
            tarefa__id__in=ids_tarefas,
            username=usuario,
            trabalho__id=trabalho.id).values_list('tarefa_id', flat=True)
        quantidade_tarefas_respondidas = self.tarefa_set.filter(
            id__in=ids_tarefas_respondidas).count()

        return quantidade_tarefas_respondidas

    def completude(self, usuario):
        """Retorna o nível de completude desta campanha por usuário"""

        return int(
            (self._quantidade_tarefas_respondidas(usuario)*100)
            / self.tarefas_por_trabalho)

    def obter_completude_geral(self):
        total_tarefas = Tarefa.objects.all().distinct().count()
        numero_respostas = self.tarefa_set.filter(
            resposta__isnull=False).distinct().count()
        return round(numero_respostas / total_tarefas * 100, 2)

    def obter_trabalho(self, usuario):
        """Obtém o último trabalho de respostas do usuário"""
        return Trabalho.objects.filter(
            tarefas__campanha__id=self.id,
            username=usuario).order_by('-id').first()

    def obter_todos_trabalhos(self, nome_usuario):
        return self.trabalho_set.filter(username=nome_usuario)

    def _obter_tarefas_alocaveis(self):
        ids_tarefas = [id for id in self.tarefa_set.values_list(
                'id', flat=True)]
        random.shuffle(ids_tarefas)
        tarefas_trabalho = ids_tarefas[:self.tarefas_por_trabalho]

        return Tarefa.objects.filter(id__in=tarefas_trabalho)

    def obter_tarefa(self, usuario, gerar_novo_trabalho=False):
        """Obtem uma tarefa para uma campanha ativa.
Retorna nulo para campanhas com tarefas completas.
Cria um job de tarefa para um usuário caso ele não exista. """
        trabalho_ativo = self.obter_trabalho(usuario)

        # se a situacao do trabalho for inativa não retorna tarefa nenhuma
        if (trabalho_ativo and
                trabalho_ativo.situacao == 'F' and
                not gerar_novo_trabalho):
            return None

        # se a situacao do trabalho for inativa e ousuário quiser
        # alocar mais um grupo de trabalho, permite
        if (trabalho_ativo and
                trabalho_ativo.situacao == 'F' and
                gerar_novo_trabalho):
            trabalho_ativo = None

        if not trabalho_ativo:

            # Caso não tenha trabalho ativo,
            # cria um set de trabalho automaticamente

            tarefas = self._obter_tarefas_alocaveis()

            trabalho_ativo = Trabalho(
                username=usuario,
                campanha=self,
                situacao='A'
            )
            trabalho_ativo.save()
            trabalho_ativo.tarefas.set(tarefas)

        ids_tarefas_realizadas = trabalho_ativo.tarefas.filter(
            resposta__username=usuario,
            resposta__trabalho__id=trabalho_ativo.id).values_list(
                'id',
                flat=True)

        tarefa = trabalho_ativo.tarefas.exclude(
            id__in=ids_tarefas_realizadas).first()

        if trabalho_ativo.situacao == 'A' and not tarefa:
            trabalho_ativo.situacao = 'F'
            trabalho_ativo.save()

        return tarefa

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
        trabalho = self.campanha.obter_trabalho(username)

        # acrescenta a resposta
        for resposta_informada in respostas:
            resposta = Resposta()
            resposta.username = username
            resposta.tarefa = self
            resposta.trabalho = trabalho
            resposta.nome_campo = resposta_informada['nomecampo']
            resposta.valor = resposta_informada['resposta']
            resposta.save()

    @staticmethod
    def importar_tarefas(campanha, tarefas):
        'Importa uma lista de tarefas'
        for item in tarefas:
            tarefa = Tarefa()
            tarefa.campanha = campanha
            tarefa.texto_original = item['original']
            tarefa.texto_inteligencia = item['parseado']
            tarefa.save()


SITUACOES_TRABALHO = (
    ('A', 'Aberto'),
    ('F', 'Finalizado'),
)


class Trabalho(models.Model):
    "Grupo de tarefas por campanha alocadas para um usuário classificar"
    tarefas = models.ManyToManyField('Tarefa')
    campanha = models.ForeignKey('Campanha', on_delete=models.CASCADE)
    username = models.TextField(max_length=255)
    situacao = models.CharField(
        max_length=1,
        choices=SITUACOES_TRABALHO,
        default='A')

    def obter_completude(self):
        ids_tarefas = self.tarefas.values_list('id', flat=True)
        ids_tarefas_respondidas = Resposta.objects.filter(
            tarefa__id__in=ids_tarefas,
            username=self.username,
            trabalho__id=self.id).values_list('tarefa_id', flat=True)
        quantidade_tarefas_respondidas = self.tarefas.filter(
            id__in=ids_tarefas_respondidas).count()

        return int(quantidade_tarefas_respondidas /
                   self.campanha.tarefas_por_trabalho * 100)


class Resposta(models.Model):
    "Registro de resposta do usuário para uma tarefa"
    tarefa = models.ForeignKey('Tarefa', on_delete=models.DO_NOTHING)
    trabalho = models.ForeignKey('Trabalho', on_delete=models.CASCADE)
    username = models.TextField(max_length=255)
    nome_campo = models.CharField(max_length=255)
    valor = models.CharField(max_length=50)
