from django.urls import path
from . import views

app_name = 'universities'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('universities/', views.university_list_view, name='university_list'),
    path('university/<int:university_id>/', views.university_detail_view, name='university_detail'),
    path('university/<int:university_id>/rate/', views.rate_university_view, name='rate_university'),
    path('comparison/', views.comparison_view, name='comparison'),
    path('compare/<str:university_ids>/', views.compare_universities_view, name='compare_universities'),
    path('rating/', views.rating_leaderboard_view, name='rating_leaderboard'),
    path('university/<int:university_id>/news/create/', views.create_news_view, name='create_news'),
    path('news/', views.news_list_view, name='news_list'),
    path('news/<int:news_id>/', views.news_detail_view, name='news_detail'),
]
