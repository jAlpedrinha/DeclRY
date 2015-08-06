from collections import OrderedDict
from django import forms
from django.db import transaction, router
from django.contrib import admin
from django.contrib.admin.options import IncorrectLookupParameters
from django.contrib.admin.util import quote,unquote
from django.contrib.admin.templatetags.admin_static import static
from django.core.urlresolvers import reverse
from django.contrib.admin import helpers
from django.contrib.admin.views.main import ORDER_VAR
from django.core.exceptions import PermissionDenied
from django.forms import Media
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext_lazy as _, ungettext
from django.utils.encoding import force_text
from django.utils.text import capfirst
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.utils.html import escape
from functools import update_wrapper
import logging

from scholradmin.detail_view import DetailView, ResumeView
from scholradmin.forms import BootstrapModelForm
from scholradmin.util import get_deleted_objects, get_object_or_none
csrf_protect_m = method_decorator(csrf_protect)

session_logger = logging.getLogger('session')

CONTEXT_PARAM = 'con'
class Application(admin.ModelAdmin):
    edit_url_name = ""
    form = BootstrapModelForm
    hidden_fields = None
    allow_add = True
    view_tabs = ()
    detail_tabs = ()
    current_page = None
    list_per_page = 25

    def get_urls(self):
        from django.conf.urls import patterns, url

        def wrap_permissions(key, view):
            view = wrap(view)
            def wrapper(request, *args, **kwargs):
                obj = None
                if args:
                    obj = self.get_object(request, unquote(args[0]))
                if self.has_permission(request,key,obj):
                    return view(request, *args, **kwargs)
                else:
                    if args:
                        session_logger.error(u'no permission {} - {} - {} - {} - {}'.format(request.path, request.COOKIES,key,obj, args))
                    else:
                        session_logger.error(u'no permission {} - {} - {} - {} '.format(request.path, request.COOKIES,key,obj))
                    raise PermissionDenied
            return update_wrapper(wrapper,view)

        def wrap(view):
            def wrapper(request, *args, **kwargs):
                if CONTEXT_PARAM in request.GET:
                    self.current_page = request.GET[CONTEXT_PARAM]
                if self.current_page:
                    request.session['active_page_id'] = self.current_page
                else:
                    request.session['active_page_id'] = None
                request.session['active_page_model'] = self.model.__name__
                return self.admin_site.admin_view(view)(request, *args, **kwargs)

            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.module_name

        url_tupple = ('',)
        url_name_mask = '{}_{}_{}'
        for key,value in self.get_instance_views().items():
            applable, module_name = self.model._meta.app_label, self.model._meta.module_name
            url_tupple = url_tupple + (url(r'^(.+)/{0}$'.format(key),wrap_permissions(key, value),
                                           name=url_name_mask.format(self.model._meta.app_label, self.model._meta.module_name,key)),)

        for key,value in self.get_model_views().items():
            url_tupple = url_tupple + (url(r'^{0}/$'.format(key), wrap_permissions(key, value),
                                           name = url_name_mask.format(self.model._meta.app_label, self.model._meta.module_name, key)),)

        url_tupple = url_tupple + (
        url(r'^add/$',
            wrap(self.add_view),
            name='%s_%s_add' % info),
        url(r'^(.+)/history/$',
            wrap(self.history_view),
            name='%s_%s_history' % info),
        url(r'^(.+)/delete/$',
            wrap(self.delete_view),
            name='%s_%s_delete' % info),
        url(r'^(.+)/$',
            wrap(self.view),
            name='%s_%s_view' % info),
        url(r'^(.+)/detail$',
            wrap(self.detail_view),
            name='%s_%s_detail_view' % info),
        url(r'^(.+)/edit$',
            wrap(self.change_view),
            name='%s_%s_edit' % info),
        url(r'^$',
            wrap(self.changelist_view),
            name='%s_%s_changelist' % info),)

        urlpatterns = patterns(*url_tupple)

        return urlpatterns

    def queryset(self,request):
        manager = self.model._default_manager
        qs = manager.get_query_set()
        # TODO: this should be handled by some parameter to the ChangeList.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def filter_app_queryset(self, qs, request, app):
        return qs

    def get_instance_views(self):
        return {}

    def get_model_views(self):
        return {}

    def get_actions(self, request):
        actions = super(Application,self).get_actions(request)
        actions = OrderedDict([
            (key, value)
            for key,value in actions.iteritems()
            if self.has_action_permission(request, key)
        ])
        return actions
    def get_action(self, action):
        """
        Return a given action from a parameter, which can either be a callable,
        or the name of a method on the ModelAdmin.  Return is a tuple of
        (callable, name, description).
        """
        # If the action is a callable, just use it.
        if callable(action):
            func = action
            if hasattr(action, 'name'):
                action = action.name
            else:
                action = action.__name__

        # Next, look for a method. Grab it off self.__class__ to get an unbound
        # method instead of a bound one; this ensures that the calling
        # conventions are the same for functions and methods.
        elif hasattr(self.__class__, action):
            func = getattr(self.__class__, action)

        # Finally, look for a named method on the admin site
        else:
            try:
                func = self.admin_site.get_action(action)
            except KeyError:
                return None

        if hasattr(func, 'short_description'):
            description = func.short_description
        else:
            description = capfirst(action.replace('_', ' '))
        return func, action, description

    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(Application,self).formfield_for_dbfield(db_field,**kwargs)
        hidden_fields = self.hidden_fields or []
        if db_field.name in hidden_fields:
            formfield.widget = forms.HiddenInput()

        return formfield

    def get_extra_content(self,request):
        return {}


    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return MyViewList

    def get_tabbed_detail(self,request,instance):
        if self.detail_tabs and self.has_permission(request,'detail',instance):
            return DetailView(self.get_detail_tabs(request,instance),self,instance.pk)

    def get_view_tabs(self, request, instance):
        return self.view_tabs

    def get_detail_tabs(self, request, instance):
        return self.detail_tabs

    def view(self,request, object_id):
        instance = get_object_or_404(self.model, pk = object_id)
        view_tabs = self.get_view_tabs(self, instance)
        if view_tabs and self.has_permission(request,'view',instance):
            resume = ResumeView(view_tabs,self,object_id)
            detail = self.get_tabbed_detail(request,instance)
            return resume.render(request, detail)
        else:
            raise PermissionDenied

    def detail_view(self,request, object_id):
        instance = get_object_or_404(self.model, pk = object_id)
        detail = self.get_tabbed_detail(request, instance)
        if detail:
            return detail.render(request)
        else:
            raise PermissionDenied

    @csrf_protect_m
    def changelist_view(self, request):
        """
        The 'change list' admin view for this model.
        """
        from django.contrib.admin.views.main import ERROR_FLAG
        opts = self.model._meta
        app_label = opts.app_label

        if not self.has_permission(request, 'view'):
            raise PermissionDenied

        list_display = self.get_list_display(request)
        list_display_links = self.get_list_display_links(request, list_display)
        list_filter = self.get_list_filter(request)

        # Check actions to see if any are available on this changelist
        actions = self.get_actions(request)
        if actions:
            # Add the action checkboxes if there are any actions available.
            list_display = ['action_checkbox'] +  list(list_display)
        ChangeList = self.get_changelist(request)
        try:
            cl = ChangeList(request, self.model, list_display,
                            list_display_links, list_filter, self.date_hierarchy,
                            self.search_fields, self.list_select_related,
                            self.list_per_page, self.list_max_show_all, self.list_editable,
                            self)
        except IncorrectLookupParameters:
            # Wacky lookup parameters were given, so redirect to the main
            # changelist page, without parameters, and pass an 'invalid=1'
            # parameter via the query string. If wacky parameters were given
            # and the 'invalid=1' parameter was already in the query string,
            # something is screwed up with the database, so display an error
            # page.
            if ERROR_FLAG in request.GET.keys():
                return SimpleTemplateResponse('admin/invalid_setup.html', {
                'title': _('Database error'),
                })
            return HttpResponseRedirect(request.path + '?' + ERROR_FLAG + '=1')

        # If the request was POSTed, this might be a bulk action or a bulk
        # edit. Try to look up an action or confirmation first, but if this
        # isn't an action the POST will fall through to the bulk edit check,
        # below.
        action_failed = False
        selected = request.POST.getlist(helpers.ACTION_CHECKBOX_NAME)
        # Actions with no confirmation
        if (actions and request.method == 'POST' and
                    'index' in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_query_set(request))
                if response:
                    return response
                else:
                    action_failed = True
            else:
                msg = _("Items must be selected in order to perform "
                        "actions on them. No items have been changed.")
                self.message_user(request, msg)
                action_failed = True

        # Actions with confirmation
        if (actions and request.method == 'POST' and
                    helpers.ACTION_CHECKBOX_NAME in request.POST and
                    'index' not in request.POST and '_save' not in request.POST):
            if selected:
                response = self.response_action(request, queryset=cl.get_query_set(request))
                if response:
                    return response
                else:
                    action_failed = True

        # If we're allowing changelist editing, we need to construct a formset
        # for the changelist given all the fields to be edited. Then we'll
        # use the formset to validate/process POSTed data.
        formset = cl.formset = None

        # Handle POSTed bulk-edit data.
        if (request.method == "POST" and cl.list_editable and
                    '_save' in request.POST and not action_failed):
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(request.POST, request.FILES, queryset=cl.result_list)
            if formset.is_valid():
                changecount = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = self.save_form(request, form, change=True)
                        self.save_model(request, obj, form, change=True)
                        self.save_related(request, form, formsets=[], change=True)
                        change_msg = self.construct_change_message(request, form, None)
                        self.log_change(request, obj, change_msg)
                        changecount += 1

                if changecount:
                    if changecount == 1:
                        name = force_text(opts.verbose_name)
                    else:
                        name = force_text(opts.verbose_name_plural)
                    msg = ungettext("%(count)s %(name)s was changed successfully.",
                                    "%(count)s %(name)s were changed successfully.",
                                    changecount) % {'count': changecount,
                                                    'name': name,
                                                    'obj': force_text(obj)}
                    self.message_user(request, msg)

                return HttpResponseRedirect(request.get_full_path())

        # Handle GET -- construct a formset for display.
        elif cl.list_editable:
            FormSet = self.get_changelist_formset(request)
            formset = cl.formset = FormSet(queryset=cl.result_list)

        # Build the list of media to be used by the formset.
        if formset:
            media = self.media + formset.media
        else:
            media = self.media
        # Build the action form and populate it with available actions.
        if actions:
            action_form = self.action_form(auto_id=None)
            action_form.fields['action'].choices = self.get_action_choices(request)
        else:
            action_form = None

        selection_note_all = ungettext('%(total_count)s selected',
                                       'All %(total_count)s selected', cl.result_count)

        _active_filters= False
        for filter_spec in cl.filter_specs:
            if filter_spec.used_parameters and filter_spec.template:
                _active_filters = True
                continue

        context = {
            'module_name': force_text(opts.verbose_name_plural),
            'selection_note': _('0 of %(cnt)s selected') % {'cnt': len(cl.result_list)},
            'selection_note_all': selection_note_all % {'total_count': cl.result_count},
            'title': cl.title,
            'is_popup': cl.is_popup,
            'cl': cl,
            'media': media,
            'has_add_permission': self.has_permission(request,'add') and self.allow_add,
            'app_label': app_label,
            'action_form': action_form,
            'actions_on_top': self.actions_on_top,
            'actions_on_bottom': self.actions_on_bottom,
            'actions_selection_counter': self.actions_selection_counter,
            'active_filters' : _active_filters,
        }

        return TemplateResponse(request, self.change_list_template or [
            '%s/%s/view_list.html' % (app_label, opts.object_name.lower()),
            '%s/view_list.html' % app_label,
            'admin/view_list.html'
        ], context, current_app=self.admin_site.name)

    @csrf_protect_m
    @transaction.commit_on_success
    def delete_view(self, request, object_id):
        "The 'delete' admin view for this model."
        opts = self.model._meta
        app_label = opts.app_label

        obj = self.get_object(request, unquote(object_id))
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_text(opts.verbose_name), 'key': escape(object_id)})

        using = router.db_for_write(self.model)
        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        (deleted_objects, perms_needed, protected) = get_deleted_objects(
            [obj], opts, request.user, self.admin_site, using)

        if request.POST: # The user has already confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = force_text(obj)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            self.message_user(request, _('The %(name)s "%(obj)s" was deleted successfully.') % {'name': force_text(opts.verbose_name), 'obj': force_text(obj_display)})

            if not self.has_permission(request, 'delete', obj):
                return HttpResponseRedirect(reverse('index',
                                                    current_app=self.admin_site.name))
            return HttpResponseRedirect(reverse('%s_%s_changelist' %
                                                (opts.app_label, opts.module_name),
                                                current_app=self.admin_site.name))

        object_name = force_text(opts.verbose_name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": object_name}
        else:
            title = _("Are you sure?")

        context = {
        "title": title,
        "object_name": object_name,
        "object": obj,
        "deleted_objects": deleted_objects,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "app_label": app_label,
        }

        return TemplateResponse(request, self.delete_confirmation_template or [
            "admin/%s/%s/delete_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context, current_app=self.admin_site.name)


    def get_object(self, request, object_id):
        """
        Returns an instance matching the primary key provided. ``None``  is
        returned if no match is found (or the object_id failed validation
        against the primary key field).
        """
        queryset = self.queryset(request)
        model = queryset.model
        try:
            object_id = model._meta.pk.to_python(object_id)
            return get_object_or_none(model, pk=object_id)
        except:
            return None

    def has_add_permission(self,request):
        return self.has_permission(request,'add')

    def has_change_permission(self,request, obj):
        return self.has_permission(request,'edit', obj)

    def has_delete_permission(self,request, obj):
        return self.has_permission(request,'delete', obj)

    def has_action_permission(self, request, action):
        return self.has_permission(request, 'change_list_{}'.format(action))

    def has_permission(self, request, perm, obj=None):
        opts = self.model._meta
        app_label = opts.app_label
        return request.user.has_perm('{}_{}_{}'.format(app_label, opts.module_name, perm), obj)
    
    @property
    def media(self):
        js = []
        if self.actions is not None:
            js.append('core_actions.js')
        return Media(js=[static('admin/js/%s' % url) for url in js])



from django.contrib.admin.views.main import ChangeList, IGNORED_PARAMS
from django.contrib.admin.views import main
from django.utils.encoding import force_str
main.IGNORED_PARAMS = main.IGNORED_PARAMS + (CONTEXT_PARAM,)
class MyViewList(ChangeList):
    def __init__(self, request, *args, **kwargs):
        super(MyViewList, self).__init__(request,*args,**kwargs)
        self.params.pop(CONTEXT_PARAM, None)

    def url_for_result(self, result):
        pk = getattr(result, self.pk_attname)
        return reverse('%s_%s_view' % (self.opts.app_label,
                                       self.opts.module_name),
                       args=(quote(pk),),
                       current_app=self.model_admin.admin_site.name)

    def get_ordering(self, request, queryset):
        """ This is the function that will be overriden so the admin_order_fields can be used as lists of fields instead of just one field """
        params = self.params
        ordering = list(self.model_admin.get_ordering(request) or self._get_default_ordering())
        if ORDER_VAR in params:
            ordering = []
            order_params = params[ORDER_VAR].split('.')
            for p in order_params:
                try:
                    none, pfx, idx = p.rpartition('-')
                    field_name = self.list_display[int(idx)]
                    order_field = self.get_ordering_field(field_name)
                    if not order_field:
                        continue
                    # Here's where all the magic is done: the new method can accept either a list of strings (fields) or a simple string (a single field)
                    if isinstance(order_field, list):
                        for field in order_field:
                            ordering.append(pfx + field)
                    else:
                        ordering.append(pfx + order_field)
                except (IndexError, ValueError):
                    continue
        ordering.extend(queryset.query.order_by)
        pk_name = self.lookup_opts.pk.name
        if not (set(ordering) & set(['pk', '-pk', pk_name, '-' + pk_name])):
            ordering.append('pk')
        return ordering
