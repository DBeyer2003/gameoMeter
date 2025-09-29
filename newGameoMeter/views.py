from ast import operator
from functools import reduce
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, JsonResponse
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
from django.urls import reverse_lazy

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

class SearchSuggestionsView(View):
   """
   Used to automatically generate suggestions that matches
   the characters a user is typing.
   """
   def get(self):
      query = self.request.GET.get('term','')
      games = GameInfo.objects.filter(name__icontains=query)[:10]
      suggestions = [game.name for game in games]
      return JsonResponse(suggestions, safe=False)

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
            Q(name__icontains=query)
        )

        non_games = GameInfo.objects.filter(
            Q(name__icontains=query)
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

   game_systems = ['PlayStation 2', 'GameCube', 'Wii', 'Xbox',
                   'PlayStation 3', 'Xbox 360',
                   'Wii U', 'PlayStation 4', 'Xbox One', 'DS',
                   '3DS', 'PC', 'PSP', 'PlayStation 5',
                   'Nintendo Switch', 'PlayStation Vita',
                   'iOS', 'iOS']

   def get_context_data(self, *arg,**kwargs):
      context = super(ShowGameDetailsView,self).get_context_data(*arg,**kwargs)
      game = GameInfo.objects.filter(pk=self.kwargs['pk']).first()

      reviews = ReviewInfo.objects.filter(id_number=game)
      #, date_published__range=(2010-1-1, 2025-12-25)
      
      #processes option to filter the review scores based on the console.
      if 'console' in self.request.GET:
         #used to recursively filter the systems that reviews have been written for.
         systems = self.request.GET.getlist('console')
         filtered_systems = Q()
         #If the All checkbox is checked, every review will be returned anyways.
         if 'All' not in systems:
            for system in systems:
               #ensures that the xbox 360 isn't included in the filter for the
               #original xbox.
               if system == 'Xbox':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'Xbox /') | Q(platform__contains = '/ Xbox')
               #ensures that the 3ds isn't included in the filter for the 
               #original ds.
               elif system == 'DS':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'DS /') | Q(platform__contains = '/ DS')
               else:
                  filtered_systems |= Q(platform__icontains = system)

            reviews = reviews.filter(filtered_systems)

         
      #processes option to filter reviews by date published.
      if 'date-range-low' in self.request.GET:
         firstDate = self.request.GET['date-range-low']
         if firstDate != '':
            print(firstDate)
            convertedDate = datetime.strptime(firstDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__gte=convertedDate)
         
      if 'date-range-high' in self.request.GET:
         lastDate = self.request.GET['date-range-high']
         if lastDate != '':
            print(lastDate)
            convertedDate = datetime.strptime(lastDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__lte=convertedDate)

      #number of reviews.
      total_reviews = len(reviews) 
      #used to calculate the percentage of thumbs_up reviews.
      thumbs_up = 0 
      #used to calculate the percentage of thumbs_down reviews.
      thumbs_down = 0
      #percentage, total.
      controlometer = 0.0
      #formula used to calculate average.
      numerator = 0
      denominator = len(reviews)*100
      average_rating = 0.0

      #case where there exists reviews.
      for review in reviews:
         #used to calculate the percentage of positive to negative
         if review.fresh_rotten == True:
            thumbs_up += 1 
            total_reviews
         if review.fresh_rotten == False:
            thumbs_down += 1
         
         #used to calculate the average rating.
         numerator += review.rating 
      
      
      if total_reviews != 0:
         #the final average rating.
         if (float(float(thumbs_up)/float(total_reviews))*100) % 1 >= 0.5: 
            controlometer = math.ceil((float(float(thumbs_up)/float(total_reviews))*100))
         else:
            controlometer = round((float(float(thumbs_up)/float(total_reviews))*100))

         #returns score as ##/10, rounded to one decimal digit.
         if float(float(numerator)/float(denominator))*100 % 1 >= 0.5:
            average_rating = math.ceil(float(float(numerator)/float(denominator))*100) / 10
         else:
            average_rating = round(float(float(numerator)/float(denominator))*10,1)
      else:
         controlometer = 0
         average_rating = 0

      #used to return a random selection of (up to three) reviews.
      random_reviews = []
      if total_reviews != 0:
         if total_reviews == 1:
            random_reviews = random.sample(list(reviews), 1)
         elif total_reviews == 2:
            random_reviews = random.sample(list(reviews), 2)
         else:
            random_reviews = random.sample(list(reviews), 3)
      
   
      #finds reviews with metacritic info for the metascore.
      reviews_with_meta = reviews.filter(metascore__gte=0,is_meta=True)
      print(len(reviews_with_meta))
      #used to calculate the metabar length.
      bar_length = 0.0
      if len(reviews_with_meta) >= 4:
         length = float(len(reviews_with_meta))
         print(length)
         bar_length = 200.0/length

      #used to calculate the colors for the metabar that will be displayed.
      meta_bars = []
      if len(reviews_with_meta) >= 4:
      #used to store/sort the metascores per review.
         
         score_list = []
         for review in reviews_with_meta:
            #print("Review looks like", review.metascore)
            score_list.append(review.metascore)
            
            score_list = sorted(score_list,reverse=True)

            red_hex = (255,0,0)
            yellow_hex = (255,255,0)
            green_hex = (0,176,80)
            color_list = []
         for value in score_list:
         
            #print(value)
            if int(value) <= 63:
               ratio = value / 63 
               r = 255
               g = int((red_hex[1]*(1-ratio))+(yellow_hex[1]*(ratio)))
               b = 0
            else:
               ratio = (value-63) / (37) 
               r = int((yellow_hex[0]*(1-ratio))+(green_hex[0]*ratio))
               g = int((yellow_hex[1]*(1-ratio))+(green_hex[1]*ratio))
               b = int((yellow_hex[2]*(1-ratio))+(green_hex[2]*ratio))
            hex_color = f'#{r:02X}{g:02X}{b:02X}'
            color_list.append(hex_color)
         #print(color_list)
         meta_bars = color_list

      #used to calculate the metascore
      uncurved_metascore = 0
      if len(reviews_with_meta) >= 4:
         print(len(reviews_with_meta))
         #calculates average rating:
         numerator = 0.0
         denominator = float(100*len(reviews_with_meta))
         for review in reviews_with_meta:
            #case where the review metascore is in the green zone (75-100)
            """"""
            numerator += review.metascore

         
         #returns score as ##/100, with metacurve attached.
         if float(float(numerator)/float(denominator))*100 % 1 >= 0.5:
            uncurved_metascore = math.ceil(float(float(numerator)/float(denominator))*100)
         else:
            uncurved_metascore = round(float(float(numerator)/float(denominator))*100)
      
      #the metascore, curved.
      curved_metascore = 0.0
      #the green case (75-100)
      if uncurved_metascore > 74:
         curved_metascore = float((float((float((float(uncurved_metascore)-74.0)/26.0)*40.0))+60.0))
      #the yellow case (50-74)
      elif uncurved_metascore <= 74 and uncurved_metascore >= 50:
         curved_metascore = float((float((float((float(uncurved_metascore)-49.0)/25.0))*21.0))+39.0)
      else:
         curved_metascore = float(float((float(uncurved_metascore)/49.0))/39.0)
      
      rounded_metascore = 0
      #rounds the curved_metascore, adds the curve.
      if curved_metascore % 1 >= 0.5:
        rounded_metascore = math.ceil(curved_metascore)
      else:
        rounded_metascore = round(curved_metascore)
      
      if game.meta_curve != None:
         rounded_metascore += game.meta_curve

      
      context.update({
         'num_fresh': thumbs_up,
         'num_rotten': thumbs_down,
         'total_reviews': total_reviews,
         'controlometer': controlometer, 
         'average_rating': average_rating,
         'random_reviews': random_reviews,
         'metascore': rounded_metascore,
         'bar_length': bar_length,
         'meta_bars': meta_bars,
      })


      return context


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

      reviews = ReviewInfo.objects.filter(id_number=game)

      #checks if there is a filter to sort between fresh-rotten reviews.
      if 'f-r' in self.request.GET:
         filter = self.request.GET['f-r']
         if filter == 'fresh':
            reviews = reviews.filter(fresh_rotten=True)
         if filter == 'rotten':
            reviews = reviews.filter(fresh_rotten=False)
      
            #processes option to filter reviews by date published.
      if 'date-range-low' in self.request.GET:
         firstDate = self.request.GET['date-range-low']
         if firstDate != '':
            print(firstDate)
            convertedDate = datetime.strptime(firstDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__gte=convertedDate)
         
      if 'date-range-high' in self.request.GET:
         lastDate = self.request.GET['date-range-high']
         if lastDate != '':
            print(lastDate)
            convertedDate = datetime.strptime(lastDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__lte=convertedDate)
      
      #processes option to filter reviews based on the console.
      if 'console' in self.request.GET:
         systems = self.request.GET.getlist('console')
         filtered_systems = Q()
         #If the All checkbox is checked, every review will be returned anyways.
         if 'All' not in systems:
            for system in systems:
               #ensures that the xbox 360 isn't included in the filter for the
               #original xbox.
               if system == 'Xbox':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'Xbox /') | Q(platform__contains = '/ Xbox')
               #ensures that the 3ds isn't included in the filter for the 
               #original ds.
               elif system == 'DS':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'DS /') | Q(platform__contains = '/ DS')
               else:
                  filtered_systems |= Q(platform__icontains = system)
            reviews = reviews.filter(filtered_systems)

      #checks if there is a filter to sort from.
      if 'date' in self.request.GET:
         filter = self.request.GET['date']
         if filter == 'latest':
            reviews = reviews.order_by("-date_published")
         if filter == 'earliest':
            reviews = reviews.order_by("date_published")
      else:
         reviews = reviews.order_by("-date_published")

      context.update({
         'game_reviews':reviews
      })


      return context



