from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

class Widget(object):
    name = "widget"
    label = "Widget"
    template = "widget.html"
    color = None
    context_errors = _('No data')
    icon = "icon-user"

    def __init__(self, request):
        self.request = request

    def show_widget(self):
        return True

    def load_context(self):
        return {}

    def get_template(self):
        return self.template

    def __unicode__(self):
        context = self.load_context()
        if not context:
            context= {
                'error' : self.context_errors
            }
        context.update({
            'name' : self.label,
            'color' : self.color,
            'icon' : self.icon,
        })
        rendered = render_to_string(self.get_template(), context)
        return mark_safe(rendered)
