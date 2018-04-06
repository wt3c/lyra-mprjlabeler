"Template tags e helpers de tela"
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def completude(context, campanha, username):
    """Obtém o valor de completude de uma campanha e
    armazena na variável de template "porcentagem" """
    context['porcentagem'] = campanha.completude(username)
    return ''


@register.simple_tag(takes_context=True)
def completude_geral(context, campanha):
    context['completude_geral_campanha'] = campanha.obter_completude_geral()
    return ''


@register.simple_tag(takes_context=True)
def completude_dos_trabalhos(context, campanha, nome_usuario):
    trabalhos = campanha.obter_todos_trabalhos(nome_usuario)
    if not trabalhos:
        context['porcentagens_trabalhos'] = [0]
        return ''

    context['porcentagens_trabalhos'] = [
	trabalho.obter_completude() for trabalho in trabalhos
    ]
    return ''
