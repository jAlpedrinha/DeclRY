# _*_  encoding: utf-8 _*_
from django.db import models
from django.core.urlresolvers import reverse

class CustomModelMixin(object):

    def is_dirty(self, attr = None):
        db_obj = self.db_instance
        if not db_obj:
            return False
        if attr:
            if self.__getattribute__(attr) != db_obj.__getattribute__(attr):
                return True
        else:
            for f in self._meta.local_fields:
                if self.__getattribute__(f.name) != db_obj.__getattribute__(f.name):
                    return True
        return False

    @property
    def db_instance(self):
        if hasattr(self,'pk') and self.pk:
            return self._default_manager.get(pk= self.pk)
        return None

    @staticmethod
    def has_model_perm(user, perm):
        return False

    def has_instance_perm(self, user, perm):
        if user.is_superuser:
            return True
        return user.permissions.has_perm('{}_{}_{}'.format(self._meta.app_label, self._meta.module_name, perm), self)

    def get_meta(self):
        return reverse('%s_%s_view' % (self._meta.app_label, self._meta.module_name),
                       args=(self.pk,))

    def get_absolute_url(self):
        try:
            return reverse('%s_%s_view' % (self._meta.app_label, self._meta.module_name),
                           args=(self.pk,))
        except :
            return None


class CustomModel(models.Model, CustomModelMixin):
    icon = "icon-group"
    class Meta:
        abstract = True
