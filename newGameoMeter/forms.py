from django import forms
from .models import *

class CreateGameInfoForm(forms.ModelForm):
  '''A form to add a game into the game registry.'''
  id_number = forms.IntegerField(label="ID Number", required=True)
  slug = forms.CharField(label="Slug", required=True)
  name = forms.CharField(label="Name", required=True)
  release_date = forms.DateField(label="Release Date", required=True)
  tba = forms.BooleanField(label="TBA", required=False)
  website = forms.URLField(label="Website", required=False)
  platforms = forms.CharField(label="Platforms", required=True)
  developers = forms.CharField(label="Developers", required=True)
  genres = forms.CharField(label="Genres", required=True)
  publishers = forms.CharField(label="Publishers", required=True)
  esrb_rating = forms.CharField(label="ESRB Rating", required=True)
  poster_link = forms.URLField(label="Poster Link", required=False)
  critics_score = forms.CharField(label="Critics Score", required=False)

  #Stores the attributes for the given game.
  class Meta:
    model = GameInfo
    fields = ['id_number', 'slug', 'name', 'release_date', 'tba', 'website', 'platforms', 
              'developers', 'genres', 'publishers', 'esrb_rating', 'poster_link', 'critics_score']


class UpdateGameInfoForm(forms.ModelForm):
  '''A form to update/edit info for individual games.'''
    #Stores the attributes for the given game.
  class Meta:
    model = GameInfo
    fields = ['id_number', 'slug', 'name', 'release_date', 'tba', 'website', 'platforms', 
              'developers', 'genres', 'publishers', 'esrb_rating', 'poster_link', 'critics_score']


class UpdateGameScoresForm(forms.ModelForm):
  '''
  A form to update the details for a given game.
  '''
  #Stores the attributes for the given game.
  class Meta:
    model = GameScores
    fields = ['mock_mc', 'all_percent', 'all_rating', 'tc_percent', 'tc_rating', 'user_percent', 'user_rating', 'critics_consensus']


class UpdateReviewInfoForm(forms.ModelForm):
  '''
  A form to update the details for a given game.
  '''
  #Stores the attributes for the given game.
  class Meta:
    model = ReviewInfo
    fields = ['id_number', 'publication','author', 'rating','display_score','fresh_rotten','date_published','quote','platform','url_link']


