<<<<<<< HEAD
from django.conf.urls import url, include

from . import views

app_name = 'spacs'

urlpatterns = [

    url(r'^api/', include('applications.scholarships.api.urls')),
    url(r'^$', views.spacs, name='spacs'),
    url(r'^student_view/$', views.student_view, name='student_view'),
    url(r'^convener_view/$', views.convener_view, name='convener_view'),
    url(r'^staff_view/$', views.staff_view, name='staff_view'),
    url(r'^stats/$', views.stats, name='stats'),
    url(r'^convenerCatalogue/$', views.convenerCatalogue, name='convenerCatalogue'),
    url(r'^getWinners/$', views.getWinners, name='getWinners'),
    url(r'^get_MCM_Flag/$', views.get_MCM_Flag, name='get_MCM_Flag'),
    url(r'^getConvocationFlag/$', views.getConvocationFlag, name='getConvocationFlag'),
    url(r'^getContent/$', views.getContent, name='getContent'),
    url(r'^updateEndDate/$', views.updateEndDate, name='updateEndDate'),

]
=======
from django.http import JsonResponse
from django.urls import path


def spacs_root(_request):
    return JsonResponse({
        'message': 'SPACS backend is active. Use /scholarships/api/ endpoints.'
    })


urlpatterns = [
    path('', spacs_root, name='spacs_root'),
]
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
