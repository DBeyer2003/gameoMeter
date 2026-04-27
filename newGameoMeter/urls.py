from django.urls import path, include
from django.conf import settings
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [ 
  path(r'gameometer', views.home_page_view, name="home"),
  path(r'gameometer/', views.home_page_view, name="home"),
  path(r'gameometer/all_games', views.ShowAllGamesView.as_view(), name="all_games"),
  path(r'gameometer/search_results', views.SearchResultsView.as_view(), name="search_results"),
  
  path(r'gameometer/create_game', views.CreateGameInfoView.as_view(), name="create_game"),
  #all of the pages related to a specific game.
  path(r'gameometer/game/<int:pk>', views.ShowGameDetailsView.as_view(), name="game_details"),
  path(r'gameometer/game/<int:pk>/', views.ShowGameDetailsView.as_view(), name="game_details"),
  path(r'gameometer/game/<int:pk>/reviews', views.ShowGameReviewsView.as_view(), name="game_reviews"),
  path(r'gameometer/game/<int:pk>/reviews/', views.ShowGameReviewsView.as_view(), name="game_reviews"),
  path(r'gameometer/game/<int:pk>/update_game', views.UpdateGameInfoView.as_view(), name="update_game"),
  path(r'gameometer/game/<int:pk>/update_scores', views.UpdateGameScoresView.as_view(), name="update_scores"),
  path(r'gameometer/game/<int:pk>/score_chart', views.DisplayGameScoreChartView.as_view(), name="score_chart"),
  path(r'gameometer/game/<int:pk>/rating_breakdown', views.DisplayGameRatingBreakdownView.as_view(), name="rating_breakdown"),
  #used to update the information for a specific review.
  path(r'gameometer/review/<int:pk>/update_review', views.UpdateReviewInfoView.as_view(), name="update_review"),
  path(r'gameometer/instant_search',views.instant_search, name="instant_search"),
  #used to display games with a specific tag.
  path(r'gameometer/tag/<int:pk>', views.ShowTagPageView.as_view(), name="tag_page"),
  #used to display the chart of tagged games over time.
  path(r'gameometer/tag/<int:pk>/tag_chart',views.ShowTagChartView.as_view(), name="tag_chart"),
  #used to display the list of publications with profiles on the website.
  path(r'gameometer/pub_list',views.ShowPublicationsListView.as_view(),name="pub_list"),
  #used to display the information for an individual publication.
  path(r'gameometer/pub_info/<int:pk>',views.ShowPublicationInfoView.as_view(),name="pub_info"),

  #authentication URLS
  path('login/', auth_views.LoginView.as_view(template_name='newGameoMeter/login.html'), name='login'),
  path('logout/', auth_views.LogoutView.as_view(template_name='newGameoMeter/logged_out.html'), name='logout'),
]