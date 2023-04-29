from django.db import models

# Create your models here.

class Task(models.Model):
    ID = models.AutoField(primary_key=True)
    TEXT = models.CharField(max_length=1024)
    DAY = models.DateField()