import autocomplete_light
from django.contrib.admin import helpers
from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import modelform_factory
from django.forms.widgets import HiddenInput
from django.utils.decorators import classonlymethod
from django.utils.translation import ugettext_lazy as _
from vanilla import FormView, GenericView

from .forms import BootstrapModelForm

class FormActionView(FormView):
    model = None
    name = "action"
    related_model = None
    template_name = "list_action_form.html"
    form = BootstrapModelForm
    fields = []
    hidden_fields = []
    exclude = []
    formfield_callback = None
    short_description = _('Edit')

    @classonlymethod
    def as_view(cls, **initkwargs):
        def view(modeladmin, request, queryset, *args, **kwargs):
            self = cls(**initkwargs)
            self.request = request
            self.modeladmin = modeladmin
            self.queryset = queryset
            self.args = args
            self.kwargs = kwargs
            return self.dispatch(modeladmin, request, queryset, *args, **kwargs)
        view.short_description = cls.short_description
        view.name = cls.name
        return view
     
    def dispatch(self, modeladmin, request, queryset, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method != 'POST':
            return None
        else:
            if self.has_queryset_errors():
                return self.validation_error()
            if 'submission' in request.POST:
                handler = self.submission
            else:
                handler = self.confirmation
        return handler(modeladmin, request, queryset, *args, **kwargs)
    
    def submission(self, modeladmin, request, queryset):
        self.form = self.get_form(data=request.POST, files=request.FILES)
        if self.form.is_valid():
            for instance in queryset:
                self.apply(instance)
        return None
    
    def confirmation(self, modeladmin, request, queryset):
        self.request = request
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)
    
    def apply(self, instance):
        for field in self.fields:
            setattr(instance, field, self.form.cleaned_data[field])
        instance.save()

    def has_queryset_errors(self):
        self.errors = []
        for instance in self.queryset:
            if not self.modeladmin.has_permission(self.request, self.name, instance):
                self.errors.append(_(u'Permission denied on {0} to apply action {1}').format(instance, self.name))
        return False
    
    def validation_error(self):
        errors = self.errors if hasattr(self,'errors') else [_('Error performing action')]
        for error in errors:
            self.modeladmin.message_user(self.request, error, level = messages.ERROR)
        return None

    def get_formfield_callback(self):
        def formfield_callback(f, **kwargs):
            field = f.formfield(**kwargs)
            if f.name in self.hidden_fields:
                field.widget = HiddenInput()
            return field
        return formfield_callback

    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """
        if self.form_class:
            return self.form_class
        elif self.model:
            widgets = autocomplete_light.get_widgets_dict(self.model)
            return modelform_factory(self.model, widgets = widgets, form = self.form, fields=self.fields, exclude =self.exclude, formfield_callback=self.get_formfield_callback())

        msg = "'%s' must either define 'form_class' or define 'model' or override 'get_form_class()'"
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def form_valid(self, form):
        return None

    def get_context_data(self, **kwargs):
        kwargs['title'] = self.short_description
        kwargs['instances'] = self.queryset
        kwargs['view'] = self
        kwargs['action_checkbox_name'] = helpers.ACTION_CHECKBOX_NAME
        kwargs['action'] = self.name
        return kwargs


class ActionConfirmationView(GenericView):
    name= "action"
    text= u'Apply {} to the following objects ?'
    short_description = _('Action')
    template_name = 'confirm_action.html'

    @classonlymethod
    def as_view(cls, **initkwargs):
        def view(modeladmin, request, queryset, *args, **kwargs):
            self = cls(**initkwargs)
            self.request = request
            self.modeladmin = modeladmin
            self.queryset = queryset
            self.args = args
            self.kwargs = kwargs
            return self.dispatch(modeladmin, request, queryset, *args, **kwargs)
        view.short_description = cls.short_description
        view.name = cls.name
        return view
     
    def dispatch(self, modeladmin, request, queryset, *args, **kwargs):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if request.method != 'POST':
            return None
        else:
            if self.has_queryset_errors():
                return self.validation_error()
            if 'submission' in request.POST:
                handler = self.submission
            else:
                handler = self.confirmation
        return handler(modeladmin, request, queryset, *args, **kwargs)
    
    def submission(self, modeladmin, request, queryset):
        if self.request.POST.get('ok',False):
            self.modeladmin.message_user(self.request,_('Action {} applied').format(self.short_description))
            for instance in queryset:
                self.apply(instance)
        return None
    
    def confirmation(self, modeladmin, request, queryset):
        self.request = request
        context = self.get_context_data()
        return self.render_to_response(context)
    
    def apply(self, instance):
        pass

    def has_queryset_errors(self):
        return False
    
    def validation_error(self):
        errors = self.errors if hasattr(self,'errors') else [_('Error performing action')]
        for error in errors:
            self.modeladmin.message_user(self.request, error, level = messages.ERROR)
        return None


    def get_context_data(self, **kwargs):
        kwargs['title'] = self.short_description
        kwargs['instances'] = self.queryset
        kwargs['view'] = self
        kwargs['action_checkbox_name'] = helpers.ACTION_CHECKBOX_NAME
        kwargs['action'] = self.name
        kwargs['text'] = self.text.format(self.short_description)
        return kwargs
