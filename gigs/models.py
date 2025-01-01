from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Gig(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=100, decimal_places=2)
    category = models.CharField(max_length=100)
    location = models.TextField()  
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, related_name='gigs', on_delete=models.CASCADE)
    number_of_raters = models.IntegerField(default=0)
    is_unlisted = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title


class GigImage(models.Model):
    gig = models.ForeignKey(Gig, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')

    def __str__(self):
        return f"Image for {self.gig.title}"
