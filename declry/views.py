from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory, modelform_factory
from django.forms.widgets import HiddenInput
from django.shortcuts import get_object_or_404
from vanilla import FormView
from django.utils.translation import ugettext_lazy as _
from scholradmin.forms import BootstrapModelForm
from django import http
from django.utils.decorators import classonlymethod
from django.template import (RequestContext,
                             loader, TemplateDoesNotExist)
import autocomplete_light
from django.views.decorators.csrf import requires_csrf_token
import logging
import smtplib
from email.mime.text import MIMEText
__author__ = 'jorgeramos'

class ModelFormView(FormView):
    model = None
    related_model = None
    success_url_path = '{}_{}_view'
    success_url_args = ''
    template_name = "edit.html"
    title = _('Edit')
    form = BootstrapModelForm
    fields = None
    hidden_fields = []
    exclude = []
    formfield_callback = None
    instance = None

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super(ModelFormView, cls).as_view(**initkwargs)
        if hasattr(cls, 'title'):
            view.label = cls.title
        return view
        
    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """
        if self.form_class:
            return self.form_class
        elif self.related_model:
            widgets = autocomplete_light.get_widgets_dict(self.related_model)
            return modelform_factory(self.related_model, widgets = widgets, form = self.form, fields=self.fields, exclude =self.exclude, formfield_callback=self.get_formfield_callback())
        elif self.model:
            widgets = autocomplete_light.get_widgets_dict(self.model)
            return modelform_factory(self.model, widgets = widgets, form = self.form, fields=self.fields, exclude =self.exclude, formfield_callback=self.get_formfield_callback())

        msg = "'%s' must either define 'form_class' or define 'model' or override 'get_form_class()'"
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_form(self, data=None, files=None, **kwargs):
        """
        Given `data` and `files` QueryDicts, and optionally other named
        arguments, and returns a form.
        """
        cls = self.get_form_class()
        return cls(instance = self.get_modelform_instance(), data=data, files=files, **kwargs)

    def get(self, request, object_id=None, *args, **kwargs):
        self.request = request
        self.object_id = object_id
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def post(self, request, object_id=None):
        self.request = request
        self.object_id = object_id

        if 'go_back' in request.POST:
            return self.form_valid(None)

        form = self.get_form(data=request.POST, files=request.FILES)
        if form.is_valid():
            inst= form.save()
            if not self.object_id:
                self.object_id = inst.pk
            self.success_url = self.get_success_url()
            return self.form_valid(form)
        return self.form_invalid(form)

    def get_success_url(self):
        return reverse(self.success_url_path.format(self.model._meta.app_label, self.model._meta.module_name),
                           args=(self.object_id,)) + self.success_url_args

    def form_invalid(self, form, **kwargs):
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        kwargs['title'] = self.title
        kwargs['instance'] = self.get_instance()
        kwargs['view'] = self
        return kwargs
    
    def get_formfield_callback(self):
        def formfield_callback(f, **kwargs):
            field = f.formfield(**kwargs)
            if f.name in self.hidden_fields:
                field.widget = HiddenInput()
            return field
        return formfield_callback

    def get_instance(self):
        if self.instance:
            return self.instance
        if self.request and self.object_id:
            return get_object_or_404(self.model, pk=self.object_id)

    def get_modelform_instance(self):
        return self.get_instance()


class InlineFormView(FormView):
    model = None
    related_model = None
    form = BootstrapModelForm
    prefix = "inlineform"
    template_name = "inline_edit.html"
    title = None
    instance = None
    success_path = '{}_{}_view'
    success_path_args = ''
    fields = None
    extra = 1
    exclude = []
    formfield_callback = None

    @classonlymethod
    def as_view(cls, **initkwargs):
        view = super(InlineFormView,cls).as_view(**initkwargs)
        if hasattr(cls, 'title'):
            view.label = cls.title
        return view

    def get_form_class(self):
        """
        Returns the form class to use in this view.
        """
        if self.form_class:
            return self.form_class
        if self.model and self.related_model:
            return inlineformset_factory(self.model, self.related_model, form=self.form,  extra=self.extra, exclude = self.exclude,
                                         fields = self.fields, formfield_callback= self.get_formfield_callback())

        msg = "'%s' must either define 'form_class' or define 'model' and 'related_model' or override 'get_form_class()'"
        raise ImproperlyConfigured(msg % self.__class__.__name__)

    def get_form(self, data=None, files=None, **kwargs):
        """
        Given `data` and `files` QueryDicts, and optionally other named
        arguments, and returns a form.
        """
        cls = self.get_form_class()
        return cls(prefix = self.prefix, instance=self.get_instance(), data=data, files=files, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Takes a set of keyword arguments to use as the base context, and
        returns a context dictionary to use for the view, additionally adding
        in 'view'.
        """
        kwargs.update({
            'prefix' : self.prefix,
            'title': self.title,
            'instance' : self.get_instance()
        })
        kwargs['view'] = self
        return kwargs

    def get(self, request, object_id, *args, **kwargs):
        self.request = request
        self.object_id = object_id
        form = self.get_form()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def post(self, request, object_id):
        self.request = request
        self.object_id = object_id
        if 'add_{}'.format(self.prefix) in request.POST:
            return self.process_add_element()
        elif 'go_back' in request.POST:
            return self.form_valid(None)
        else:
            form = self.get_form(data = request.POST, files= request.FILES)
            if form.is_valid():
                with transaction.commit_on_success():
                    #try:
                    form.save()
                    #except:
                    #    transaction.rollback()

                return self.form_valid(form)
        return self.form_invalid(form)

    def process_add_element(self):
        post_copy = self.request.POST.copy()
        post_copy['{}-TOTAL_FORMS'.format(self.prefix)] = int(post_copy['{}-TOTAL_FORMS'.format(self.prefix)]) + 1
        form = self.get_form(data=post_copy, files=self.request.FILES)
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        if self.success_path is None:
            msg = "'%s' must define 'success_url' or override 'form_valid()'"
            raise ImproperlyConfigured(msg % self.__class__.__name__)
        else:
             return reverse(self.success_path.format(self.model._meta.app_label, self.model._meta.module_name),
                            args=(self.object_id,)) + self.success_path_args

    def get_instance(self):
        if self.instance:
            return self.instance
        if self.request and self.object_id:
            return get_object_or_404(self.model, pk=self.object_id)

    def get_formfield_callback(self):
        return self.formfield_callback

