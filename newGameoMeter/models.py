import ast
import json
import math
from urllib.parse import urlparse
from django.db import models
from django.urls import reverse ## NEW
from django.contrib.auth.models import User ## NEW
from django.db.models.signals import post_save
from django.dispatch import receiver
import pandas as pd

# Create your models here.

class ReviewInfo(models.Model):
  '''
  Stores the information for each individual game review, identified using the 
  corresponding game's ID number.
  '''
  id_number = models.IntegerField(blank=False)
  publication = models.TextField(blank=False)
  author = models.TextField(blank=False, null=True) 
  #use the curved rating rather than the MC one.
  rating = models.IntegerField(blank=False, null=True) 
  display_score = models.TextField(blank=True,null=True)
  fresh_rotten = models.BooleanField(blank=False)   
  date_published = models.DateField(blank=False)
  quote = models.TextField(blank=False)
  platform = models.TextField(blank=False)
  url_link = models.URLField(blank=True,null=True)

  def __str__(self):
    return f'The game with id {self.id_number} now has a review published by {self.publication} and written by {self.author}, marked {self.fresh_rotten}.'

def load_reviews():

  # open the file for reading one line at a time
  filename = "/Users/DBeye/django_game/review_cvs/chibi-photo.csv"
  # open the file for reading
  f = open(filename,encoding="utf8") 
  # discard the first line containing headers
  headers = f.readline()

  # go through the entire file one line at a time
  for line in f:

    try:
      #split the CSV file into fields
      fields = line.split(',')
      #determines whether review is fresh or rotten.
      is_fresh = True
      if fields[6] == 'R':
        is_fresh = False
      

      if fields[2] == "N/A":
        print("NO AUTHOR.")
      if fields[5] == "No Score":
        print("NO SCORE HERE.")
      if fields[10] == "www.rottentomatoes.com":
        print('IT"S TIME TO FREAKING TOMATOMETER.')
      

      
      #creates and saves the review info
      
      review = ReviewInfo(
        id_number = fields[0], 
        publication = fields[1],
        author = fields[2],
        rating = fields[4],
        display_score = fields[5], 
        fresh_rotten = True,
        date_published = fields[7],
        quote = fields[8], 
        platform = fields[9], 
        url_link = fields[10],
      )
      
      review.save()
      """
      
      """

      """ 
      
      """
      print(f"game {review.id_number} with publication {review.publication} is Done and is {review.fresh_rotten}ly Fresh.")

    except IOError as e:
      print(f"EXCEPTION {e} OCCURED: {fields}.")

    