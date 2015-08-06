from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from scholradmin.util import get_value_from_accessor
class TableField(object):
    header_levels = 1

    def __init__(self, label = 'label', accessor = '', th = False ,value_styles = {}, header_styles = {}):
        self.label = label
        self.accessor = accessor
        self.th = th
        self.header_styles = header_styles
        self.value_styles = value_styles

    def get_from_data(self, data):
        pass

    def get_value(self, data):
        return {'caption': self.get_from_data(data), 'th' : self.th, 'colspan' : 1, 'rowspan' : 1, 'style' : self.value_styles}

    def get_header(self, level):
        return {'caption': self.label, 'th' : True, 'colspan' : 1, 'rowspan' : 1, 'style' : self.header_styles}


class DatasetField(TableField):
    def get_from_data(self, data):
        return data.get(self.accessor, None)


class ModelField(TableField):
    def __init__(self, accessor, model, *args, **kwargs):
        if not 'label' in kwargs:
            kwargs['label'] = model._meta.get_field_by_name(accessor)[0].verbose_name.capitalize()
        kwargs['accessor'] = accessor
        super(ModelField, self).__init__(*args, **kwargs)

    def get_from_data(self, data):
        return get_value_from_accessor(data, self.accessor)

class DisplayModelField(ModelField):
    def get_from_data(self, data):
        return get_value_from_accessor(data, u'get_{}_display'.format(self.accessor))

class ModelLinkField(ModelField):
    def get_from_data(self, data):
        instance= super(ModelLinkField,self).get_from_data(data)
        return mark_safe(u'<a href="{}">{}</a>'.format(instance.get_absolute_url(), instance))


class FotoModelField(ModelField):
    width = 32
    def __init__(self, *args, **kwargs):
        if 'width' in kwargs:
            self.width = kwargs['width']
        super(FotoModelField, self).__init__(*args, **kwargs)
    def get_from_data(self, data):
        instance= super(FotoModelField,self).get_from_data(data)
        return mark_safe(u'<img src="{}" width="{}"></img>'.format(instance.url, self.width))


class UnicodeField(TableField):
    def __init__(self, model, *args, **kwargs):
        if not 'label' in kwargs:
            kwargs['label'] = model._meta.verbose_name.capitalize()
        super(UnicodeField, self).__init__(*args, **kwargs)
    def get_from_data(self, data):
        return unicode(data)


class LinkField(UnicodeField):
    def get_from_data(self, data):
        return mark_safe(u'<a href="{}">{}</a>'.format(data.get_absolute_url(), data))


class FunctionField(TableField):
    def __init__(self, lambda_function, *args, **kwargs):
        self.lambda_function = lambda_function
        super(FunctionField, self).__init__(*args, **kwargs)
    def get_from_data(self, data):
        return self.lambda_function(data)


class DatasetLinkField(DatasetField):
    def get_from_data(self, data):
        instance= super(DatasetLinkField,self).get_from_data(data)
        return mark_safe(u'<a href="{}">{}</a>'.format(instance.get_absolute_url(), instance))



class TableData(object):
    template = 'reports/crosstab.html'
    def __init__(self, fields, dataset, template = None):
        self.fields = fields
        self.dataset = dataset
        if template:
            self.template = template

    def get_headers(self):
        headers = [[]]
        for field in self.fields:
            for level in range(field.header_levels):
                headers[level].append(field.get_header(level))
        return headers

    def get_values(self):
        values = []
        for data in self.dataset:
            data_values = []
            for field in self.fields:
                data_values.append(field.get_value(data))
            values.append(data_values)
        return values
    def get_context(self):
        return {
            'headers' : self.get_headers(), 
            'body' : self.get_values()
        }
    def __unicode__(self):
        rendered = render_to_string(self.template, self.get_context())
        return mark_safe(rendered)