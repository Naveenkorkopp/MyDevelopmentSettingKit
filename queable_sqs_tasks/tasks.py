# -*- coding: utf-8 -*-
from apps.tasks import QueueableTask
from apps.tasks.celery import app as celery_app


# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
USER_UPDATE = 'user_update'


# -----------------------------------------------------------------------------
# Celery Tasks
# -----------------------------------------------------------------------------
@celery_app.task(name=USER_UPDATE)
def run_user_update(*args, **kwargs):
    UserUpdate().run(*args, **kwargs)


# -----------------------------------------------------------------------------
# Task Definitions
# -----------------------------------------------------------------------------
class UserUpdate(QueueableTask):

    celery_task_function = run_user_update
    ACTION_NAME = USER_UPDATE

    def run(self, *args, **kwargs):
        from .events import update_user_unionware_data
        update_user_unionware_data(*args, **kwargs)
