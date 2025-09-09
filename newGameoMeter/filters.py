from django_filters import *

from .models import *


class ReviewFilterSet(FilterSet):
    fresh_rotten = CharFilter(label="fresh_rotten")

    class Meta:
        model = ReviewInfo
        fields = {
            'fresh_rotten': ['exact'],
        }