from django import forms
from .models import Post, Comment
from django.db import models


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ("group", "text", "image")
        widgets = {
            "text": forms.Textarea(),
        }
        labels = {
            "group": "Группа",
            "text": "Текст",
            "image": "Изображение",
        }
        help_texts = {
            "group": "Укажите сообщество, в котором хотите опубликовать пост.",
            "text": "Напишите текст поста.",
            "image": "Загрузите изображение",
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(),
        }
        labels = {
            "text": "Комментарий",
        }
        help_texts = {
            "text": "Напишите комментарий.",
        }