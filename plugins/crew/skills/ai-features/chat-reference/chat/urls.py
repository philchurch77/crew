from django.urls import path

from . import views

urlpatterns = [
    path("", views.chat_page, name="chat"),
    path("stream/", views.stream_chat, name="chat_stream"),
    path("history/", views.chat_history, name="chat_history"),
    path("rename/<str:session_key>/", views.rename_chat, name="chat_rename"),
    path("delete/<str:session_key>/", views.delete_chat, name="chat_delete"),
    path("export/<str:session_key>/", views.export_chat, name="chat_export"),
]
