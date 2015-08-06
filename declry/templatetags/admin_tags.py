from django.template import Library
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.contrib.admin.views.main import PAGE_VAR
register = Library()

@register.simple_tag
def paginator_number(cl,i):
    """
    Generates an individual page index link in a paginated list.
    """
    if i == '.':
        return format_html('<li class="active"><a href="#">{0}</a></li> ', '...')
    elif i == cl.page_num:
        return format_html('<li class="active"><a href="#">{0}</a></li> ', i+1)
    else:
        return format_html('<li><a href="{0}">{1}</a></li>',
                           cl.get_query_string({PAGE_VAR: i}),
                           i+1)

@register.simple_tag
def paginator_prev(cl):
    """
    Generates an individual page index link in a paginated list.
    """
    if cl.page_num == 0:
      return format_html(u'<li class="prev disabled"><a href="#">{0}</a></li> ', _('Previous Page'))
    else:
      return format_html(u'<li class="prev"><a href="{0}">{1}</a></li>',
        cl.get_query_string({PAGE_VAR: cl.page_num-1}),_('Previous Page'))

@register.simple_tag
def paginator_next(cl):
    """
    Generates an individual page index link in a paginated list.
    """
    if cl.page_num == cl.paginator.num_pages-1:
      return format_html(u'<li class="next disabled"><a href="#">{0}</a></li> ', _('Next Page'))
    else:
      return format_html(u'<li class="next"><a href="{0}">{1}</a></li>',
        cl.get_query_string({PAGE_VAR: cl.page_num+1}), _('Next Page'))