from django import template
from django.core.urlresolvers import reverse
import django

register = template.Library()

@register.filter
def format_categories(fysm, year):
    print year
    snippets = ["<a href='%s'>%s</a>" % (
        reverse('fysm', args=[year, tag.slug, ]),
        tag,
    ) for tag in fysm.tags.all()]
    # Mark this as safe. This assumes that the tags are safe...
    return django.utils.safestring.mark_safe(", ".join(snippets))
