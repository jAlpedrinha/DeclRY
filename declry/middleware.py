from django.utils.functional import SimpleLazyObject
from django.contrib.auth.middleware import load_backend
from django.conf import settings



SESSION_KEY = '_auth_user_id'
BACKEND_SESSION_KEY = '_auth_user_backend'

def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = load_user(request)
    return request._cached_user

def load_user(request):
    from django.contrib.auth.models import AnonymousUser
    from notifications.models import user_notification_digest
    try:
        user_id = request.session[SESSION_KEY]
        backend_path = request.session[BACKEND_SESSION_KEY]
        backend = load_backend(backend_path)
        user = backend.get_user(user_id) or AnonymousUser()
        # user.roles = request.session.get('roles', None)
        # set_permission(user, request)
        # user.notifications = user_notification_digest(user)
    except KeyError:
        user = AnonymousUser()
        # user.roles = request.session.get('roles', None)
        # set_permission(user, request)
        user.tipo = None
    return user


class AuthMiddleware(object):
    def process_request(self, request):
        assert hasattr(request, 'session'), "The Django authentication middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
        request.user = SimpleLazyObject(lambda: get_user(request))


