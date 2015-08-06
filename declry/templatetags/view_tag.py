# _*_ encoding: utf-8  _*_
from copy import copy

from django.template import Library, loader, Context
from django.contrib.admin.templatetags.admin_static import static
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.core.serializers import serialize
from django.utils.safestring import mark_safe
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.core.urlresolvers import reverse


register = Library()

@register.simple_tag(takes_context=True)
def instance_card(context, instance=None):
    new_context= copy(context)
    if not instance:
        instance = context['instance']
    else:
        new_context['instance'] = instance
    templates = ['{0}/{1}/{1}_card.html'.format(instance._meta.app_label,instance._meta.module_name), 'card.html']

    t = loader.select_template(templates)
    return t.render(new_context)

def get_edit_url(instance):
    try:
        return reverse('%s_%s_edit_foto' % (instance._meta.app_label, instance._meta.module_name),
                args=(instance.pk,))
    except:
        return None

def has_edit_perm(user, instance):
    return user.has_perm('{}_{}_{}'.format(instance._meta.app_label, instance._meta.module_name,'edit_foto'), obj= instance)


@register.simple_tag(takes_context=True)
def instance_photo(context, size= 64, instance= None, edit_foto = False):

    no_edit_image_format = u'<img width="{2}" src="{0}" alt="{1}" />'

    edit_image_format = u"""
        <div class="inst-image" >
            <img width="{2}" src="{0}" alt="{1}" />
            <div class="foto-edit">
                <a href="{3}">
                    <i class="icon-edit"></i>{4}
                </a>
            </div>
        </div>
    """

    if not instance:
        instance = context['instance']

    # user = None
    # if 'request' in context:
    #     user = context['request'].user
    # if user and edit_foto and has_edit_perm(user, instance):
    #     image_format = edit_image_format
    #     edit_url = get_edit_url(instance)
    # else:
    image_format = no_edit_image_format
    edit_url = None
    if hasattr(instance,'foto'):
        if instance.foto:
            url = instance.foto.url
        else:
            url = static("img/empty.png")
    else:
        if instance.icon:
            return format_html(u'<div class="inst-icon" ><i class="icon-4x {}"> </i></div>',instance.icon)
        else:
            url = static("img/school.png")

    return format_html(image_format, url, force_text(instance),size,edit_url,_("Edit"))

@register.simple_tag (takes_context=True)
def get_module_name(context):
    instance = context['instance']
    return instance._meta.verbose_name

@register.filter
def display_string(name):
    return ' '.join([capfirst(x) for x in name.split('_')])

@register.filter
def ellipsis(value, limit=10):
    try:
        limit = int(limit)
    except ValueError:
        return value

    if not isinstance(value, unicode):
        value = unicode(value)

    if len(value) <= limit:
        return value

    try:
        value = u'{}{}'.format(value[:limit],'...')
    except Exception as e:
        return e.args

    return value

@register.filter
def cap_letters(value):
    return ''.join(c for c in value if c.isupper())

@register.filter
def dict_get(value, arg):
    return value[arg]

@register.filter
def jsonify(obj):
    if isinstance(obj, QuerySet):
        return serialize('json', obj)
    return mark_safe(simplejson.dumps(obj))

@register.filter
def simple_timeframe(value):
    value = unicode(value)
    return value.split('-')[0]


@register.filter
def can_edit(value, user):
    if hasattr(user, 'roles'):
        return value.has_instance_perm(user, "edit")
    return False

@register.filter
def getattr(obj, attr):
    if hasattr(obj,attr):
        return getattr(obj,attr)