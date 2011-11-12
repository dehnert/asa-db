from django.forms.widgets import Widget, Select, HiddenInput
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from itertools import chain

class StaticWidget(Widget):
    """Widget that just displays and supplies a specific value.

    Useful for "freezing" form fields --- displaying them, but not
    allowing editing.
    """

    def __init__(self, *args, **kwargs):
        self.value = kwargs['value']
        del kwargs['value']
        if 'choices' in kwargs:
            if kwargs['choices'] is not None:
                self.choices = kwargs['choices']
            else:
                self.choices = ()
            del kwargs['choices']
        else:
            self.choices = ()
        super(StaticWidget, self).__init__(*args, **kwargs)
        self.inner = HiddenInput()

    def value_from_datadict(self, data, files, name, ):
        for choice_value, choice_label in self.choices:
            if choice_label == unicode(self.value):
                return choice_value
        return self.value

    def render(self, name, value, attrs=None, choices=(), ):
        if value is None:
            value = ''
        label = value
        the_choices = chain(self.choices, choices)
        for choice_value, choice_label in the_choices:
            if choice_value == value:
                label = choice_label
        # We have this inner hidden widget because that allows us to nicely
        # handle a transition from StaticWidget to another widget type
        # (e.g., the user loads a form while unauthenticated and submits while
        # authenticated)
        hidden_render = self.inner.render(name, value, attrs=attrs)
        return mark_safe(conditional_escape(label) + hidden_render)

    @classmethod
    def replace_widget(cls, formfield, value):
        choices = None
        choices = getattr(formfield.widget, 'choices', ())
        formfield.widget = cls(value=value, choices=choices)
