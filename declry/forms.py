# _*_ encoding: utf-8  _*_
from django.forms import fields, HiddenInput, widgets
from django.forms import ModelForm, Form
from django.forms.util import flatatt

from itertools import chain
# from form_utils.forms import BetterModelForm, BetterForm
from django.utils.html import conditional_escape, format_html
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils import six
from fnmatch import fnmatch
from .util import get_value_from_accessor

field_html_mask = u"""
	<div class="row-fluid">
		<div class="span4 label-span"> 
			%(label)s
		</div>
		<div class="span8">
			<div %(html_class_attr)s>%(field)s%(help_text)s</div>
			<div class="errors">%(errors)s</div>
		</div>
	</div>"""

form_mask = u"""
	<div class="row-fluid">
		<div class="span6">
			{0}
		</div>  
		<div class="span6">
			{1}
		</div>  
	</div>
	"""


simple_form_mask = u"""
	<div class="row-fluid">
		<div class="offset1 span10">
			{}
		</div>
	</div>
	"""

named_fieldset_mask = u"""
	<div class="row-fluid panel" data-toggle="collapse" data-target="#{0}">
		<div class="offset1 span1">
			<span class="btn-minimize">
				<i id="icon-{0}" class="icon-arrow-down"></i>
			</span>
		</div>
		<div class="span8" >
			<div class="title">{1}</div>
		</div>
	</div>
	<div class="row-fluid collapse in fieldgroup" id="{0}">{2}</div>
	"""



