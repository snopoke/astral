from django import template
from django.template.base import token_kwargs
from django.template.defaultfilters import stringfilter
from django_cotton.templatetags import DynamicAttr

register = template.Library()

EMPTY = object()


class DefineVarNode(template.Node):
    def __init__(self, val, if_, target_var):
        self.val = val
        self.target_var = target_var
        self.if_ = if_

    def render(self, context):
        if self.if_ is not EMPTY and not self.if_.resolve(context):
            return ""

        context[self.target_var] = self.val.resolve(context)
        return ""


def define_var(parser, token):
    """
    {% define "value" as var %}
    {% define "value" if_=maybe_true as var %}
    """
    bits = token.split_contents()[1:]
    if len(bits) >= 2 and bits[-2] == "as":
        target_var = bits[-1]
        bits = bits[:-2]
    else:
        raise template.TemplateSyntaxError(
            "'define' must be assigned to a variable using the 'as' keyword"
        )

    if len(bits) == 1:
        val = bits[0]
        if_ = EMPTY
    else:
        try:
            val, if_ = bits
        except ValueError:
            raise template.TemplateSyntaxError(
                "'define' tag requires a value and an optional condition"
            )
        if_ = token_kwargs([if_], parser)["if_"]
    return DefineVarNode(parser.compile_filter(val), if_, target_var)


register.tag("define", define_var)


@register.simple_tag(takes_context=True)
def define_eval(context, val):
    val = str(val)
    return DynamicAttr(val).resolve(context)


@register.simple_tag
def join_vars(*args, separator=" "):
    return separator.join(filter(None, args))


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
