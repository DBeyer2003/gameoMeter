from ast import operator
from functools import reduce
import re
from django.shortcuts import render
from django.core.cache import cache

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
from itertools import chain
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.db.models import Q, Case, When # new
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django import template
from django.db.models import Count, FloatField
from django.db.models.functions import Cast
from . filters import *
from django.urls import reverse_lazy
import matplotlib.pyplot as plt
import numpy as np
#used to display the score graph in the html template.
from io import BytesIO
#used to take in the bytes object.
import base64
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank

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

def instant_search(request):
   '''
   Used to automatically bring up games that match
   the user's input.
   '''
   query = request.GET.get("q", '')

   if query is not None:
      query_search = Q()
      #split the words by spaces so that the ordering doesn't matter.
      for word in query.split():
         #split up any regex; e.g. exclamation points or hyphons.
         query_search &= Q(name__icontains=word)
         
      # allows the search engine to find game titles.
      results = GameInfo.objects.annotate().filter(
            query_search
      )
   else:
      results = []
   
   return render(request,"newGameoMeter/instant_search.html", {"results": results})


#used to determine if game between 70-74% in search results is Certified Fresh or
#not, based on patterns in which reviews were added.
def is_search_cf(game):
   #number of reviews. (Order reviews from earliest to newest.)
   reviews = ReviewInfo.objects.order_by("date_published")
   total_reviews = len(reviews) 
   total_fresh = len(reviews.filter(fresh_rotten=True))
   total_rotten = len(reviews.filter(fresh_rotten=False))
   #is above 75% or below 70%, it can be assumed that the overall score is not
   #certified Fresh.
   if float(float(total_fresh)/float(total_reviews)) >= 74.5:
      return False
   elif float(float(total_fresh)/float(total_reviews)) < 69.5:
      return False 
   else:
      #used to calculate the percentage of thumbs_up reviews.
      thumbs_up = 0 
      #used to calculate the percentage of thumbs_down reviews.
      thumbs_down = 0

      #case where there exists reviews.
      for review in reviews:
         #used to calculate the percentage of positive to negative
         if review.fresh_rotten == True:
            thumbs_up += 1 
         if review.fresh_rotten == False:
            thumbs_down += 1
         
         #checks if we have enough reviews (40) to turn on the CF symbol.
         if (thumbs_up+thumbs_down) >= 40:
         #if is_cf isn't turned on yet, we'll check if we have 40 total reviews,
         # and if it >=75%. If true, then we'll turn the CF symbol on.
            if float(thumbs_up)/float(thumbs_up+thumbs_down) >= 0.745:
                  is_cf = True
            # If the cf symbol IS already on, then we'll check if we've fallen under
            # 70%. If so, then we'll turn off the CF symbol.
            if float(thumbs_up)/float(thumbs_up+thumbs_down) < 0.695:
                  is_cf = False
      return is_cf

