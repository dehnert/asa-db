from django.forms.widgets import Widget, HiddenInput
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

class StaticWidget(Widget):
    """Widget that just displays and supplies a specific value.

    Useful for "freezing" form fields --- displaying them, but not
    allowing editing.
    """

    def __init__(self, *args, **kwargs):
        self.value = kwargs['value']
        del kwargs['value']
        super(StaticWidget, self).__init__(*args, **kwargs)
        self.inner = HiddenInput()

    def value_from_datadict(self, data, files, name, ):
        return self.value

    def render(self, name, value, attrs=None, ):
        if value is None:
            value = ''
        # We have this inner hidden widget because that allows us to nicely
        # handle a transition from StaticWidget to another widget type
        # (e.g., the user loads a form while unauthenticated and submits while
        # authenticated)
        hidden_render = self.inner.render(name, value, attrs=attrs)
        return mark_safe(conditional_escape(value) + hidden_render)
