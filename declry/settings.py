from django.conf import settings
settings.LOGIN_REDIRECT_URL = 'index'
print 'what?', settings.AUTHENTICATION_BACKENDS
settings.AUTHENTICATION_BACKENDS = (
    'declry.backends.backend.CoreBackend',
)
print settings.AUTHENTICATION_BACKENDS