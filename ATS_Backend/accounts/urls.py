from django.urls import path
from .views import register_view, dashboard, ats_check, compare, about, history
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('register/', register_view, name='register'),
    path('dashboard/',dashboard,name='dashboard'),
    path('ats_check/',ats_check,name='ats_check'),
    path('compare/',compare,name='compare'),
    path('history/',history,name='history'),
    path('about/',about,name='about')
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)