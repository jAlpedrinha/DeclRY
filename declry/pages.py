# _*_ encoding: utf-8  _*_
import calendar
from datetime import date,timedelta
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from fnmatch import fnmatch
from .tables import TableData


class Page(object):
    name = "tab"
    label = "Page"
    template = 'tabs/view_tab.html'
    icon = "icon-info-sign"
    resume_template = None
    fields = None
    context= None
    edit_url_name = None

    def __init__(self, app, resume = False):
        self.app = app
        self.resume = resume
        if not hasattr(self,'model'):
            self.model = app.model

    def get_fields(self, request=None):
        return self.fields

    def get_edit_urls(self, obj, user):
        urls = self.edit_url_name
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

    def load_context(self, obj, request = None):
        self.request = request
        if obj:
            self.context = {
            'instance' : obj
            }
        else:
            self.context_errors = _("No instance found")

    def include_page(self,request,obj):
        return True

    def __unicode__(self):
        if not self.context:
            return mark_safe(self.context_errors)

        template = self.template
        if self.resume and self.resume_template:
            template = self.resume_template

        rendered = render_to_string(template, self.context)
        return mark_safe(rendered)


class CrosstabPage(Page):
    template = 'tabs/crosstab_page.html'

    def load_context(self, obj, request = None):
        crosstab = self.get_crosstab(obj)
        if not crosstab:
            self.context_errors = u'<div>{}</div>'.format(_('No %(model_verbose_name)s found') %
                { 'model_verbose_name' : force_text(self.model._meta.verbose_name_plural) or self.name})
            return None

        self.context = {
            'crosstab' : crosstab,
            'instance' : obj
        }

        
class TablePage(Page):
    fields = []
    template = 'tabs/tabledata_page.html'
    tabledata_template = 'tabledata/page.html'
    def get_tabledata(self, dataset):
        return TableData(self.fields, dataset, self.tabledata_template)

    def load_context(self, obj, request = None):
        self.request = request
        dataset = self.get_dataset(obj)
        if not dataset:
            self.context_errors = u'<div>{}</div>'.format(_('No %(model_verbose_name)s found') %
                { 'model_verbose_name' : force_text(self.model._meta.verbose_name_plural) or self.name})
            return None
        table_data = self.get_tabledata(dataset)
        self.context = {
            'table_data' : table_data,
            'instance' : obj
        }




class DetailPage(Page):
    template = 'tabs/view_tab.html'
    label = "Detail Page"
    _simple_template = 'tabs/simple_view_tab.html'
    resume_template = 'tabs/table_detail_tab.html'
    _simple_detail = False

    def __init__(self, app, resume = False):
        super(DetailPage,self).__init__(app, resume)

    def get_fields(self, request=None):
        self.update_fields()
        return self.fields

    def update_fields(self):
        if self.fields:
            if not isinstance(self.fields, tuple):
                self.fields = ( (None, self.fields), )
                self._simple_detail = True
            new_fields = ()
            for fieldset_name, fieldset in self.fields:
                fields = self.flatten(fieldset)
                new_fields = new_fields + ((fieldset_name,fields),)
            self.fields = new_fields
        else:
            self.fields = ( (None, [x.name for x in self.model._meta.fields if x.name != 'id']),)
            self._simple_detail = True

    def load_context(self, obj, request = None):
        self.request = request
        self.context = None
        if obj:
            self.context = {
                'instance': obj,
                'groups' : self.get_detail_groups(obj, request)
            }
        else:
            self.context_errors = _("No instance found")
        if self._simple_detail:
            self.template = self._simple_template

    def flatten(self, fields):
        wildcards = [x for x in fields if '*' in x]
        for wildcard in wildcards:
            fields.remove(wildcard)
            fields.extend([model_field.name for model_field in self.model._meta.fields if fnmatch(model_field.name,wildcard)])
        return fields

    def get_detail_groups(self,obj, request):
        groups =[]
        for key, fields in self.get_fields(request):
            field_items = []
            for field in fields:
                if hasattr(obj, field):
                    value = getattr(obj, field)
                    if hasattr(value, 'get_absolute_url') and value.get_absolute_url():
                        value = mark_safe(u'<a href="{}">{}</a>'.format(value.get_absolute_url(), value))

                    if self.model._meta.get_field(field).choices:
                        lookup_field = 'get_{0}_display'.format(field)
                        value = getattr(obj,lookup_field)()
                    field_label = self.model._meta.get_field(field).verbose_name
                elif hasattr(self, field):
                    value = getattr(self, field)
                    if hasattr(value, 'label'):
                        field_label = value.label
                    else:
                        field_label = field

                    if callable(value):
                        value = value(obj)

                field_items.append({
                'label' : field_label,
                'value' : value
                })
            if key:
                groups.append( { 'name' : _(key), 'fields': field_items })
            else:
                groups.append( { 'name' :  None, 'fields': field_items})
        return groups


