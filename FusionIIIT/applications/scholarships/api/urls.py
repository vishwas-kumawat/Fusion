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
]