class SearchResultsView(ListView):
    model = GameInfo
    template_name = 'newGameoMeter/search_results.html'
    context_object_name = 'games'
    #INSERT TRY-EXCEPT STATEMENT HERE.
    def get_paginate_by(self, queryset):
        return self.request.GET.get('per_page', 10)

    #used for filtering games in search results.
    def get_queryset(self):  # new
        query = self.request.GET.get("q", '')

        if query is not None:
            query_search = Q()
            #split the words by spaces so that the ordering doesn't matter.
            for word in query.split():
               #split up any regex; e.g. exclamation points or hyphons.
               query_search &= Q(name__icontains=word)
               
            # allows the search engine to find game titles.
            games = GameInfo.objects.annotate().filter(
                  query_search
            )
            
        else:
            games = GameInfo.objects.all()

        if 'filters' in self.request.GET:
           #filter by title.
          filters= self.request.GET['filters']
          if filters == 'newest':
             games = games.order_by('-release_date')
          if filters == 'highest_critics':
            games = games.filter(cached_gm__gte=0).order_by('-cached_gm')
          if filters == 'lowest_critics':
             games = games.filter(cached_gm__gte=0).order_by('cached_gm')


          if filters == 'highest_audience':
             f_games = []
             games = games.filter(cached_user__gte=0).order_by('-cached_user')

          if filters == 'lowest_audience':
             f_games = []
             games = games.filter(cached_user__gte=0).order_by('cached_user')
        
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
                   'Wii U', 'PlayStation 4', 'Xbox One',
                   '3DS', 'PC', 'PC (2011 Re-Release)', 'PSP', 'PlayStation 5',
                   'Nintendo Switch', 'Nintendo Switch 2', 'PlayStation Vita','iOS', 'Mac',
                   'PC (2004 Release)', 'Nintendo 64']

   def get_context_data(self, *arg,**kwargs):
      context = super(ShowGameDetailsView,self).get_context_data(*arg,**kwargs)
      game = GameInfo.objects.filter(pk=self.kwargs['pk']).first()

      

      reviews = ReviewInfo.objects.filter(id_number=game).order_by('date_published')

      #calculates the user review score+average rating.
      user_reviews = UserReviewInfo.objects.filter(game=game)
      #, date_published__range=(2010-1-1, 2025-12-25)
      
      #store these reviews for extra filtering later.
      modible_reviews = reviews

      #this will be used to check if any of the filters are on; it not, we will
      #modify the GameInfo's gameoMeter's and User scores so that they can
      #be quickly displayed in the search engine.
      check_filters = False
         
      #processes option to filter reviews by date published.
      if 'date-range-low' in self.request.GET:
         check_filters = True
         firstDate = self.request.GET['date-range-low']
         if firstDate != '':
            convertedDate = datetime.strptime(firstDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__gte=convertedDate)
            user_reviews = user_reviews.filter(date_published__gte=convertedDate)
         
      if 'date-range-high' in self.request.GET:
         check_filters = True
         lastDate = self.request.GET['date-range-high']
         if lastDate != '':
            convertedDate = datetime.strptime(lastDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__lte=convertedDate)
            user_reviews = user_reviews.filter(date_published__lte=convertedDate)
            #print(len(user_reviews))
      
      
      #pre-calculation to determine if the game is Certified Fresh or not. This includes
      #all reviews, not just top critics ones, which is why we're handling this case
      #before filtering out the top critics if needed. We also don't need the average
      #score, which is why we're using len() functions instead of adding manually. We'll
      #later check if the score for the filtered consoles is still >=75% for extra measure,
      #though that will be handled in the HTML file.
      
      is_cf = False
      #used to determine the dates at which the cf_symbol is displayed; this is useful for cases where the 
      #filters are turned on, such as Consoles or Top Critics.
      cf_dict = {}
      #number of reviews.
      total_reviews = len(reviews) 
      #used to calculate the percentage of thumbs_up reviews.
      thumbs_up = 0 
      #used to calculate the percentage of thumbs_down reviews.
      thumbs_down = 0

      #case where there exists reviews.
      for review in reviews:
         #used to calculate the percentage of positive to negative
         if review.fresh_rotten == True:
            thumbs_up += 1 
         if review.fresh_rotten == False:
            thumbs_down += 1
         
         #checks if we have enough reviews (40) to turn on the CF symbol.
         if (thumbs_up+thumbs_down) >= 40:
         #if is_cf isn't turned on yet, we'll check if we have 40 total reviews,
         # and if it >=75%. If true, then we'll turn the CF symbol on.
            if float(thumbs_up)/float(thumbs_up+thumbs_down) >= 0.745:
                  is_cf = True
            # If the cf symbol IS already on, then we'll check if we've fallen under
            # 70%. If so, then we'll turn off the CF symbol.
            if float(thumbs_up)/float(thumbs_up+thumbs_down) < 0.695:
                  is_cf = False
         
         
         cf_dict[review.date_published] = is_cf 
      

      #processes option to filter the review scores based on the console.
      if 'console' in self.request.GET:
         check_filters = True
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
               elif system == 'Wii':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'Wii /') | Q(platform__contains = '/ Wii')
               else:
                  filtered_systems |= Q(platform__icontains = system)

            reviews = reviews.filter(filtered_systems)
            #if the reviews for this console are significantly lower than any other system, then the Certified Fresh symbol shall be removed.
            """"""
            user_reviews = user_reviews.filter(filtered_systems)
         
            #We need to filter the reviews a second time, since the individual
            # console scores might be different..
            thumbs_up = 0 
            #used to calculate the percentage of thumbs_down reviews.
            thumbs_down = 0
            for review in reviews:
               #used to calculate the percentage of positive to negative
               if review.fresh_rotten == True:
                  thumbs_up += 1 
               if review.fresh_rotten == False:
                  thumbs_down += 1
               
               #We need to filter the CF-into a second time if the consoles are 
               #filtered.
               if (thumbs_up+thumbs_down) >= 40:
                  #Above 70% and certified fresh for all reviews.
                  if float(thumbs_up)/float(thumbs_up+thumbs_down) >= 0.695 and is_cf == True:
                     is_cf = True
                  # Below 70% with filtered consoles.
                  else:
                     is_cf = False

               cf_dict[review.date_published] = is_cf 
      
      #used to mark the top critics.
      #makes the top_critics list to filter the publications for the games' score.
      only_tc = False
      filtered_pubs = Q()
      filtered_critics = Q()
      tp_list = load_top_publications()
      tc_list = load_top_critics()
      for top_pub in tp_list:
         filtered_pubs |= Q(publication__iexact = top_pub)
      for top_c in tc_list:
         filtered_critics |= Q(author__iexact = top_c)
      #use to check if there are any top critic publications within the total critics.
      if 'critic-type' in self.request.GET:
         check_filters = True
         critic_type = self.request.GET['critic-type']
         if critic_type == 'only-tc':
            only_tc = True
            reviews = reviews.filter(filtered_pubs | filtered_critics)
      

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
         if review.fresh_rotten == False:
            thumbs_down += 1
         
         #used to calculate the average rating.
         numerator += review.rating 
         
         # If the cf symbol IS already on, then we'll check if we've fallen under
         # 70%. If so, then we'll turn off the CF symbol.
         review_date = review.date_published
         if float(thumbs_up)/float(thumbs_up+thumbs_down) < 0.695 and only_tc == False:
            is_cf = False
         else:
            is_cf = cf_dict[review_date]
      
      
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
      

      #use to check if there are any top critic publications within the total critics.
      tc_reviews = reviews.filter(filtered_critics | filtered_pubs) 
      num_tc_reviews = len(tc_reviews)
      #used to calculate the percentage of top critic thumbs_up reviews.
      tc_thumbs_up = 0 
      #used to calculate the percentage of top critic thumbs_down reviews.
      tc_thumbs_down = 0
      #top critic percentage, total.
      tc_controlometer = 0.0
      #top critic formula used to calculate average.
      tc_numerator = 0
      tc_denominator = num_tc_reviews*100
      tc_average_rating = 0.0
      #we'll only count top critic reviews if there are at least five.
      if num_tc_reviews >= 5:
         for tc_review in tc_reviews:
            #used to calculate the percentage of positive to negative for top critics.
            if tc_review.fresh_rotten == True:
               tc_thumbs_up += 1 
            if tc_review.fresh_rotten == False:
               tc_thumbs_down += 1
            
            #used to calculate the top critic average rating.
            tc_numerator += tc_review.rating 
         
         #the final top critic average rating.
         if (float(float(tc_thumbs_up)/float(num_tc_reviews))*100) % 1 >= 0.5: 
            tc_controlometer = math.ceil((float(float(tc_thumbs_up)/float(num_tc_reviews))*100))
         else:
            tc_controlometer = round((float(float(tc_thumbs_up)/float(num_tc_reviews))*100))

         #returns top critic score as ##/10, rounded to one decimal digit.
         if float(float(tc_numerator)/float(tc_denominator))*100 % 1 >= 0.5:
            tc_average_rating = math.ceil(float(float(tc_numerator)/float(tc_denominator))*100) / 10
         else:
            tc_average_rating = round(float(float(tc_numerator)/float(tc_denominator))*10,1)


      #used to return a random selection of (up to three) reviews.
      random_reviews = []
      if total_reviews != 0:
         if total_reviews == 1:
            random_reviews = random.sample(list(reviews.exclude(quote="Quotation forthcoming.")), 1)
         elif total_reviews == 2:
            random_reviews = random.sample(list(reviews.exclude(quote="Quotation forthcoming.")), 2)
         else:
            random_reviews = random.sample(list(reviews.exclude(quote="Quotation forthcoming.")), 3)
      
   
      #finds reviews with metacritic info for the metascore.
      reviews_with_meta = reviews.filter(metascore__gte=0,is_meta=True)
      
      #used to calculate the default metabar length.
      bar_length = 0.0
      if len(reviews_with_meta) >= 4:
         length = float(len(reviews_with_meta))
         bar_length = 200.0/length

      #used to calculate the colors for the metabar that will be displayed.
      meta_bars = {}
      if len(reviews_with_meta) >= 4:
      #used to store/sort the metascores per review.
         score_dict = {}
         score_list = []
         #the default RGB values for the colors.
         red_hex = (255,0,0)
         yellow_hex = (255,255,0)
         green_hex = (0,176,80)

         for review in reviews_with_meta:
            if review.metascore not in score_dict: 
               score_dict[review.metascore] = 1
            else:
               score_dict[review.metascore] += 1
            score_list.append(review.metascore)
            
            score_list = sorted(score_list,reverse=True)
         scoreKeys = list(score_dict.keys())
         scoreKeys.sort(reverse=True)
         score_dict = {k: score_dict[k] for k in scoreKeys}
         #print(score_dict)

            
         color_list = {}
         #used to check if we need to add gradient colors to our bar-list by
         #comparing the current metascore to the previous one; if they are the
         #same or only 1 point apart, we don't need to add any gradients. Otherwise
         #we will add gradients to smoothly blend the two colors together.
         last_score = -5
         last_quantity = 0
         last_hex = f''
         #last index with one of the metascores.
         #last_index = -1
         #adds index values to account for gradient bars AS WELL as the 
         #bars from the score_list.
         extra_index = 0
         #in case we are adding gradients, use this variable to get its bar length.
         extra_length = 0
         for score, quantity in score_dict.items():
            #print("SCORE HERE IS ", score, "and it appears ", quantity)
            """"""
            #the main bar that we are adding.
            if int(score) <= 63:
               ratio = score / 63 
               r = 255
               g = int((red_hex[1]*(1-ratio))+(yellow_hex[1]*(ratio)))
               b = 0
            else:
               ratio = (score-63) / (37) 
               r = int((yellow_hex[0]*(1-ratio))+(green_hex[0]*ratio))
               g = int((yellow_hex[1]*(1-ratio))+(green_hex[1]*ratio))
               b = int((yellow_hex[2]*(1-ratio))+(green_hex[2]*ratio))
            hex_color = f'#{r:02X}{g:02X}{b:02X}'

            #we're going to divide the two consecutive metabars' lengths in half
            #if there are gradients to add.
            color_list[extra_index] = {'color': hex_color, 'type':'metabar','length':(200.0*(float(quantity)/float(len(reviews_with_meta))))}
            
            
            extra_index += 1
            #last_index = extra_index
            last_score = score
            last_quantity = quantity
            last_hex = hex_color
            
         meta_bars = color_list
         #print(meta_bars)


      #used to calculate the metascore
      uncurved_metascore = 0.0
      if len(reviews_with_meta) >= 4:
         #calculates average rating:
         numerator = 0.0
         denominator = float(100*len(reviews_with_meta))
         for review in reviews_with_meta:
            #case where the review metascore is in the green zone (75-100)
            """"""
            numerator += review.metascore
         
         #returns score as ##/100, with metacurve attached.
         uncurved_metascore = float(float(numerator)/float(denominator))*100
      
      #the metascore, curved.
      curved_metascore = 0.0
      #the green case (75-100)
      if uncurved_metascore > 74:
         curved_metascore = float((float((float((float(uncurved_metascore)-74.0)/26.0)*40.0))+60.0))
      #the yellow case (50-74)
      elif uncurved_metascore <= 74 and uncurved_metascore >= 50:
         curved_metascore = float((float((float((float(uncurved_metascore)-49.0)/25.0))*21.0))+39.0)
      else:
         curved_metascore = float(float((float(uncurved_metascore)/49.0))*39.0)
      
      rounded_metascore = 0
      #rounds the curved_metascore, adds the curve.
      if curved_metascore % 1 >= 0.5:
        rounded_metascore = math.ceil(curved_metascore)
      else:
        rounded_metascore = round(curved_metascore)
      
      if game.meta_curve != None:
         rounded_metascore += game.meta_curve

      
      #check if we need to filter the user reviews by their date.
      #keeps tracks of scores and number of user reviews.
      #print(len(user_reviews))
      user_percent = 0
      user_rating = 0
      percent_numerator = 0 
      rating_numerator = 0
      user_denominator = 0
      if len(user_reviews) <= 0:
         user_percent = -5
      else:
         
         for review in user_reviews:
            #reviews from 7-10 are considered Fresh.
            if review.rating >= 7:
               percent_numerator += 1 
            #adds to calculate average rating.
            rating_numerator += review.rating 
            user_denominator += 1
            #converts to float to get percentage.
            if (float(float(percent_numerator)/float(user_denominator)) * 100) % 1 >= 0.5:
               #print(float(float(percent_numerator)/float(user_denominator)))
               user_percent = math.ceil(float(float(percent_numerator)/float(user_denominator)) * 100)
            else:
               #print(float(float(percent_numerator)/float(user_denominator)))
               user_percent = round(float(float(percent_numerator)/float(user_denominator)) * 100)
            #print("The score should be: ", float(numerator)/float(denominator))

            #converts to float to get average rating.
            if (float(float(rating_numerator)/float(user_denominator))*10) % 1 >= 0.5: 
               #print(self.name, (float(float(numerator)/float(denominator))*10))
               user_rating = math.ceil((float(float(rating_numerator)/float(user_denominator))*10))
            else:
               #print(self.name, float(float(numerator)/float(denominator))*10)
               user_rating = round((float(float(rating_numerator)/float(user_denominator))*10))
      
      #print("METASCORE UNCURVED LOOKS LIKE: ", uncurved_metascore, "based on ", denominator)

      #update the game's score info automatically (but only when)
      #no filters are applied.
      if check_filters == False:
         game.cached_gm = controlometer
         game.cached_user = user_percent
         game.save()


      #Here is where the actual caching happens.

      #First, we retrieve the cache key.
      """
      cache_key = f"game:{self.kwargs['pk']}"
      cache_game = cache.get(cache_key)
      """
      """THIS WILL BE FINISHED LATER"""
      

      context.update({
         'num_fresh': thumbs_up,
         'num_rotten': thumbs_down,
         'total_reviews': total_reviews,
         'controlometer': controlometer, 
         'average_rating': average_rating,
         'tc_num_fresh': tc_thumbs_up, 
         'tc_num_rotten': tc_thumbs_down, 
         'tc_total_reviews': num_tc_reviews,
         'tc_controlometer': tc_controlometer, 
         'tc_average_rating': tc_average_rating,
         'random_reviews': random_reviews,
         'metascore': rounded_metascore,
         'num_meta': len(reviews_with_meta),
         'bar_length': bar_length,
         'meta_bars': meta_bars,
         'is_cf': is_cf,
         'user_percent':user_percent,
         'user_rating':user_rating,
         'total_user_reviews':user_denominator,
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
         fr_filter = self.request.GET['f-r']
         if fr_filter == 'fresh':
            reviews = reviews.filter(fresh_rotten=True)
         else:
            reviews = reviews.filter(fresh_rotten=False)
      
      #use to check if there are any top critic publications within the total critics.
      if 'critic-type' in self.request.GET:
         filtered_pubs = Q()
         filtered_critics = Q()
         critic_type = self.request.GET['critic-type']
         if critic_type == 'only-tc':
            #makes the top_critics list to filter the publications for the games' score.
            tp_list = load_top_publications()
            tc_list = load_top_critics()
            for top_critic in tc_list:
               filtered_critics |= Q(author__iexact = top_critic)
            for top_pub in tp_list:
               filtered_pubs |= Q(publication__iexact = top_pub)
            reviews = reviews.filter(filtered_pubs | filtered_critics)
      
            #processes option to filter reviews by date published.
      if 'date-range-low' in self.request.GET:
         firstDate = self.request.GET['date-range-low']
         if firstDate != '':
            convertedDate = datetime.strptime(firstDate,"%Y-%m-%d").date()
            reviews = reviews.filter(date_published__gte=convertedDate)
         
      if 'date-range-high' in self.request.GET:
         lastDate = self.request.GET['date-range-high']
         if lastDate != '':
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
               elif system == 'Wii':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'Wii /') | Q(platform__contains = '/ Wii')
               else:
                  filtered_systems |= Q(platform__icontains = system)
            reviews = reviews.filter(filtered_systems)


      #Case where we order the reviews by their positivity level, which is the
      #curved hidden scores (NOT the display scores) used to calculate the 
      #displayed average score.
      if 'hidden-score' in self.request.GET:
         print("HID HERE")
         score_filter = self.request.GET.getlist('hidden-score')
         print("SCORE FILTER LOOKS LIKE: ", score_filter)
         if score_filter == 'lowest':
            print("HIGH HIGH HIGH")
            #Fresh and rotten reviews will be separated out, as the lowest "Fresh"
            #review will be marked as higher than the highest "Rotten" review.
            fresh_reviews = reviews.filter(fresh_rotten=True)
            print(len(fresh_reviews))
            rotten_reviews = reviews.filter(fresh_rotten=False)
            print("FRESH: ", len(fresh_reviews), "ROTTEN, ", len(rotten_reviews))
            
            reviews = reviews.order_by('-rating')
         else:
            print("OH NO")
            fresh_reviews = reviews.filter(fresh_rotten=True).order_by('rating')
            rotten_reviews = reviews.filter(fresh_rotten=False).order_by('rating')
            reviews = chain(rotten_reviews,fresh_reviews)
      #checks if there is a filter to sort from.
      elif 'date' in self.request.GET:
         date_filter = self.request.GET['date']
         print("DATE FILTER looks like: ", date_filter)
         if date_filter is 'latest':
            reviews = reviews.order_by('-date_published')
         if date_filter is 'earliest':
            reviews = reviews.order_by('date_published')
      else:
         reviews = reviews.order_by('-date_published')
      
      


      context.update({
         'game_reviews':reviews,
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



class UpdateReviewInfoView(UpdateView):
  """
  Used to update information about individual reviews (e.g. change the 
  fresh/rotten symbol.)
  """
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
  


class DisplayGameScoreChartView(DetailView):
   '''
   Used to display a graph of the game score(s) over time, and how it 
   evolves as more reviews are entered in. 
   '''
   model = GameInfo 
   template_name = 'newGameoMeter/score_chart.html'
   context_object_name = 'game'

   def get_context_data(self, *arg,**kwargs):
      context = super(DisplayGameScoreChartView,self).get_context_data(*arg,**kwargs)
      game = GameInfo.objects.filter(pk=self.kwargs['pk']).first()
      get_pk = self.kwargs['pk']

      reviews = ReviewInfo.objects.filter(id_number=game)

      #calculates the user review score+average rating.
      user_reviews = UserReviewInfo.objects.filter(game=game)


      #The key will be the date, and the value will be a dictionary containingthe gameoMeter, average rating,
      # metascore, and corresponding number of ratings.
      date_n_score = dict()
      #order from earliest to latest.
      ordered_reviews = reviews.order_by("date_published")

      #used to determine the dates at which the cf_symbol is displayed; this is useful for cases where the 
      #filters are turned on, such as Consoles or Top Critics.
      cf_dict = {}
      is_cf = False
      #number of reviews.
      total_reviews = len(ordered_reviews) 
      #used to calculate the percentage of thumbs_up reviews.
      thumbs_up = 0 
      #used to calculate the percentage of thumbs_down reviews.
      thumbs_down = 0

      #case where there exists reviews.
      for review in ordered_reviews:
         #used to calculate the percentage of positive to negative
         if review.fresh_rotten == True:
            thumbs_up += 1 
         if review.fresh_rotten == False:
            thumbs_down += 1
         
         #checks if we have enough reviews (40) to turn on the CF symbol.
         if (thumbs_up+thumbs_down) >= 40:
         #if is_cf isn't turned on yet, we'll check if we have 40 total reviews,
         # and if it >=75%. If true, then we'll turn the CF symbol on.
            if float(thumbs_up)/float(thumbs_up+thumbs_down) >= 0.745:
                  is_cf = True
            # If the cf symbol IS already on, then we'll check if we've fallen under
            # 70%. If so, then we'll turn off the CF symbol.
            if float(thumbs_up)/float(thumbs_up+thumbs_down) < 0.695:
                  is_cf = False
         else:
            is_cf = False
         
         
         cf_dict[review.date_published] = is_cf 


      #stores systems in a list.
      system_list = []
      
      #processes option to filter the review scores based on the console.
      if 'console' in self.request.GET:
         #used to recursively filter the systems that reviews have been written for.
         systems = self.request.GET.getlist('console')
         filtered_systems = Q()
         #If the All checkbox is checked, every review will be returned anyways.
         if 'All' not in systems:
            for system in systems:
               #store system in list for use later.
               system_list.append(system)
               #ensures that the xbox 360 isn't included in the filter for the
               #original xbox.
               if system == 'Xbox':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'Xbox /') | Q(platform__contains = '/ Xbox')
               #ensures that the 3ds isn't included in the filter for the 
               #original ds.
               elif system == 'DS':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'DS /') | Q(platform__contains = '/ DS')
               elif system == 'PC':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'PC /') | Q(platform__contains = '/ PC')
               elif system == 'Wii':
                  filtered_systems |= Q(platform__iexact = system) | Q(platform__contains = 'Wii /') | Q(platform__contains = '/ Wii')
               else:
                  filtered_systems |= Q(platform__icontains = system)
               #print(filtered_systems)

            ordered_reviews = ordered_reviews.filter(filtered_systems)
            user_reviews = user_reviews.filter(filtered_systems)

            #We need to filter the reviews a second time, since the individual
            # console scores might be different..
            thumbs_up = 0 
            #used to calculate the percentage of thumbs_down reviews.
            thumbs_down = 0
            for review in ordered_reviews:
               #used to calculate the percentage of positive to negative
               if review.fresh_rotten == True:
                  thumbs_up += 1 
               if review.fresh_rotten == False:
                  thumbs_down += 1
               
               #We need to filter the CF-into a second time if the consoles are 
               #filtered.

               #Above 70% and certified fresh for all reviews.
               if float(thumbs_up)/float(thumbs_up+thumbs_down) >= 0.695 and cf_dict[review.date_published] == True:
                  is_cf = True
               # Below 70% with filtered consoles.
               else:
                  is_cf = False

               cf_dict[review.date_published] = is_cf 
      
      #print(system_list)
      
      #used to remember the first date that a review was published.
      first_date = ordered_reviews.first().date_published
      #keeps track of the current date that the game score info will be stored in; when we hit a review with a
      #later date, we will create a key for the new date and add the information for the new score (building
      #on the information from the prior dates) to it.
      current_date = ordered_reviews.first().date_published

      #creates an empty dictionary for the current date within a nested dictionary.
      date_n_score[current_date] = {}
      #number of reviews.
      total_reviews = 0
      #used to calculate the percentage of thumbs_up reviews.
      thumbs_up = 0 
      #used to calculate the percentage of thumbs_down reviews.
      thumbs_down = 0
      #percentage, total.
      controlometer = 0
      #formula used to calculate average.
      numerator = 0
      # denominator is incremented with each new review.
      denominator = total_reviews*100
      average_rating = 0.0
      #used to calculate the metascore
      num_metareviews = 0
      meta_numerator = 0
      meta_denominator = 0
      final_metascore = 0
      #turns on the fresh-rotten-certifiedFresh symbol.
      is_cf = False

      #used to score top critics info, if available.
      tp_dict = top_publication_dict()
      tc_dict = top_critic_dict()
      tc_total_reviews = 0
      tc_thumbs_up = 0
      tc_thumbs_down = 0
      tc_controlometer = 0
      tc_numerator = 0
      tc_denominator = tc_total_reviews*100
      tc_average_rating = 0.0
      
      
      #increment through the reviews.
      for review in ordered_reviews:
         #checks if this review is the same date as the current date; if it is, we'll iterate on the 
         #score objects for said date. If not, we'll update the date.
         review_date = review.date_published

         total_reviews += 1
         #adds to the fresh-rotten values.
         if review.fresh_rotten == True:
            thumbs_up += 1
         else:
            thumbs_down += 1
         #used to calculate average rating.
         numerator += review.rating
         denominator = total_reviews*100
         
         
         #the current average rating.
         if (float(float(thumbs_up)/float(total_reviews))*100) % 1 >= 0.5: 
            controlometer = math.ceil((float(float(thumbs_up)/float(total_reviews))*100))
         else:
            controlometer = round((float(float(thumbs_up)/float(total_reviews))*100))

         #returns average score as ##/10, rounded to one decimal digit.
         if float(float(numerator)/float(denominator))*100 % 1 >= 0.5:
            average_rating = math.ceil(float(float(numerator)/float(denominator))*100) / 10
         else:
            average_rating = round(float(float(numerator)/float(denominator))*10,1)
         
         #uses the dictionary from earlier to determine if the game is currently 
         #certified Fresh or not.
         if review_date in cf_dict:
            if controlometer >= 70:
               is_cf = cf_dict[review_date]
            else:
               is_cf = False
         else:
            is_cf = False
         
         #create the top critic information.
         if review.publication in tp_dict.values() or review.author in tc_dict.values():
            tc_total_reviews += 1
            #print("FOR THE DATE ", review.date_published, "WE HAVE FOUND FOR TC ", tc_total_reviews, "WITH RECENT PUB ", review.publication)
            #adds to the fresh-rotten values.
            if review.fresh_rotten == True:
               tc_thumbs_up += 1
            else:
               tc_thumbs_down += 1
            #used to calculate average rating.
            tc_numerator += review.rating
            tc_denominator = tc_total_reviews*100

            #the current average rating.
            if (float(float(tc_thumbs_up)/float(tc_total_reviews))*100) % 1 >= 0.5: 
               tc_controlometer = math.ceil((float(float(tc_thumbs_up)/float(tc_total_reviews))*100))
            else:
               tc_controlometer = round((float(float(tc_thumbs_up)/float(tc_total_reviews))*100))

            #returns average score as ##/10, rounded to one decimal digit.
            if float(float(tc_numerator)/float(tc_denominator))*100 % 1 >= 0.5:
               tc_average_rating = math.ceil(float(float(tc_numerator)/float(tc_denominator))*100) / 10
            else:
               tc_average_rating = round(float(float(tc_numerator)/float(tc_denominator))*10,1)
         
         #used to calculate metascore.
         uncurved_metascore = 0.0
         #used to store metascores for color bars.
         score_dict = {}

         if review.is_meta == True:
            #counts the number of metareviews. (NOT JUST THE ONES WITH SCORES.)
            num_metareviews += 1
            #print("NUMBER OF METAREVIEWS SO FAR IS ", num_metareviews, " with the recent reviewer being, ", review.publication)
            # checks if metareview has score; uses it to calculate metascore if true.
            if review.metascore >= 0:  
               #add score to meta_numerator to calculate average score.
               meta_numerator += review.metascore
               #add 100 to denominator because each score is calculated out of 100.
               meta_denominator += 100
               #returns score as ##/100, with metacurve attached.
               uncurved_metascore = float(float(meta_numerator)/float(meta_denominator))*100.0
                  #print("LESSER CASE: ", meta_numerator, meta_denominator, uncurved_metascore)
               

               #used to curve metascore.
               #the metascore, curved.
               curved_metascore = 0.0
               #the green case (75-100)
               if uncurved_metascore > 74:
                  curved_metascore = float((float((float((float(uncurved_metascore)-74.0)/26.0)*40.0))+60.0))
               #the yellow case (50-74)
               elif uncurved_metascore <= 74 and uncurved_metascore >= 50:
                  curved_metascore = float((float((float((float(uncurved_metascore)-49.0)/25.0))*21.0))+39.0)
                  #print("WE ARE STILL OUT OF THE RED: ", curved_metascore)
               else:
                  
                  curved_metascore = float(float((float(uncurved_metascore)/49.0))*39.0)
                  #print("WHY ARE WE GOING UNDER? ", curved_metascore)
               
               rounded_metascore = 0
               #rounds the curved_metascore, adds the curve.
               if curved_metascore % 1 >= 0.5:
                  rounded_metascore = math.ceil(curved_metascore)
               else:
                  rounded_metascore = round(curved_metascore)
               
               final_metascore = rounded_metascore
               if game.meta_curve != None:
                  final_metascore += game.meta_curve
            #print("FOR PUBLICATION ", review.publication, " ON DATE ", review.date_published, ", METASCORE IS ", review.metascore, ", METANINATOR IS ", meta_numerator, ", DENOMINATOR IS ", meta_denominator, " AND FINAL METASCORE IS ", final_metascore)
         #case where there is nothing to add.
         else:
            final_metascore += 0

         #the case to handle the user scores.
         #check if we need to filter the user reviews by their date.
         #keeps tracks of scores and number of user reviews.
         #print(len(user_reviews))
         user_percent = 0
         user_rating = 0
         percent_numerator = 0 
         rating_numerator = 0
         user_denominator = 0

         check_user_reviews = user_reviews.filter(date_published__lte=review_date)
         if len(check_user_reviews) <= 0:
            user_percent = -5
         else: 
            for review in check_user_reviews:
               #reviews from 7-10 are considered Fresh.
               if review.rating >= 7:
                  percent_numerator += 1 
               #adds to calculate average rating.
               rating_numerator += review.rating 
               user_denominator += 1
               #converts to float to get percentage.
               if (float(float(percent_numerator)/float(user_denominator)) * 100) % 1 >= 0.5:
                  #print(float(float(percent_numerator)/float(user_denominator)))
                  user_percent = math.ceil(float(float(percent_numerator)/float(user_denominator)) * 100)
               else:
                  #print(float(float(percent_numerator)/float(user_denominator)))
                  user_percent = round(float(float(percent_numerator)/float(user_denominator)) * 100)
               #print("The score should be: ", float(numerator)/float(denominator))

               #converts to float to get average rating.
               if (float(float(rating_numerator)/float(user_denominator))*10) % 1 >= 0.5: 
                  #print(self.name, (float(float(numerator)/float(denominator))*10))
                  user_rating = math.ceil((float(float(rating_numerator)/float(user_denominator))*10))
               else:
                  #print(self.name, float(float(numerator)/float(denominator))*10)
                  user_rating = round((float(float(rating_numerator)/float(user_denominator))*10))

         #case where the current review has the same date as the prior review, and will be added to its nested dictionary.
         if current_date == review_date:
            date_n_score[current_date] = {'total_reviews':total_reviews,'fresh_reviews':thumbs_up,
                                          'rotten_reviews':thumbs_down,'controlometer':controlometer,'average_rating':average_rating,
                                          'tc_total_reviews':tc_total_reviews,'tc_fresh_reviews':tc_thumbs_up,
                                          'tc_rotten_reviews':tc_thumbs_down, 'tc_controlometer':tc_controlometer,'tc_average_rating':tc_average_rating,
                                          'metascore':final_metascore,'num_metareviews':num_metareviews,'is_cf':is_cf,
                                          'formatted_date':current_date,'system_list':system_list,
                                          'user_percent': user_percent, 'user_rating':user_rating,'total_user_ratings':user_denominator}
         #case where we create a new nested dictionary for a new date.
         else:
            #check to make sure that the prior date_n_score value is there.
            #first, we create a new dictionary for the new date within the nested dictionary,
            #which will include all of the reviews from the prior dictionary.
            date_n_score[review_date] = date_n_score[current_date]
            #Then, we set the current date to the new date.
            current_date = review_date
            #finally, we continue adding reviews to the dictionary as normal.
            date_n_score[current_date] = {'total_reviews':total_reviews,'fresh_reviews':thumbs_up,
                                          'rotten_reviews':thumbs_down,'controlometer':controlometer,'average_rating':average_rating,
                                          'tc_total_reviews':tc_total_reviews,'tc_fresh_reviews':tc_thumbs_up,
                                          'tc_rotten_reviews':tc_thumbs_down, 'tc_controlometer':tc_controlometer,'tc_average_rating':tc_average_rating,
                                          'metascore':final_metascore,'num_metareviews':num_metareviews,'is_cf':is_cf,
                                          'formatted_date':current_date,'system_list':system_list,
                                          'user_percent': user_percent, 'user_rating':user_rating,'total_user_ratings':user_denominator}
      
      # Create the visual graph.
      xReviews = [date_n_score[date]['total_reviews'] for date in date_n_score if date_n_score[date]['total_reviews'] >= 5]
      xDates = [date for date in date_n_score if date_n_score[date]['total_reviews'] >= 5]
      y = [date_n_score[date]['controlometer'] for date in date_n_score if date_n_score[date]['total_reviews'] >= 5]
      graph = get_plot(xReviews,xDates,y,cf_dict,game.name)

      tc_xReviews = [date_n_score[date]['tc_total_reviews'] for date in date_n_score if date_n_score[date]['tc_total_reviews'] >= 5]
      tc_xDates = [date for date in date_n_score if date_n_score[date]['tc_total_reviews'] >= 5]
      tc_y = [date_n_score[date]['tc_controlometer'] for date in date_n_score if date_n_score[date]['tc_total_reviews'] >= 5]
      tc_graph = get_plot(tc_xReviews,tc_xDates,tc_y,cf_dict,game.name)
      """
      plt.plot(x, y)
      plt.xlim(first_date,current_date)
      plt.ylim(0, 100)
      """

      context = {
         'date_n_score':date_n_score,
         'get_pk':get_pk,
         'game':game,
         'graph':graph,
         'tc_graph':tc_graph,
      }
      
      return context

