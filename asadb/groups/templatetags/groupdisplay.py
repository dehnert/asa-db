from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(needs_autoescape=True)
def format_constitution_link(url, autoescape=None):
    if autoescape:
        esc = conditional_escape
    else:
        esc = lambda x: x

    if url:
        text = esc(url)
    else:
        text = mark_safe("<em>not provided</em>")

    link = None
    if url.startswith("http://") or url.startswith("https://"):
        link = esc(url)

    if link:
        return mark_safe("<a href='%s'>%s</a>" % (link, text, ))
    else:
        return text
