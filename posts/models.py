from django.db import models
from django.contrib.auth import get_user_model
from django import forms

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey(Group, blank=True, null=True, 
                              on_delete=models.SET_NULL, related_name="posts")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    
    def __str__(self):
        return self.text
    

    class Meta:
        ordering = ("-pub_date",)


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, 
                             related_name="comments", verbose_name="Пост")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="comments", verbose_name="Пост")
    text = models.TextField(verbose_name="Текст")
    created = models.DateTimeField(auto_now_add=True, 
                                   verbose_name="Дата публикации")
    

    class Meta:
        ordering = ("-created", )


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="following")