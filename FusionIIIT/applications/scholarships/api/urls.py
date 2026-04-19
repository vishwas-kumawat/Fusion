<<<<<<< HEAD
"""
api/urls.py – Award & Scholarship Module
All API routing definitions for the scholarships module.
"""

from django.urls import path

from .views import (
    ApplicationDisbursementView,
    ApplicationStatusUpdateView,
    EligibleStudentsView,
    ScholarshipApplicationDetailView,
    ScholarshipApplicationListCreateView,
    ScholarshipTypeDetailView,
    ScholarshipTypeListCreateView,
)

app_name = "scholarships"

urlpatterns = [
    # ── Scholarship Types ──────────────────────────────────────────────
    path(
        "types/",
        ScholarshipTypeListCreateView.as_view(),
        name="scholarship-type-list-create",
    ),
    path(
        "types/<int:pk>/",
        ScholarshipTypeDetailView.as_view(),
        name="scholarship-type-detail",
    ),

    # ── Applications ───────────────────────────────────────────────────
    path(
        "applications/",
        ScholarshipApplicationListCreateView.as_view(),
        name="application-list-create",
    ),
    path(
        "applications/<int:pk>/",
        ScholarshipApplicationDetailView.as_view(),
        name="application-detail",
    ),
    path(
        "applications/<int:pk>/update-status/",
        ApplicationStatusUpdateView.as_view(),
        name="application-update-status",
    ),
    path(
        "applications/<int:pk>/disburse/",
        ApplicationDisbursementView.as_view(),
        name="application-disburse",
    ),

    # ── Eligible Students ──────────────────────────────────────────────
    path(
        "eligible-students/<int:pk>/",
        EligibleStudentsView.as_view(),
        name="eligible-students",
    ),
=======
from django.conf.urls import url
from . import views

urlpatterns = [
    # Student Views
    url(r'^student-profile/$', views.StudentProfileLookupAPIView.as_view(), name='api-student-profile'),
    url(r'^active-awards/$', views.ActiveAwardsAPIView.as_view(), name='api-active-awards'),
    url(r'^student/applications/$', views.StudentApplicationsAPIView.as_view(), name='api-student-applications'),
    url(r'^student/submit/mcm/$', views.McmSubmissionAPIView.as_view(), name='api-submit-mcm'),
    url(r'^student/submit/medal/$', views.MedalSubmissionAPIView.as_view(), name='api-submit-medal'),

    # Convener Views (legacy MCM/medal)
    url(r'^convener/application/(?P<application_id>\d+)/review/$', views.ConvenerActionAPIView.as_view(), name='api-convener-review'),

    # Scholarship Types
    url(r'^types/$', views.ScholarshipTypesAPIView.as_view(), name='api-scholarship-types'),

    # Scholarship Applications (full lifecycle)
    url(r'^applications/$', views.ScholarshipApplicationsAPIView.as_view(), name='api-scholarship-applications'),
    url(r'^applications/(?P<application_id>\d+)/approve/$', views.ScholarshipApplicationApproveAPIView.as_view(), name='api-scholarship-application-approve'),

    # General Awards Management
    url(r'^awards/$', views.AwardsManagementAPIView.as_view(), name='api-awards-management'),
    url(r'^awards/(?P<award_id>\d+)/$', views.AwardDetailAPIView.as_view(), name='api-award-detail'),

    # Merit Lists
    url(r'^merit-list/$', views.MeritListAPIView.as_view(), name='api-merit-list-all'),
    url(r'^merit-list/(?P<batch_id>[^/]+)/$', views.MeritListAPIView.as_view(), name='api-merit-list'),
    url(r'^generate-merit-list/$', views.GenerateMeritListAPIView.as_view(), name='api-generate-merit-list'),
    url(r'^convenor/mcm-merit-list/$', views.ConvenorMcmMeritListAPIView.as_view(), name='api-convenor-mcm-merit-list'),

    # Eligibility and Statistics
    url(r'^eligible-students/(?P<scholarship_id>\d+)/$', views.EligibleStudentsAPIView.as_view(), name='api-eligible-students'),
    url(r'^check-eligibility/$', views.StudentEligibilityCheckAPIView.as_view(), name='api-check-eligibility'),
    url(r'^statistics/batch/$', views.BatchStatisticsAPIView.as_view(), name='api-batch-statistics'),
    url(r'^mcm-applications/$', views.McmApplicationViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-mcm-applications'),
    url(r'^mcm-applications/(?P<pk>\d+)/$', views.McmApplicationViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='api-mcm-application-detail'),
    url(r'^single-parent-applications/$', views.SingleParentApplicationViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-single-parent-applications'),
    url(r'^single-parent-applications/(?P<pk>\d+)/$', views.SingleParentApplicationViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'}), name='api-single-parent-application-detail'),
    url(r'^settings/$', views.ScholarshipSettingsView.as_view(), name='api-scholarship-settings'),
>>>>>>> 98291d374ebf7ff621d59f26fe250a2426b0747e
]
