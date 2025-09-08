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



class GameScores(models.Model):
  '''
  Stores the fake Tomatometer information for each game, as
  well as an ID that will be used to refer to info about the game.
  '''
  id_number = models.IntegerField(blank=False)
  title = models.TextField(blank=False)
  mock_mc = models.FloatField(blank=True)
  all_percent = models.FloatField(blank=True)
  all_rating = models.TextField(blank=True)
  tc_percent = models.FloatField(blank=True)
  tc_rating = models.TextField(blank=True)
  user_percent = models.FloatField(blank=True)
  user_rating = models.TextField(blank=True)
  critics_consensus = models.TextField(blank=True, null=True, max_length=100000)

  # numbers to determine symbol for accompanying ratings.
  all_symbol = models.FloatField(blank=True)
  tc_symbol = models.FloatField(blank=True)
  user_symbol = models.FloatField(blank=True)

  def __str__(self):
    return f'The video game {self.title} is score-ready with ID {self.id_number}.'
  
class MetaBars(models.Model):
  """
  Stores the information for the Metascores that will be used to create color bars
  representing the metascores.
  """
  id_number = models.IntegerField(blank=False)
  score_list = models.JSONField(blank=False)

  def __str__(self):
    return f'The id number {self.id_number} has a list of metascores {self.score_list}.'

class GameInfo(models.Model):
  '''
  Stores the Rawg Information for each game, as well as an ID that will be 
  used to refer to info about the game.
  '''
  id_number = models.IntegerField(blank=True, null=True)
  slug = models.TextField(blank=False, null=True)
  name = models.TextField(blank=True, null=True)
  release_date = models.DateField(blank=True, null=True)
  tba = models.BooleanField(blank=True, null=True)
  website = models.URLField(blank=True, null=True)
  platforms = models.TextField(blank=True, null=True)
  developers = models.TextField(blank=True, null=True)
  genres = models.TextField(blank=True, null=True)
  publishers = models.TextField(blank=True, null=True)
  esrb_rating = models.TextField(blank=True, null=True)
  poster_link = models.URLField(blank=True, null=True)
  critics_score = models.TextField(blank=True, null=True)


  #used to calculate the game scores scrated from Metacritic.
  def game_scores(self):
    scores = GameScores.objects.filter(id_number=self.id_number)
    if len(scores) > 0:
      score = scores.first()
      if score.mock_mc is not None:
        score.mock_mc *= 100 
      if score.all_percent is not None:
        score.all_percent *= 100
        r_all = round(score.all_percent,0)
        score.all_percent = r_all
      if score.tc_percent is not None:
        score.tc_percent *= 100 
        r_tc = round(score.tc_percent,0)
        score.tc_percent = r_tc
      if score.user_percent is not None:
        score.user_percent *= 100
        r_user = round(score.user_percent,0)
        score.user_percent = r_user
      return score
    else:
      return None
  
  #calculates the thumbs_up/thumbs_down percentage for each game using the individual reviews.
  def fake_controlometer(self):
    #filters reviews by id_number.
    reviews = ReviewInfo.objects.filter(id_number=self)
    #used to calculate the percentage of thumbs_up reviews.
    thumbs_up = 0 
    total_reviews = len(reviews) 
    #case where there are no values:
    if total_reviews == 0:
      return None
    #case where there exists reviews.
    else:
      for review in reviews:
        if review.fresh_rotten == True:
          thumbs_up += 1 
      #converts to float to get percentage
      if (float(float(thumbs_up)/float(total_reviews))*100) % 1 >= 0.5: 
        return math.ceil((float(float(thumbs_up)/float(total_reviews))*100))
      else:
        return round((float(float(thumbs_up)/float(total_reviews))*100))
  
  def fresh_count(self):
  #filters reviews by id_number.
    reviews = ReviewInfo.objects.filter(id_number=self)
    #used to calculate the percentage of thumbs_up reviews.
    thumbs_up = 0 
    total_reviews = len(reviews) 
    #case where there are no values:
    if total_reviews == 0:
      return None
    #case where there exists reviews.
    else:
      for review in reviews:
        if review.fresh_rotten == True:
          thumbs_up += 1 
    return thumbs_up 
  
  def rotten_count(self):
  #filters reviews by id_number.
    reviews = ReviewInfo.objects.filter(id_number=self)
    #used to calculate the percentage of thumbs_up reviews.
    thumbs_down = 0 
    total_reviews = len(reviews) 
    #case where there are no values:
    if total_reviews == 0:
      return None
    #case where there exists reviews.
    else:
      for review in reviews:
        if review.fresh_rotten == False:
          thumbs_down += 1 
    return thumbs_down 
  
  #returns the average rating for the game, calculated from the curved review ratings.
  def curved_average(self):
    #filters reviews by id_number.
    reviews = ReviewInfo.objects.filter(id_number=self)
    #formula used to calculate average.
    numerator = 0
    denominator = len(reviews)*100
    #case where there are no values.
    if len(reviews) == 0:
      return -1
    else:
      for review in reviews:
        numerator += review.rating 

      #returns score as ##/10, rounded to one decimal digit.
      string_score = round(float(float(numerator)/float(denominator))*10,1)

      return string_score
  
  #returns all of the reviews with the game's id.
  def get_reviews(self):
    reviews = ReviewInfo.objects.filter(id_number=self).order_by('-date_published')

    if len(reviews) == 0:
      return None

    return reviews
  
  #returns the number of reviews that a game has.
  def num_reviews(self):
    return len(ReviewInfo.objects.filter(id_number=self))
    
  
  def bar_length(self):
    metabars = MetaBars.objects.filter(id_number = self.id_number)
    if len(metabars) > 0:
      length = float(len(metabars.first().score_list))
      return 200/length
  
  def meta_bars(self):
    metabars = MetaBars.objects.filter(id_number = self.id_number)
    
    if len(metabars) > 0:
      red_hex = (255,0,0)
      yellow_hex = (255,255,0)
      green_hex = (0,176,80)
      metabar = metabars.first()
      color_list = []
      for value in metabar.score_list:
        
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

      return color_list
    else:
      return None

  def __str__(self):
    return f'The video game {self.name} has been added with ID number {self.id_number}.'



