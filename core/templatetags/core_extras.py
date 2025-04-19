from django import template

register = template.Library()

@register.filter
def filter_by_course(progress_data, course_id):
    """
    Filter progress data by course ID.
    Usage: {{ progress_data|filter_by_course:course.id }}
    """
    if not progress_data:
        return None
    for progress in progress_data:
        if progress.course.id == course_id:
            return progress
    return None

@register.filter
def multiply(value, arg):
    """
    Multiply the value by the argument.
    Usage: {{ value|multiply:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """
    Divide the value by the argument.
    Usage: {{ value|divide:arg }}
    """
    try:
        arg = float(arg)
        if arg == 0:
            return 0
        return float(value) / arg
    except (ValueError, TypeError):
        return 0 