from django.core.urlresolvers import reverse

class Menu(object):
	template = {}
	name = "menu"
	label = "Menu Label"
	models = []

	def __init__(self, request):
		self.app_url = reverse('app_list', kwargs={'app_label': self.name}, current_app="")

	def store_info(self, request, app_label):
		pass

	@classmethod
	def get_menus(cls, request):
		return [cls(request)]

