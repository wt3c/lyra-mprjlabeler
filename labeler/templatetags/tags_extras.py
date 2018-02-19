"Template tags e helpers de tela"
from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def completude(context, campanha, username):
    """Obtém o valor de completude de uma campanha e
    armazena na variável de template "porcentagem" """
    context['porcentagem'] = campanha.completude(username)
    return ''
