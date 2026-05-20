from django.conf import settings


def app_info(request):
    return {
        'APP_NAME': settings.APP_NAME,
    }
