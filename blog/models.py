from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse



class Post(models.Model):
    content = models.TextField(max_length=1000)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    likes= models.IntegerField(default=0)
    dislikes= models.IntegerField(default=0)
    latitude = models.FloatField(max_length=140, default=0)
    longitude = models.FloatField(max_length=140, default=0)
    header_image = models.ImageField(null= True, blank=True, upload_to='gallery/')
    estado = models.TextField(max_length=10, default=0)

    def __str__(self):
        return self.content[:]

    @property
    def number_of_comments(self):
        return Comment.objects.filter(post_connected=self).count()

class Reflejado(models.Model):
    content = models.TextField(max_length=1000)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    likes= models.IntegerField(default=0)
    dislikes= models.IntegerField(default=0)
    latitude = models.FloatField(max_length=140, default=0)
    longitude = models.FloatField(max_length=140, default=0)
    header_image = models.ImageField(null= True, blank=True, upload_to='gallery/')
    mexico_states = models.TextField(max_length=1000, default=0)

    def __str__(self):
        return self.content[:]

    @property
    def number_of_comments(self):
        return Comment.objects.filter(post_connected=self).count()

class Comment(models.Model):
    content = models.TextField(max_length=150)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post_connected = models.ForeignKey(Post, on_delete=models.CASCADE)


class Preference(models.Model):
    user= models.ForeignKey(User, on_delete=models.CASCADE)
    post= models.ForeignKey(Post, on_delete=models.CASCADE)
    value= models.IntegerField()
    date= models.DateTimeField(auto_now= True)

    def __str__(self):
        return str(self.user) + ':' + str(self.post) +':' + str(self.value)

    class Meta:
       unique_together = ("user", "post", "value")

class Hashtags(models.Model):
    content = models.TextField(max_length=150)
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post_connected = models.ForeignKey(Post, on_delete=models.CASCADE)
