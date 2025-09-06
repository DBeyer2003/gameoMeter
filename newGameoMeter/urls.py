from django.urls import path, include
from django.conf import settings
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [ 
  path(r'', views.home_page_view, name="home"),
  path(r'all_games', views.ShowAllGamesView.as_view(), name="all_games"),
  path(r'search_results', views.SearchResultsView.as_view(), name="search_results"),
  path(r'game/<int:pk>', views.ShowGameDetailsView.as_view(), name="game_details"),
  path(r'game/<int:pk>/reviews', views.ShowGameReviewsView.as_view(), name="game_reviews"),
  path(r'game/<int:pk>/update_scores', views.UpdateGameScoresView.as_view(), name="update_scores"),

  #authentication URLS
  path('login/', auth_views.LoginView.as_view(template_name='newGameoMeter/login.html'), name='login'),
  path('logout/', auth_views.LogoutView.as_view(template_name='newGameoMeter/logged_out.html'), name='logout'),
]