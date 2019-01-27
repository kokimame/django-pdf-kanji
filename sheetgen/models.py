from django.db import models

# Create your models here.

class Generator(models.Model):
    text_field = models.TextField('Paste some text with kanji. Anything else will be ignored.',
                                  help_text="Currently, we can only process about "\
                                   "300 characters at once because of free and weak "
                                   "web hosting.")
