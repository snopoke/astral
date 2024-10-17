from django import template
from django.template.defaultfilters import stringfilter
from django_cotton.templatetags import DynamicAttr

register = template.Library()

EMPTY = object()


@register.simple_tag(takes_context=True)
def define(context, val, name=None, append=None, if_=EMPTY):
    if if_ is not EMPTY and if_ != "empty__" and not if_:
        return ""

    if append and name in context:
        out = context.get(name)
        if not isinstance(append, bool):
            out += append
        val = out + str(val)

    if name:
        context[name] = val
        return ""

    return val


@register.simple_tag(takes_context=True)
def define_eval(context, val):
    val = str(val)
    return DynamicAttr(val).resolve(context)


@register.filter(is_safe=True)
@stringfilter
def append_class(value, arg):
    if not arg:
        return value
    if not value:
        return arg

    return f"{value} {arg}"


@register.filter
@stringfilter
def build_class_map(value, prefix):
    classes = value.split(" ")
    return {class_.removeprefix(f"{prefix}-"): class_ for class_ in classes}
