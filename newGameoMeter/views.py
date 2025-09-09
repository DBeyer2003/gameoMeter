from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
import time
import random
from datetime import timedelta, date, datetime
from . models import *
from . forms import *
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse ## NEW
#from .forms import UpdateProfileForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.db.models import Q, Case, When # new
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django import template
from django.db.models import Count
from django.db.models import FloatField
from django.db.models.functions import Cast
from . filters import *

# Create your views here.
def home_page_view(request):
  template_name = "newGameoMeter/home.html"

  context = {

  }

  return render(request,template_name,context)


class ShowAllGamesView(ListView):
  '''
  Displays a list of every game stored in the database, with the correspoding
  information for each game.
  '''
  template_name = "newGameoMeter/all_games.html"
  model = GameInfo
  context_object_name = 'games'
  #Fifty games will be displayed per page.
  paginate_by = 40

  def get_context_data(self, **kwargs):
    '''
    Provide context variables for use in template.
    '''
    # start with superclass context
    context = super().get_context_data(**kwargs)

    return context



class SearchResultsView(ListView):
    model = GameInfo
    template_name = 'newGameoMeter/search_results.html'
    context_object_name = 'games'
    paginate_by = 40

    #used for filtering games in search results.
    def get_queryset(self):  # new
        query = self.request.GET.get("q", '')
        # allows the search engine to find game titles, publishers and developers.
        games = GameInfo.objects.filter(
            Q(name__icontains=query) | Q(publishers__icontains=query) | Q(developers__icontains=query) | Q(platforms__icontains=query)
        )

        non_games = GameInfo.objects.filter(
            Q(name__icontains=query) | Q(publishers__icontains=query) | Q(developers__icontains=query) | Q(platforms__icontains=query)
        )

        

        if 'filters' in self.request.GET:
           #filter by title.
          filters= self.request.GET['filters']
          if filters == 'newest':
             games = games.order_by('-release_date')
          if filters == 'highest_critics':
             
             f_games = []
             """
             scores = GameScores.objects.order_by('-all_percent')
             for s in scores:
                s_id = s.id_number 
                f_games.append(s_id)
             
             score_ordering = Case(*[When(id_number=id, then=position) for position, id in enumerate(f_games)])
             games = games.filter(
                id_number__in=f_games
             ).order_by(score_ordering)

             non_games = non_games.exclude(
                id_number__in=f_games
             )
             games.union(non_games, all=True)
             """
             
             games_with_reviews = games.annotate(num_fresh_ratings=
                                                 Count("reviewinfo", filter=Q(reviewinfo__fresh_rotten=True))).annotate(
                                                 total_ratings=Count("reviewinfo")).annotate(
                                                 critics_rating=Cast('num_fresh_ratings',output_field=FloatField()) 
                                                   / Cast('total_ratings',output_field=FloatField())
                                                 )
                
             games = games_with_reviews.order_by('-critics_rating')
             

          if filters == 'lowest_critics':
            games_with_reviews = games.annotate(num_fresh_ratings=
                                                 Count("reviewinfo", filter=Q(reviewinfo__fresh_rotten=True))).annotate(
                                                 total_ratings=Count("reviewinfo")).annotate(
                                                 critics_rating=Cast('num_fresh_ratings',output_field=FloatField()) 
                                                   / Cast('total_ratings',output_field=FloatField())
                                                 )
                
            games = games_with_reviews.filter(total_ratings__gt=0).order_by('critics_rating')

            non_games = games_with_reviews.filter(total_ratings__lt=1)
            games.union(non_games,all=True)

          if filters == 'highest_audience':
             f_games = []
             scores = GameScores.objects.order_by('-user_percent')
             for s in scores:
                s_id = s.id_number 
                f_games.append(s_id)
             score_ordering = Case(*[When(id_number=id, then=position) for position, id in enumerate(f_games)])
             games = games.filter(
                id_number__in=f_games
             ).order_by(score_ordering)

             non_games = non_games.exclude(
                id_number__in=f_games
             )
             games.union(non_games)

          if filters == 'lowest_audience':
             f_games = []
             scores = GameScores.objects.order_by('user_percent')
             for s in scores:
                s_id = s.id_number 
                f_games.append(s_id)
             score_ordering = Case(*[When(id_number=id, then=position) for position, id in enumerate(f_games)])
             games = games.filter(
                id_number__in=f_games
             ).order_by(score_ordering)
         
             non_games = non_games.exclude(
                id_number__in=f_games
             )
             games.union(non_games)

        return games

class ShowGameDetailsView(DetailView):
   '''
   Displays the details for an individual game.
   '''
   model = GameInfo 
   template_name = 'newGameoMeter/game_details.html'
   context_object_name = 'game'

class UpdateGameScoresView(UpdateView):

  form_class = UpdateGameScoresForm
  template_name = "newGameoMeter/update_scores.html"
  model = GameScores 
  context_object_name = 'game'

  def form_valid(self,form):
    '''
    Handle the form submission to update the Game Scores.
    '''
    print(f'UpdateGameScoresView: form.cleaned_data={form.cleaned_data}')
    return super().form_valid(form)
  
  def get_success_url(self):
    '''
    Returns the URL to which we should be directed after the update.
    '''
    # get the GameScores pk (NOT the GameInfo pk).
    pk = self.kwargs.get('pk')
    # get the GameScores object.
    scores = GameScores.objects.filter(pk=pk).first()
    # get the GameInfo object.
    info = GameInfo.objects.filter(id_number=scores.id_number).first()
    #reverse to show the GameInfo page.
    return reverse('game_details',kwargs={'pk':info.pk})


class ShowGameReviewsView(DetailView):
   '''
   Used to display and filter the reviews for an individual game.
   '''
   model = GameInfo
   template_name = 'newGameoMeter/game_reviews.html' 
   context_object_name = 'game'

   #used for filtering games in search results.
   '''
   def get_queryset(self):  # new
      query = self.request.GET.get("q", '')
      return query
   '''
   def get_context_data(self, *arg,**kwargs):
      context = super(ShowGameReviewsView,self).get_context_data(*arg,**kwargs)
      game = GameInfo.objects.filter(pk=self.kwargs['pk']).first()

      if 'f-r' in self.request.GET:
         filter = self.request.GET['f-r']
         if filter == 'all':
            context.update({
               #'game_reviews': ReviewFilterSet(self.request.GET,queryset=ReviewInfo.objects.filter(id_number=game.id_number))
               'game_reviews': ReviewInfo.objects.filter(id_number=game),
            })
         if filter == 'fresh':
            context.update({
               #'game_reviews': ReviewFilterSet(self.request.GET,queryset=ReviewInfo.objects.filter(id_number=game.id_number))
               'game_reviews': ReviewInfo.objects.filter(id_number=game).filter(fresh_rotten=True),
            })
         if filter == 'rotten':
            context.update({
               #'game_reviews': ReviewFilterSet(self.request.GET,queryset=ReviewInfo.objects.filter(id_number=game.id_number))
               'game_reviews': ReviewInfo.objects.filter(id_number=game).filter(fresh_rotten=False),
            })

      else:
         context.update({
            #'game_reviews': ReviewFilterSet(self.request.GET,queryset=ReviewInfo.objects.filter(id_number=game.id_number))
            'game_reviews': ReviewFilterSet(self.request.GET, ReviewInfo.objects.filter(id_number=game),request=self.request).qs.distinct(),
         })

      return context


