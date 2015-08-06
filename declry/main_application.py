from functools import update_wrapper
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.contrib.auth.forms import AuthenticationForm
from django.core.urlresolvers import reverse
from django.template.response import TemplateResponse
from django.views.decorators.cache import never_cache

from apps import Application


class Site(admin.AdminSite):
    login_template = "auth/login.html"
    logout_template = "auth/logout.html"
    login_form = AuthenticationForm
    widgets = ()
    menus = []

    def __init__(self, *args, **kwargs ):
        super(Site, self).__init__(*args, **kwargs)
        self._actions = {}

    def set_menu_items(self, request):
        if 'menu' not in request.session:
            menus = []
            self.menus = sorted(self.menus, key=lambda student: student[0])
            for index, Menu in self.menus:
                menus.extend(Menu.get_menus(request))
            request.session['menu'] = menus

    def get_menu_items(self, request):
        if 'menu' not in request.session:
            self.set_menu_items(request)
        return request.session['menu']

    def get_menu_item(self, request, name):
        try:
            return next(x for x in self.get_menu_items(request) if x.name == name)
        except StopIteration:
            raise PermissionDenied

    def has_perm(self,perms_dict, request):
        perm_name = perms_dict['perm']
        perm_obj = None
        if 'instance' in perms_dict:
            perm_obj = perms_dict['instance']
        return request.user.has_perm(perm_name, obj= perm_obj)

    def admin_view(self, view, cacheable = False):
        def inner(request, *args, **kwargs):
            if not self.has_permission(request):
                if request.path == reverse('logout',
                                           current_app=self.name):
                    index_path = reverse('index', current_app=self.name)
                    return HttpResponseRedirect(index_path)
                return self.login(request)
            return view(request, *args, **kwargs)
        if not cacheable:
            inner = never_cache(inner)
            # We add csrf_protect here so this function can be used as a utility
        # function for any view, without having to repeat 'csrf_protect'.
        if not getattr(view, 'csrf_exempt', False):
            inner = csrf_protect(inner)
        return update_wrapper(inner, view)

    @never_cache
    def index(self, request):
        """
        Displays the main admin index page, which lists all of the installed
        apps that have been registered in this site.
        """
        if hasattr(request, 'user') and not isinstance(request.user, AnonymousUser):
            app_name = self.get_menu_items(request)[0].name
            return self.app_index(request,app_name)
        else:
            return self.login(request)

    def register(self, model_or_iterable, admin_class=None, **options):
        if not admin_class:
            admin_class = Application
        return super(Site, self).register(model_or_iterable,admin_class, **options)

    def has_permission(self,request):
        from django.core.urlresolvers import resolve
        match = resolve(request.path)
        if match.url_name == "pedagogico_matricula_candidate":
            return True
        if isinstance(request.user, AnonymousUser) and hasattr(request.user, 'roles') and request.user.roles:
            return True
        return request.user.is_authenticated() and request.user.is_active

    def app_index(self, request, app_label):
        if request.user.has_module_perms(app_label):
            enabled= {}
            app = self.get_menu_item(request,app_label)
            request.session['app'] = app

            for Widget in app.widgets:
                widget = Widget(request)
                if widget.show_widget():
                    enabled[widget.name] = widget

            context = {
                'active_model': None,
                'widgets': enabled
            }

            return TemplateResponse(request, app.template or [
                '%s/app_index.html' % app_label,
                'app_index.html'
            ], context, current_app=self.name)
        else:
            raise PermissionDenied

