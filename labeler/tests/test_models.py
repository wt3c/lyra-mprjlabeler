from django.test import TestCase

from model_mommy.mommy import generators, make


# Adiciona Field nao suportado pela biblioteca model_mommy
generators.add('yamlfield.fields.YAMLField', lambda: None)


class Completude(TestCase):
    def test_completude_geral_da_campanha_uma_resposta(self):
        """
            Calcula o volume de tarefas ja respondidas por todos os usuarios.
        """
        campanha = make('labeler.Campanha')
        tarefas = make('labeler.Tarefa', _quantity=10, campanha=campanha)
        trabalhos = make('labeler.Trabalho', _quantity=5, tarefas=tarefas)

        # Uma Resposta
        make('labeler.Resposta', tarefa=tarefas[0], trabalho=trabalhos[0])

        completude_geral = campanha.obter_completude_geral()

        self.assertEqual(completude_geral, 1)

    def test_completude_geral_da_campanha_multiplas_respostas(self):
        """
            Calcula o volume de tarefas ja respondidas por todos os usuarios.
        """
        campanha = make('labeler.Campanha')
        tarefas = make('labeler.Tarefa', _quantity=10, campanha=campanha)
        trabalhos = make('labeler.Trabalho', _quantity=5, tarefas=tarefas)

        # Tres Respostas
        make('labeler.Resposta', tarefa=tarefas[0], trabalho=trabalhos[0])
        make('labeler.Resposta', tarefa=tarefas[1], trabalho=trabalhos[1])
        make('labeler.Resposta', tarefa=tarefas[2], trabalho=trabalhos[2])

        completude_geral = campanha.obter_completude_geral()

        self.assertEqual(completude_geral, 3)
