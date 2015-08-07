from declry import site
from declry.apps import Application


class FormacaoAdmin(Application):
    list_display = ('nome','modulo','local','data_inicio','data_fim','coordenador')
    list_filter = ('data_inicio',)
    search_fields = ('nome','modulo','local')
