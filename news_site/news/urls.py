from django.urls import path
from . import views 

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('no-link/', views.no_link, name='no_link'),
    path('add_to_read_later/<int:news_id>/', views.add_to_read_later, name='add_to_read_later'),
    path('remove_from_read_later/<int:news_id>/', views.remove_from_read_later, name='remove_from_read_later'),
    path('read_later/', views.read_later_list, name='read_later_list'),
]