# This can be called when CsrfViewMiddleware.process_view has not run,
# therefore need @requires_csrf_token in case the template needs
# {% csrf_token %}.

session_logger = logging.getLogger('session')
@requires_csrf_token
def permission_denied(request, template_name='403.html'):
    """
    Permission denied (403) handler.

    Templates: :template:`403.html`
    Context: None

    If the template does not exist, an Http403 response containing the text
    "403 Forbidden" (as per RFC 2616) will be returned.
    """

    email_txt="""
    Erro 403 
    Path: {}
    Cookies: {}
    User: {}
    Roles: {}
    Bom trabalho
    A Equipa do Scholr
    """
    user = request.user if hasattr(request, 'user') else '?'
    roles = request.user.roles if hasattr(request, 'user') and hasattr(request.user,'roles') else '---'
    session_logger.error(u'{} with cookies {}, user: {}, roles: {}'.format(request.path, request.COOKIES, user, roles))
    email = email_txt.format(request.path, request.COOKIES, user, roles)


    server = smtplib.SMTP('smtp.gmail.com:587')
    server.ehlo()
    server.starttls()
    server.login('alexandrerua@institutonunalvres.pt', 'xolagut855')
    msg = MIMEText(email)
    msg['Subject'] = 'Scholr 403 Alert'
    msg['From'] = 'helpdesk@scholr.net'
    msg['To'] = 'helpdesk@scholr.net, jalpedrinharamos@gmail.com, alexandrerua@institutonunalvres.pt'
    server.sendmail('info@institutonunalvres.pt', ['helpdesk@scholr.net', 'jalpedrinharamos@gmail.com', 'alexandrerua@institutonunalvres.pt'], msg.as_string())

    server.quit()
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return http.HttpResponseForbidden('<h1>403 TESTE</h1>')
    return http.HttpResponseForbidden(template.render(RequestContext(request)))