class ListDetailPage(DetailPage):
    template = 'tabs/list_view_tab.html'
    label = "List Detail Page"
    resume_template = None
    def __init__(self, app, resume = False):
        self.app = app
        self.update_fields()
        self.resume = resume

    def load_context(self, obj, request = None):
        if hasattr(self,'get_queryset'):
            query_instances = self.get_queryset(obj, request)
            if not query_instances:
                self.context_errors = u'<div>{}</div>'.format(_(u'No %(model_verbose_name)s found') %
                    { 'model_verbose_name' : force_text(self.model._meta.verbose_name_plural) or self.name})
                return None
            instances, labels = self.get_instances_details(query_instances)
        else:
            self.context_errors = _("Unable to load page")
            return None

        self.context = {
            'instances' : instances,
            'object' : obj,
            'labels' : labels,
            'name' : self.name
        }

    def get_instances_details(self, query_instances):
        instances = []
        labels = []
        for instance in query_instances:
            groups = []
            for key, fields in self.get_fields():
                field_items = []
                for field in fields:
                    if hasattr(instance, field):
                        value = getattr(instance, field)
                        if hasattr(value, 'get_absolute_url') and value.get_absolute_url():
                            value = mark_safe(u'<a href="{}">{}</a>'.format(value.get_absolute_url(), value))
                        if self.model._meta.get_field(field).choices:
                            lookup_field = 'get_{0}_display'.format(field)
                            value = getattr(instance,lookup_field)()
                        field_label = self.model._meta.get_field(field).verbose_name
                    elif hasattr(self, field):
                        value = getattr(self, field)
                        if hasattr(value, 'label'):
                            field_label = value.label
                        else:
                            field_label = field

                        if callable(value):
                            value = value(instance)

                    if field_label not in labels:
                        labels.append(field_label)
                    field_items.append({
                    'label' : field_label,
                    'value' : value
                    })
                if key:
                    groups.append({'name' : _(key), 'fields': field_items})
                else:
                    groups.append({'name' : None, 'fields': field_items})
            instances.append({ 'instance' : instance, 'groups' : groups })

        return instances, labels


class CalendarElement(object):
    template = "tabs/calendar_element.html"
    name = "element"

    def __init__(self, instance):
        self.name = self.get_name(instance)
        self.instance = instance
        self.date = self.get_date(instance)
        self.context = self.load_context()

    def load_context(self):
        return {
        'name' : self.name,
        'instance' : self.instance,
        'date' : self.date
        }

    def get_name(self, instance):
        return instance.name

    def get_date(self, instance):
        return instance.date


    def __unicode__(self):
        if not self.context:
            return mark_safe(self.context_errors)

        template = self.template

        return mark_safe(render_to_string(template, self.context))

def add_months(initial_date, months):
    months = months + initial_date.month
    years = 0
    if months > 0:
        years = (months-1) // 12;
    elif months < 0:
        years = -1-(abs(months) // 12);

    year = initial_date.year + years
    months = months - years*12
    if months == 0:
        month = 12
    else:
        month = months
    day = initial_date.day
    return date(year, month, day)


class CalendarPage(Page):
    elementClass = CalendarElement
    label = "Calendar Page"
    template = "tabs/calendar_view.html"
    icon = "icon-calendar"
    month = 0
    def load_context(self, obj, request = None):
        if 'month' in request.GET:
            self.month = int(request.GET['month'])
        initial_date = self.get_initial_date(request)
        end_date = self.get_end_date(request)
        instances = self.get_objects(obj,request, initial_date, end_date)
        current_month = self.get_current_month()

        days = {}
        temp_date = initial_date
        while temp_date != end_date:
            days[temp_date.isoformat()] ={
            'current' : temp_date.month == current_month,
            'date' : temp_date,
            'elements' : []
            }
            temp_date = temp_date + timedelta(days=1)
        for instance in instances:
            element = self.elementClass(instance)
            days[element.date.isoformat()]['elements'].append(element)

        weeks = []
        temp_date = initial_date
        counter = 0
        week_days = []
        while temp_date != end_date:
            week_days.append(days[temp_date.isoformat()])
            counter = counter + 1
            temp_date = temp_date + timedelta(days=1)
            if counter == 7 :
                counter = 0
                weeks.append({ 'days' : week_days})
                week_days = []
        if obj:
            self.context = {
            'month_label' : calendar.month_name[current_month],
            'month' : self.month,
            'weeks' : weeks,
            'instance' : obj,
            'current_url' : self.get_current_url(request)
            }
            self.context.update(self.get_extra_context(obj,request))
        else:
            self.context_errors = _("No instance found")

    def get_extra_context(self,obj, request):
        return {}

    def get_current_month(self):
        crnt_date = date.today()
        crnt_date = crnt_date - timedelta(days = crnt_date.day-1)
        return add_months(crnt_date, self.month).month


    def get_current_url(self,request):
        path = request.get_full_path()
        parts = path.split('&')
        return '&'.join([x for x in parts if not x.startswith('month=')])

    def get_objects(self, obj, request, start_date, end_date):
        pass

    def get_initial_date(self, request):
        initial_date = date.today()

        if initial_date.day != 1:
            initial_date = initial_date - timedelta(days = initial_date.day-1)

        initial_date = add_months(initial_date, self.month)

        if initial_date.weekday() > 0:
            initial_date = initial_date - timedelta(days = initial_date.weekday())
        return initial_date

    def get_end_date(self, request):
        end_date = date.today()
        end_date = end_date - timedelta(days = end_date.day-1)

        end_date = add_months(end_date, self.month+1)

        end_date = end_date - timedelta(days = end_date.day)
        if end_date.weekday() < 6:
            end_date = end_date + timedelta(days = 7-end_date.weekday())

        return end_date

