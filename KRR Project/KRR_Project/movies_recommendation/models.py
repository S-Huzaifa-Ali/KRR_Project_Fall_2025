from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=255)
    genre = models.CharField(max_length=255, blank=True, null=True)
    director = models.CharField(max_length=255, blank=True, null=True)
    release_year = models.CharField(max_length=10, blank=True, null=True) 
    review = models.TextField(blank=True, null=True)
    predicted_emotion = models.CharField(max_length=50, blank=True, null=True)
    emotion_scores = models.TextField(blank=True, null=True) 
    
    def __str__(self):
        return self.title
