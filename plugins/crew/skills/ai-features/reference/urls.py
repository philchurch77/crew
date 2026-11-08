from django.urls import path

from . import views

app_name = "assistant"
urlpatterns = [
    path("suggest/", views.suggest, name="suggest"),
    path("accept/<int:pk>/", views.accept, name="accept"),
]
