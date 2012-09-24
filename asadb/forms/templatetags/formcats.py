from django import template
from django.core.urlresolvers import reverse
import django

register = template.Library()

@register.filter
def format_categories(fysm, year):
    snippets = ["<a href='%s'>%s</a>" % (
        reverse('fysm', args=[year, category.slug, ]),
        category,
    ) for category in fysm.categories.all()]
    # Mark this as safe. This assumes that the categories are safe...
    return django.utils.safestring.mark_safe(", ".join(snippets))
