from django.db import models

# Create your models here.

class Generator(models.Model):
    text_field = models.TextField('Paste some text with kanji. Anything else will be ignored.',)
