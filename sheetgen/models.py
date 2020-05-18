from django.db import models

# Create your models here.

class Generator(models.Model):
    text_field = models.TextField('Paste text with Kanji',
                                  help_text="Currently, we can only process about 300 characters at once")