class CreateGameInfoView(LoginRequiredMixin, CreateView):
  '''A view to add information for a game that hasn't been registered yet.'''
  form_class = CreateGameInfoForm 
  template_name = 'newGameoMeter/create_game_info_form.html'

  def form_valid(self,form):

    print(f'CreateGameInfoView.form_valid(): form={form.cleaned_data}')
    print(f'CreateGameInfoView.form_valid(): self.kwargs={self.kwargs}')


    # save the status message to database
    form.save()


    # delegate work to superclass version of method
    return super().form_valid(form)
  
  def get_success_url(self):
     return reverse('all_games')


"""
Used to update information about individual games. (Like adding a poster link
or something.)
"""
class UpdateGameInfoView(LoginRequiredMixin, UpdateView):
   form_class = UpdateGameInfoForm
   template_name = 'newGameoMeter/update_game.html'
   model = GameInfo 
   context_object_name = 'game'

   def form_valid(self,form):
    '''
    Handle the form submission to update the Game Info.
    '''
    print(f'UpdateGameInfoView: form.cleaned_data={form.cleaned_data}')
    return super().form_valid(form)
  
   def get_success_url(self):
      '''
      Returns the URL to which we should be directed after the update.
      '''
      # get the GameInfo pk (NOT the GameInfo pk).
      pk = self.kwargs.get('pk')
      # get the ReviewInfo object.
      game = GameInfo.objects.filter(pk=pk).first()
      #reverse to show the GameInfo page.
      return reverse('game_details',kwargs={'pk':pk})
  

"""
Used to update information about individual reviews (e.g. change the 
fresh/rotten symbol.)
"""
class UpdateReviewInfoView(UpdateView):

  form_class = UpdateReviewInfoForm
  template_name = "newGameoMeter/update_review.html"
  model = ReviewInfo
  context_object_name = 'review'

  def form_valid(self,form):
    '''
    Handle the form submission to update the Game Scores.
    '''
    print(f'UpdateReviewInfoView: form.cleaned_data={form.cleaned_data}')
    return super().form_valid(form)
  
  def get_success_url(self):
    '''
    Returns the URL to which we should be directed after the update.
    '''
    # get the ReviewInfo pk (NOT the GameInfo pk).
    pk = self.kwargs.get('pk')
    # get the ReviewInfo object.
    scores = ReviewInfo.objects.filter(pk=pk).first()
    # get the GameInfo object.
    info = scores.id_number
    #reverse to show the GameInfo page.
    return reverse('game_details',kwargs={'pk':info.pk})