class ReviewInfo(models.Model):
  '''
  Stores the information for each individual game review, identified using the 
  corresponding game's ID number.
  '''
  #id_number = models.IntegerField(blank=False)
  id_number = models.ForeignKey(GameInfo, on_delete=models.CASCADE)
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

    #checks if the link is to rottentomatoes, in which case it means that
  # there is no url link/
  def check_tomato(self):
    parsed_tomato = urlparse(self.url_link)
    if parsed_tomato.netloc == 'letterboxd.com':
      return None 
    else:
      return self.url_link


  def __str__(self):
    return f'The game with id {self.id_number} now has a review published by {self.publication} and written by {self.author}, marked {self.fresh_rotten}.'
  
  

def load_scraped_game_info():
  '''
  Load the video game information from a CSV file.
  '''

  # delete all records
  #GameInfo.objects.all().delete()

  # open the file for reading one line at a time
  filename = '/Users/DBeye/django_game/media/game_info.csv'
  # open the file for reading
  f = open(filename, encoding="utf8") 
  # discard the first line containing headers
  headers = f.readline()

  GameInfo.objects.all().delete()

  # go through the entire file one line at a time
  for line in f:
    
    try:
      #split the CSV file into fields
      fields = line.split(',')

      bool = False
      if fields[4] == "TRUE":
        bool = True

      age_rating = 'RP'
      if fields[10] != '\n':
        age_rating = fields[10]

      #GameInfo.objects.filter(id_number=fields[0]).delete()
    

      #create an instance of the GameInfo object
      result = GameInfo(
        id_number = fields[0],
        slug = fields[1],
        name = fields[2],
        release_date = fields[3],
        tba = bool,
        website = fields[5],
        platforms = fields[6],
        developers = fields[7],
        genres = fields[8],
        publishers = fields[9],
        esrb_rating = age_rating,
      )
      result.save()
    except:
      print(f"EXCEPTION OCCURED: {fields}.")

  print("Done.") 



