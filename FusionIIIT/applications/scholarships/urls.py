from django.conf.urls import include, url
from django.http import JsonResponse


def spacs_root(_request):
    return JsonResponse({"message": "SPACS backend is active. Use /scholarships/api/ endpoints."})


urlpatterns = [
    url(r"^api/", include("applications.scholarships.api.urls")),
    url(r"^$", spacs_root, name="spacs_root"),
]