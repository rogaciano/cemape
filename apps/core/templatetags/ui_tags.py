from django import template

register = template.Library()


@register.inclusion_tag('components/form_field.html')
def form_field(field, label=None, help_text=None):
    return {
        'field': field,
        'label': label or field.label,
        'help_text': help_text or field.help_text,
    }


@register.inclusion_tag('components/badge.html')
def status_badge(status):
    colors = {
        'AGUARDANDO': 'bg-yellow-100 text-yellow-800',
        'EM_ANDAMENTO': 'bg-blue-100 text-blue-800',
        'SUSPENSO': 'bg-orange-100 text-orange-800',
        'ENCERRADO': 'bg-green-100 text-green-800',
        'EXTINTO': 'bg-red-100 text-red-800',
    }
    labels = {
        'AGUARDANDO': 'Aguardando',
        'EM_ANDAMENTO': 'Em Andamento',
        'SUSPENSO': 'Suspenso',
        'ENCERRADO': 'Encerrado',
        'EXTINTO': 'Extinto',
    }
    return {
        'status': labels.get(status, status),
        'color': colors.get(status, 'bg-gray-100 text-gray-800'),
    }
