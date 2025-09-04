"""
Custom template tags for the becas_sntsa app.
"""
from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """
    A template filter to add a CSS class to a form field.

    Args:
        field (Field): The form field.
        css_class (str): The CSS class to add.

    Returns:
        Widget: The field's widget with the added CSS class.
    """
    return field.as_widget(attrs={"class": css_class})