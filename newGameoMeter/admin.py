from django.contrib import admin

# Register your models here.
from .models import *
admin.site.register(ReviewInfo)
admin.site.register(GameScores)
admin.site.register(MetaBars)
admin.site.register(GameInfo)