from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('core:dashboard' if request.session.get('email') else 'core:login'), name='home'),
    path('', include('core.urls')),
]
