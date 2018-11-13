# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField

# Create your models here.
class Member(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class MemberFileData(models.Model):
    user = models.ForeignKey('Member',on_delete=models.CASCADE)
    data = JSONField()
