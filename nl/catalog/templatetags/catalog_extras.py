from django import template

register = template.Library()

@register.filter
def get_list(value, arg):
    """Получить список значений GET-параметра"""
    return value.getlist(arg)