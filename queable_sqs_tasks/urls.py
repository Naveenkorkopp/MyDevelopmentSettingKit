# -*- coding: utf-8 -*-
from django.urls import path

from apps.tasks import eb_worker

app_name = 'tasks'

urlpatterns = [
    path('', eb_worker.eb_index, name='eb_index'),
]
