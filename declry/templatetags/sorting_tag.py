from django import template
from django.http import Http404
from django.conf import settings
from copy import copy
register = template.Library()

REMOVE_ORDER = '<a href="{}"><i class="icon-remove"></i></a>'

sort_directions = {
    'asc': {'icon':'icon-arrow-up', 'inverse': 'desc'}, 
    'desc': {'icon':'icon-arrow-down', 'inverse': 'asc'}, 
    '': {'icon':'icon-arrow-down', 'inverse': 'asc'}, 
}

def strip_order_query(query):
    sortList = query.split('.')
    sortFields = [x.strip('-') for x in sortList]
    return (sortList,sortFields)

def create_query(sortFields):
    return '.'.join(sortFields)

def sortable_header(parser, token):
    """
    Parses a tag that's supposed to be in this format: {% sortable_header field title %}    
    """
    bits = [b.strip('"\'') for b in token.split_contents()]
    if len(bits) < 2:
        raise TemplateSyntaxError, "anchor tag takes at least 1 argument"
    try:
        title = bits[2]
    except IndexError:
        title = bits[1].capitalize()
    return SortableHeaderNode(bits[1].strip(), title.strip())
    

class SortableHeaderNode(template.Node):
    """
    Renders an <a> HTML tag with a link which href attribute 
    includes the field on which we sort and the direction.
    and adds an up or down arrow if the field is the one 
    currently being sorted on.

    Eg.
        {% anchor name Name %} generates
        <a href="/the/current/path/?sort=name" title="Name">Name</a>

    """
    def __init__(self, field, fields):
        self.field_variable = template.Variable(field)
        self.fields_variable = template.Variable(fields)

    def render(self, context):

        self.field_obj = self.field_variable.resolve(context)
        self.fields = self.fields_variable.resolve(context)
        self.title = self.field_obj.verbose_name
        self.field = self.fields.index(self.field_obj)+1
        mask = """
            <div class="table-header-sort">

                <a class="caption" href="{0}" title="{1}">
                    <div>
                        {1}
                    </div>
                </a>
                <div class="sort">
                    <span class="sort-index">{2}</span>
                    <span>{3}</span>
                    <span class="order">
                        <a  href="{0}" title="{1}">
                            {4}
                        </a>
                    </span>
                </div>
            </div>
            """
        request = context['request']
        getvars = request.GET.copy()

        if 'o' in getvars:
            (sortList,sortFields) = strip_order_query(getvars['o'])
        else:
            sortList = []
            sortFields = []
        
        fieldStr = str(self.field)

        if fieldStr in sortFields:
            index = sortFields.index(fieldStr)+1
            if fieldStr in sortList:
                oldField = fieldStr
                newField = '-' + fieldStr
                icon = '<i class="{}"></i>'.format(sort_directions['desc']['icon'])
            else:
                oldField = '-' + fieldStr
                newField = fieldStr
                icon = '<i class="{}"></i>'.format(sort_directions['asc']['icon'])

            removeList = copy(sortList)
            removeList.remove(oldField)
            removeQuery = create_query(removeList)
            removeOrder = REMOVE_ORDER.format(removeQuery and '{}?o={}'.format(request.path, removeQuery) or request.path)
            sortList[sortList.index(oldField)] = newField
        else:
            sortList.append(fieldStr)
            icon = '&nbsp;'
            removeOrder = ''
            index = ''

        sortQuery = create_query(sortList)

        url = '{}?o={}'.format(request.path, sortQuery)
        return mask.format(url, self.title, index, removeOrder, icon)



sortable_header = register.tag(sortable_header)