class BootstrapMixin(object):

    fieldsets = None
    simple_form = False
    def __init__(self, *args, **kwargs):
        if self.fieldsets:
            if not isinstance(self.fieldsets, tuple):
                self.simple_form = True
                self.fieldsets = ( (None, self.fieldsets), )
        elif self.fields:
            self.simple_form = True
            self.fieldsets = ( (None, self.fields), )
        new_fields = {}
        
        for fieldset_name, fieldset in self.fieldsets:
            fields = self.flatten(fieldset)
            for name in fields:
                field = self.fields.get(name)
                new_fields[name] = field
        self.fields = new_fields

    def flatten(self, fields):
        wildcards = [x for x in fields if '*' in x]
        for wildcard in wildcards:
            fields.remove(wildcard)
            fields.extend([model_field.name for model_field in self._meta.model._meta.fields if fnmatch(model_field.name,wildcard)])
        return fields

    def as_bootstrap(self):
        "Returns this form rendered as HTML <tr>s -- excluding the <table></table>."
        return self.html_better_output(
            normal_row = field_html_mask,
            error_row = '<div>%s</div>',
            row_ender = '</div>',
            help_text_html = '<br/><span class="helptext">%s</span>',
            errors_on_separate_row = False,
            fieldset_html = None,
            label_class='')

    def update_hidden_fields(self):
        fieldset_fields = []
        top_errors, hidden_fields = [],[]
        for fieldset_name, fieldset in self.fieldsets:
            fieldset_fields.extend(self.flatten(fieldset))

        for name, field in self.fields.items():
            if name not in fieldset_fields:
                bf = self[name]
                if bf.is_hidden:
                    bf_errors = self.error_class([conditional_escape(error) for error in bf.errors])
                    if bf_errors:
                        top_errors.extend(['(Hidden field %s) %s' % (name, force_text(e)) for e in bf_errors])
                    hidden_fields.append(six.text_type(bf))
        return hidden_fields, top_errors

    def html_better_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row,fieldset_html, label_class=None):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output_global, output, hidden_fields = [], [], []
        hidden_fields, top_errors = self.update_hidden_fields()
        for fieldset_name, fieldset in self.fieldsets:
            fields = self.flatten(fieldset)
            fieldset_inner = []
            for name in fields:
                field = self.fields.get(name)
                html_class_attr = ''
                bf = self[name]
                bf_errors = self.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
                if bf.is_hidden:
                    if bf_errors:
                        top_errors.extend(['(Hidden field %s) %s' % (name, force_text(e)) for e in bf_errors])
                    hidden_fields.append(six.text_type(bf))
                else:
                    # Create a 'class="..."' atribute if the row should have any
                    # CSS classes applied.
                    css_classes = bf.css_classes()
                    if css_classes:
                        html_class_attr = ' class="%s"' % css_classes

                    if errors_on_separate_row and bf_errors:
                        output.append(error_row % force_text(bf_errors))

                    if bf.label:
                        label = conditional_escape(force_text(bf.label))

                        # If field is required put an asterisk
                        if field.required or hasattr(field, 'mandatory') and field.mandatory:
                            label = "* " + label

                        # Only add the suffix if the label does not end in
                        # punctuation.
                        if self.label_suffix:
                            if label[-1] not in ':?.!':
                                label = format_html(u'{0}{1}', label, self.label_suffix)
                        
                        if label_class:
                            label = bf.label_tag(label,{'class' : label_class}) or ''
                        else:
                            label = bf.label_tag(label) or ''
                    else:
                        label = ''

                    if field.help_text:
                        help_text = help_text_html % force_text(field.help_text)
                    else:
                        help_text = ''

                    fieldset_inner.append(normal_row % {
                        'errors': force_text(bf_errors),
                        'label': force_text(label),
                        'field': six.text_type(bf),
                        'help_text': help_text,
                        'html_class_attr': html_class_attr
                    })

            if fieldset_name is None:
                output_global.append(mark_safe('\n'.join(fieldset_inner)))
            else:
                fieldset_name = force_text(fieldset_name)
                output.append(named_fieldset_mask.format(fieldset_name.replace(" ", ""), fieldset_name,
                                                         mark_safe('\n'.join(fieldset_inner))))

        if top_errors:
            output_global.insert(0, error_row % force_text(top_errors))

        if hidden_fields: # Insert any hidden fields in the last row.
            str_hidden = ''.join(hidden_fields)
            if output_global:
                last_row = output_global[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                if not last_row.endswith(row_ender):
                    # This can happen in the as_p() case (and possibly others
                    # that users write): if there are only top errors, we may
                    # not be able to conscript the last row for our purposes,
                    # so insert a new, empty row.
                    last_row = (normal_row % {'errors': '', 'label': '',
                                              'field': '', 'help_text':'',
                                              'html_class_attr': html_class_attr})
                    output_global.append(last_row)

                output_global[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output_global.append(str_hidden)

        if self.simple_form:
            return mark_safe(simple_form_mask.format('\n'.join(output_global)))
        else:
            return mark_safe(form_mask.format('\n'.join(output_global), '\n'.join(output)))


class BootstrapModelForm(ModelForm,BootstrapMixin):

    def __init__(self, *args, **kwargs):
        super(BootstrapModelForm,self).__init__(*args,**kwargs)
        BootstrapMixin.__init__(self,*args,**kwargs)

        for name, field in self.fields.items():
            if isinstance(field, fields.DateField) and not isinstance(field.widget, HiddenInput):
                field.widget.format = '%d/%m/%Y'
                field.widget.attrs.update({'class':'datePicker'})
                field.input_formats = ['%d/%m/%Y']

    def __str__(self):
        return self.as_bootstrap()
    def __unicode__(self):
        return self.as_bootstrap()


class BootstrapForm(Form,BootstrapMixin):
    def __init__(self, *args, **kwargs):
        super(BootstrapForm,self).__init__(*args,**kwargs)
        BootstrapMixin.__init__(self,*args,**kwargs)
        for name, field in self.fields.items():
            if isinstance(field, fields.DateField) and not isinstance(field.widget, HiddenInput):
                field.widget.format = '%d/%m/%Y'
                field.widget.attrs.update({'class':'datePicker'})
                field.input_formats = ['%d/%m/%Y']

    def __str__(self):
        return self.as_bootstrap()
    def __unicode__(self):
        return self.as_bootstrap()


class DynamicSelectWidget(widgets.Widget):
    allow_multiple_selected = False
    def __init__(self, attrs=None, queryset=(), depend_field = None, depend_accessor= ''):
        """
        Choices is a queryset and is not treated as a regular choices fields
        """
        self.depend_field = depend_field
        self.depend_accessor = depend_accessor
        self.queryset = queryset
        super(DynamicSelectWidget, self).__init__(attrs)
        
    def render(self, name, value, attrs=None, choices=()):
        class_dict = {'class' : 'dynamic_select', 'data-depends' : 'id_' + self.depend_field}
        if attrs:
            attrs.update(class_dict)
        else:
            attrs = class_dict
        if value is None: value = ''
        final_attrs = self.build_attrs(attrs, name=name)
        output = [format_html('<select{0}>', flatatt(final_attrs))]
        options = self.render_options(choices, [value])
        if options:
            output.append(options)
        output.append('</select>')
        return mark_safe('\n'.join(output))

   
    def render_option(self, selected_choices, option_value, option_label, option_dependency):
        option_value = force_text(option_value)
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html(u'<option value="{0}" data-id_{1}="{2}" {3}>{4}</option>',
                           option_value,
                           self.depend_field,
                           option_dependency,
                           selected_html,
                           force_text(option_label))

    def render_options(self, choices, selected_choices):
        # Normalize to strings.
        selected_choices = set(force_text(v) for v in selected_choices)
        output = []
        for option in chain(self.queryset, choices):
            if isinstance(option, tuple):
                option_value = option[0]
                option_label = option[1]
                option_dependency = ''
            else:
                option_value = option.pk
                option_label = str(option)
                option_dependency = get_value_from_accessor(option, self.depend_accessor)
            output.append(self.render_option(selected_choices, option_value, option_label, option_dependency))
        return '\n'.join(output)