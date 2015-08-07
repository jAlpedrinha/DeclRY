from django.contrib.auth.backends import ModelBackend
from django.db.models.loading import get_model
from django.core.validators import email_re
from django.contrib.auth.models import AnonymousUser

#from django.conf.settings import AUTH_USER_MODEL

class CoreBackend(ModelBackend):

    

    def has_perm(self, user_obj, perm, obj=None):
        pass
        # if user_obj.is_superuser:
        #     return True
        # perm_parts = perm.split('_')
        # app_label = perm_parts[0]
        # model_name = perm_parts[1]
        
        # permission = '_'.join(perm_parts[2:])
        # if not obj:
        #     model = get_model(app_label, model_name,
        #           seed_cache=False, only_installed=False)
        #     return model.has_model_perm(user_obj,permission)

        # else:
        #     return obj.has_instance_perm(user_obj, permission)


    def has_module_perms(self, user_obj, app_label):
        """
        Returns True if user_obj has any permissions in the given app_label.
        """
        print 'aqui'
        if not user_obj.is_active or isinstance(user_obj, AnonymousUser):
            return False
        return True

        
    def get_group_permissions(self, user_obj, obj=None):
        pass
    def get_all_permissions(self, user_obj, obj=None):
        pass

