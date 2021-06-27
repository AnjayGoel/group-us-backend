from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('create', views.create_poll, name='create'),
    path('vote/<str:proj_id>/<str:mem_id>', views.vote, name='vote'),
    path('check', views.trigger_check_deadline, name='trigger_check_deadline'),
]
