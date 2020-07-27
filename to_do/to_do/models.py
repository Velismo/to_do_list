from django.db import models
from django.conf import settings

class TaskList(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField()

class Task(models.Model):
    id = models.AutoField(primary_key=True)
    list = models.ForeignKey('List', on_delete=models.CASCADE) #Foreign key relation to list
    name = models.CharField(max_length=50)
    done = models.BooleanField(default=False)
    description = models.TextField()