"""
interfaces/api/v1/router.py

DRF router wiring for v1 ViewSets.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from interfaces.api.v1.job.views import JobViewSet
from interfaces.api.v1.matching.views import MatchView
from interfaces.api.v1.resume.views import ResumeViewSet

router = DefaultRouter()
router.register(r"resumes", ResumeViewSet, basename="resume")
router.register(r"jobs", JobViewSet, basename="job")

urlpatterns = [
    path("", include(router.urls)),
    path("match/", MatchView.as_view(), name="match"),
]
