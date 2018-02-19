from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def completude(context, campanha, username):
    context['porcentagem'] = campanha.completude(username)
    return ''