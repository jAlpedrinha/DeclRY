# _*_  encoding: utf-8 _*_

from django.contrib.admin.util import NestedObjects, quote
from django.core.urlresolvers import reverse
from django.utils.html import format_html
from django.utils.text import capfirst
from django.utils.encoding import force_text
from django.shortcuts import _get_queryset
##################
#     Roles      #
##################

class Role(object):
	def __init__(self, name, list_ids = []):
		self.name = name
		self.list_ids = list_ids

	def __unicode__(self):
		return '{}_{}'.format(self.name, self.list_ids)

	def __str__(self):
		return '{}_{}'.format(self.name, self.list_ids)


def has_role(search_role, roles, obj_id = None):
	if not type(search_role) is list:
		search_role = [search_role]
	if roles:
		matching_roles = [x for x in roles if x.name in search_role]
	else:
		matching_roles = []
	if obj_id:
		for role in matching_roles:
			if obj_id in role.list_ids:
				return True
		return False
	elif matching_roles:
		return True

	return False

def get_role_ids(search_role, roles):
	if not type(search_role) is list:
		search_role = [search_role]
	matching_roles = [x for x in roles if x.name in search_role]
	ids = []
	[ids.extend(role.list_ids) for role in matching_roles]
	return ids

def get_object_or_none(klass, *args, **kwargs):
    """
    Uses get() to return an object, or raises a Http404 exception if the object
    does not exist.

    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.

    Note: Like with get(), an MultipleObjectsReturned will be raised if more than one
    object is found.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return None

def get_deleted_objects(objs, opts, user, admin_site, using):
	"""
	Find all objects related to ``objs`` that should also be deleted. ``objs``
	must be a homogenous iterable of objects (e.g. a QuerySet).

	Returns a nested list of strings suitable for display in the
	template with the ``unordered_list`` filter.

	"""
	collector = NestedObjects(using=using)
	collector.collect(objs)
	perms_needed = set()

	def format_callback(obj):
		has_admin = obj.__class__ in admin_site._registry
		opts = obj._meta

		if has_admin:
			admin_url = reverse('%s_%s_edit'
								% (
								   opts.app_label,
								   opts.object_name.lower()),
								None, (quote(obj._get_pk_val()),))
			p = '%s_%s_delete' % (opts.app_label,opts.object_name.lower())
			if not user.has_perm(p):
				perms_needed.add(opts.verbose_name)
			# Display a link to the admin page.
			return format_html(u'{0}: <a href="{1}">{2}</a>',
							   capfirst(opts.verbose_name),
							   admin_url,
							   obj)
		else:
			# Don't display link to edit, because it either has no
			# admin or is edited inline.
			return '%s: %s' % (capfirst(opts.verbose_name),
								force_text(obj))

	to_delete = collector.nested(format_callback)

	protected = [format_callback(obj) for obj in collector.protected]

	return to_delete, perms_needed, protected

def get_value_from_accessor(instance, accessor):
    if not accessor:
        return None
    elif accessor == 'self':
        return instance

    if '__' in accessor:
        accessors = accessor.split('__')
    else:
        accessors = [accessor]

    accessor = accessors[0]
    if hasattr(instance, accessor):
        instance = getattr(instance,accessor, None)
    else:
        return None
    if len(accessors) > 1:
        instance = get_value_from_accessor(instance, '__'.join(accessors[1:]))
    return instance