def load_reviews():
  # open the file for reading one line at a time
  filename = "/Users/DBeye/new_django_game/review_csvs/crysis3-metacritic.csv"
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
      

      #finds and deletes any duplicate reviews
      game = GameInfo.objects.filter(id_number=fields[0]).first()

      
      #creates and saves the review info
      
      review = ReviewInfo(
        id_number = game, 
        publication = fields[1],
        author = fields[2],
        rating = fields[4],
        display_score = fields[5], 
        fresh_rotten = is_fresh,
        date_published = fields[7],
        quote = fields[8], 
        platform = fields[9], 
        url_link = fields[10],
      )
      review.save()

      print(f"game {review.id_number} with publication {review.publication} is Done and is {review.fresh_rotten}ly Fresh.")

    except IOError as e:
      print(f"EXCEPTION {e} OCCURED: {fields}.")
    

def make_metabars():
  '''
  loads metacritics bars for display.
  '''
  meta_info = pd.read_csv("/Users/DBeye/django_game/media/meta_lists.csv")

  MetaBars.objects.all().delete()
  len(meta_info)
  for i in range(0,len(meta_info)):
    game = meta_info.iloc[i].copy()
    game_id = game['id']
    game_list = game['s_lists']
    print(game_id)
    
    game_list = json.loads(game_list)
    print(type(game_list))


    results = MetaBars(
      id_number = game_id, 
      score_list = game_list
    )
    print("Results are :",results.score_list)

    results.save()


def load_scores():
  '''
  Load the video game scores from a CSV file.
  '''

  # delete all records
  GameScores.objects.all().delete()

  # open the file for reading one line at a time
  filename = '/Users/DBeye/django_game/media/game_scores.csv'
  # open the file for reading
  f = open(filename) 
  # discard the first line containing headers
  headers = f.readline()

  # go through the entire file one line at a time
  for line in f:

    try:
      #split the CSV file into fields
      fields = line.split(',')

      all = fields[3]
      #print("ALL IS "+all)
      tc = fields[5]
      #print("TC IS "+tc)

      all_pic = 5.0
      tc_pic = 5.0

      
      if float(all) >= 0.75:
        #print("CERTIFIED FRESH.")
        all_pic = 2
        tc_pic = 2
      elif float(all) <= 0.74 and float(all) >= 0.60 and float(tc) >= 0.60:
        #print("FRESH")
        all_pic = 1
        tc_pic = 1
      elif float(all) <= 0.74 and float(all) >= 0.60 and float(tc) <= 0.59:
        #print("FRESH WITH THE MASSES, NOT WITH THE ELITE")
        all_pic = 1
        tc_pic = 0
      elif float(all) <= 0.59 and float(tc) >= 0.60:
        #print("DISLIKED BY ALL EXCEPT THE ELITE")
        all_pic = 0
        tc_pic = 1
      elif float(all) <= 0.59 and float(tc) <= 0.59:
        #print("UNIVERSALLY DISLIKED")
        all_pic = 0
        tc_pic = 0
      
      user = fields[7]
      user_pic = 2.0
      if float(user) >= 0.6:
        user_pic = 1.0
      else:
        user_pic = 0.0
      

      #create an instance of the GameScores object
      result = GameScores(
        id_number = fields[0],
        title = fields[1],
        mock_mc = fields[2],
        all_percent = fields[3],
        all_rating = fields[4],
        tc_percent = fields[5],
        tc_rating = fields[6],
        user_percent = fields[7],
        user_rating = fields[8],
        all_symbol = all_pic,
        tc_symbol = tc_pic,
        user_symbol = user_pic,
        critics_consensus = fields[9],
      )
      result.save()
      #print("Result saved")

    except:
      print(f"EXCEPTION OCCURED: {fields}.")

  print("Done.") 