from django import forms
from .models import *

class UpdateGameScoresForm(forms.ModelForm):
  '''
  A form to update the details for a given game.
  '''
  #Stores the attributes for the given game.
  class Meta:
    model = GameScores
    fields = ['mock_mc', 'all_percent', 'all_rating', 'tc_percent', 'tc_rating', 'user_percent', 'user_rating', 'critics_consensus']


