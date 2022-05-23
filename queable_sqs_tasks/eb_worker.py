# -*- coding: utf-8 -*-

#
# ElasticBeanstalk worker support
# in addition to calling all the tasks from this entry point,
# you need to create and plug an SQS queue to the EB environment
#
import logging
import inspect
import apps
import uuid
import datetime
import json
import traceback

from django.conf import settings
from django.http import Http404

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema

from apps.tasks import QueueableTask


logger = logging.getLogger(__name__)

'''
    Tasks must be located as a child of apps folder, in its own class.
    E.g. apps.campaigns.tasks
'''


def get_queueable_tasks() -> dict:
    logger.info("[trace] apps/tasks/eb_worker.py: get_queueable_tasks()")

    tasks = {}
    # inspect modules from the apps module
    for name, obj in inspect.getmembers(apps):
        if inspect.ismodule(obj):
            # keep only the QueueableTask sub-classes
            for class_name, class_ref in inspect.getmembers(obj):
                # check if class is QueueableTask and subclass of QueueableTask
                if inspect.isclass(class_ref) and issubclass(class_ref, QueueableTask):
                    try:
                        action = class_ref().action_name()
                        tasks[action] = class_ref
                    except AttributeError:
                        # we ignore classes that don't have the action_name()
                        pass
    return tasks


@swagger_auto_schema(method='post', auto_schema=None)
@api_view(['POST'])
def eb_index(request):
    task_id = uuid.uuid4()
    now = datetime.datetime.now()
    logger.info("[SQS-pull: {}, {}] apps/tasks/eb_worker.py: eb_index(request)".format(task_id, now))

    if settings.QUEUE_TYPE != 'sqs':
        return Http404("Host configuration does not authorize this endpoint.")

    try:
        body = request.body.decode('utf-8')
        payload = json.loads(body)

        action = payload.get('action')
        tasks = get_queueable_tasks()

        logger.info("[begin-task: {uuid}, {now}] {action}: payload = {payload}".format(
            uuid=task_id, now=now, action=action, payload=body))

        task = tasks[action]()
        task.decode_args_and_run(payload)

        now = datetime.datetime.now()
        logger.info("[end-task: {uuid}, {now}] {action}: payload = {payload}".format(
            uuid=task_id, now=now, action=action, payload=body))

    except Exception as error:
        logger.error("{}: Failed to handle sqs task. Error {}, {}".format(now, error, body))
        logger.error("{}: {}".format(now, traceback.format_exc()))
        return Response("Task could not be processed.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(data={}, status=status.HTTP_200_OK)
