from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    return mapping.get(key) if mapping else None


@register.filter
def fmt_marks(value):
    """Show 7.0 as 7 and 7.5 as 7.5; blank for None."""
    if value is None or value == "":
        return ""
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, float):
        return f"{value:g}"
    return value


@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    """Current query string with some keys replaced (used for pagination/filter links)."""
    params = context["request"].GET.copy()
    for k, v in kwargs.items():
        if v in (None, ""):
            params.pop(k, None)
        else:
            params[k] = v
    return params.urlencode()


@register.filter
def tone(obj):
    """Stable 0-5 colour index for avatars."""
    return (getattr(obj, "pk", None) or 0) % 6


@register.filter
def is_checkbox(field):
    return field.field.widget.__class__.__name__ == "CheckboxInput"


@register.filter
def pct(part, whole):
    try:
        return round(float(part) * 100 / float(whole)) if float(whole) else 0
    except (TypeError, ValueError):
        return 0


@register.filter
def is_member_of(project, user):
    return project.is_member(user)


@register.filter
def can_private(project, user):
    return project.can_view_private(user)
