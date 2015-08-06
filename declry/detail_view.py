# _*_ encoding: utf-8  _*_
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse


class DetailView(object):
    def __init__(self, pages, app, object_id):
        self.pages = {}
        self.pages_order = []
        for Page in pages:
            page = Page(app)
            self.pages[page.name] = page
            self.pages_order.append(page)
        self.app = app
        self.obj = get_object_or_404(app.model, pk=object_id)

    def get_active_page(self, request):
        return self.pages[request.GET.get('page')]

    def update_page_data(self,active_page, request):
        active_page.load_context(self.obj, request)

    def get_pages(self,request):
        pages= []
        for page in self.pages_order:
            if page.include_page(request,self.obj) and self.has_detail_permission(request.user, page):
                pages.append(page)
        return pages


    def get_delete_url(self):
        try:
            opts = self.app.model._meta
            app_label = opts.app_label
            return reverse(u'{}_{}_{}'.format(app_label, opts.module_name, 'delete'), args = (self.obj.pk,))
        except:
            return None

    def has_delete_permission(self,user):
        opts = self.app.model._meta
        app_label = opts.app_label
        return user.has_perm('{}_{}_{}'.format(app_label, opts.module_name, 'delete'), self.obj)

    def has_detail_permission(self,user, page):
        opts = self.app.model._meta
        app_label = opts.app_label
        return user.has_perm('{}_{}_{}'.format(app_label, opts.module_name, 'detail_' + page.name), self.obj)

    def get_context(self, request):
        active_page = self.get_active_page(request)
        self.update_page_data(active_page, request)
        context ={
            'can_delete' : self.has_delete_permission(request.user),
            'delete_url' : self.get_delete_url(),
            'instance' : self.obj,
            'active_page' : active_page,
            'edit_urls' : active_page.get_edit_urls(self.obj, request.user),
            'pages' : self.get_pages(request),
        }
        return context

    def render(self,request):
        opts = self.app.model._meta
        app_label = opts.app_label
        context = self.get_context(request)
        return TemplateResponse(request,[
            '%s/%s/detail_view.html' % (app_label, opts.object_name.lower()),
            '%s/detail_view.html' % app_label,
            'detail_view.html'
        ], context, current_app=self.app.admin_site.name)


class ResumeView(object):
    def __init__(self, pages, app, object_id):
        self.pages = []
        for Page in pages:
            page = Page(app, resume = True)
            self.pages.append(page)
        self.app = app
        self.obj = get_object_or_404(app.model, pk=object_id)

    def update_page_data(self, request):
        for page in self.get_pages(request):
            page.load_context(self.obj, request)

    def get_context(self, request):
        self.update_page_data(request)
        context ={
            'can_delete' : self.has_delete_permission(request.user),
            'delete_url' : self.get_delete_url(),
            'instance' : self.obj,
            'pages' : self.get_pages(request),
            'edit_urls' : self.get_edit_urls(self.obj, request.user),
        }
        return context

    def get_edit_urls(self, obj, user):
        urls = self.app.edit_url_name
        if urls and not isinstance(urls, list):
            urls = [self.edit_url_name]
        if not urls:
            return None
        edit_links = []
        for url in urls:
            if user.has_perm(u'{}_{}_{}'.format(self.app.model._meta.app_label,
                                                self.app.model._meta.module_name,url),obj):
                if url in self.app.get_instance_views():
                    if hasattr(self.app.get_instance_views()[url],'label'):
                        url_name = self.app.get_instance_views()[url].label
                    else:
                        if 'edit_' in url:
                            url_name = url.split('edit_')[1]
                        else:
                            url_name = url

                edit_links.append((url_name, reverse('%s_%s_%s' % (self.app.model._meta.app_label,
                                                                   self.app.model._meta.module_name,url),args=(obj.pk,))))
        return edit_links

    def get_delete_url(self):
        try:
            opts = self.app.model._meta
            app_label = opts.app_label
            return reverse(u'{}_{}_{}'.format(app_label, opts.module_name, 'delete'), args = (self.obj.pk,))
        except:
            return None

    def has_delete_permission(self,user):
        opts = self.app.model._meta
        app_label = opts.app_label
        return user.has_perm('{}_{}_{}'.format(app_label, opts.module_name, 'delete'), self.obj)

    def has_detail_permission(self,user, page):
        opts = self.app.model._meta
        app_label = opts.app_label
        return user.has_perm('{}_{}_{}'.format(app_label, opts.module_name, 'detail_' + page.name), self.obj)

    def get_pages(self,request):
        pages= []
        for page in self.pages:
            if page.include_page(request,self.obj) and self.has_detail_permission(request.user, page):
                pages.append(page)
        return pages

    def render(self, request, detail=None):
        opts = self.app.model._meta
        app_label = opts.app_label
        context = self.get_context(request)
        if detail:
            context.update({ 'detail_pages' : detail.get_pages(request)})

        return TemplateResponse(request,[
            '%s/%s/view.html' % (app_label, opts.object_name.lower()),
            '%s/view.html' % app_label,
            'view.html'
        ], context, current_app=self.app.admin_site.name)
