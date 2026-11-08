from django.urls import path

from . import views

urlpatterns = [
    path("", views.observation_list, name="observation_list"),
    path("observations/new/", views.observation_create, name="observation_create"),
    path("observations/<int:pk>/", views.observation_detail, name="observation_detail"),
    path("observations/<int:pk>/edit/", views.observation_edit, name="observation_edit"),
    path("observations/<int:pk>/autosave/", views.observation_autosave, name="observation_autosave"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
