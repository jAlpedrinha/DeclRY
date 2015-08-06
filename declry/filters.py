from django.contrib.admin import SimpleListFilter
from django.utils.translation import ugettext_lazy as _

class DynamicFilter(SimpleListFilter):
	template = 'admin/dynamic_filter.html'

	def choices(self, cl):
		if self.value() is None:
			self.display_value =  _('All')
		else :
			self.display_value = self.get_display_value()
		yield {
			'selected': self.value() is None,
			'query_string': cl.get_query_string({}, [self.parameter_name]),
			'dynamic' : False,
			'display': _('All'),
		}
		yield {
			'selected': self.value() is not None,
			'query_string': cl.get_query_string({self.parameter_name: '___value___'}, [self.parameter_name]),
			'dynamic' : True,
			'display': self.title,
		}

	def lookups(self, request, model_admin):
		"""
		Must be overriden to return a list of tuples (value, verbose value)
		"""	
		self.widget= self.widget.render(self.parameter_name,None)
		

	def has_output(self):
		return True