def display_graph():
   buffer = BytesIO()
   #used to set format for buffered graph.
   plt.savefig(buffer, format='png', dpi=120)
   """"""
   #sets course at beginning of stream.
   buffer.seek(0)
   image_png = buffer.getvalue()
   #PRINT IMAGE_PNG HERE FOR DEBUGGING.
   #encode the image.
   graph = base64.b64encode(image_png)
   graph = graph.decode('utf-8')
   #free buffer memory.
   buffer.close()
   return graph

#used to display fresh, rotten and Certified Fresh symbols for
#score graph.
def getImage(path):
   return OffsetImage(plt.imread(path, format="png"), zoom=.05)

def get_plot(xReviews,xDates,y,cf_dict,name):
   #uses anti-grain geometry to visualize the chart.
   plt.switch_backend('AGG')
   #set size of figure.
   plt.figure(figsize=(9,5))
   plt.title('Gameometer Charted By Number of reviews')
   #plt.plot(x,y,marker='o',label="number of reviews")
   #makes a list of fresh/certified fresh/rotten symbols
   #based on each score.
   
   #plots the chart with Fresh, Certified Fresh or Rotten symbols
   #based on the score.

   plt.scatter(xReviews,y,alpha=0.8)
   
   #used for displaying the individual scores
   #on the chart; if the score shifts significantly
   #over time (by, like, 5% or greater) then the 
   #number will be displayed.
   current_percent = 0

   fresh_rotten_list = []
   fig, ax = plt.subplots()
   #only displays info if there is enough info to chart.
   if len(y) >= 0:
      for x0, xDate, y0 in zip(xReviews,xDates,y):
         #check if the game is certified fresh or not.
         if cf_dict[xDate] == True:
            ab = AnnotationBbox(getImage('static/images/certified-fresh.png'), (x0, y0), frameon=False)
            ax.add_artist(ab)
         #check if the game is merely fresh.
         elif y0 >= 60:
            ab = AnnotationBbox(getImage('static/images/fresh.png'), (x0, y0), frameon=False)
            ax.add_artist(ab)
         #ROTTEN CASE.
         else:
            ab = AnnotationBbox(getImage('static/images/rotten.png'), (x0, y0), frameon=False)
            ax.add_artist(ab)
         #displays percentage every 10 reviews.
         """
         if abs(y0-current_percent) >= 5:
            plt.text(x0,y0,y0,size=10)
            current_percent = y0
         """
      #add dotted line for visual clarity.
      plt.plot(xReviews,y,linestyle='dotted',color='black')

      #used to display the number of reviews on the graph.
      plt.xticks(np.arange(0,max(xReviews),10))
      #used to display the year values on the x-axis.
      #plt.xticks(np.arange(min_year,max_year,1))
      #sets the percentage range (0,100) for plot, as
      #well as the percentage locations on the graph.
      plt.yticks(np.arange(0,110,10))
      #used to display grid lines.
      plt.grid()
   else:
      #used to display the number of reviews on the graph.
      plt.xticks(np.arange(0,110,10))
      #used to display the year values on the x-axis.
      #plt.xticks(np.arange(min_year,max_year,1))
      #sets the percentage range (0,100) for plot, as
      #well as the percentage locations on the graph.
      plt.yticks(np.arange(0,110,10))
      #used to display grid lines.
      plt.grid()

   #plt.xticks(rotation=45)
   plt.xlabel('number of reviews')
   plt.ylabel('score')
   plt.title(name)
   #clean up the layout.
   plt.tight_layout()
   graph = display_graph()
   plt.close()
   return graph