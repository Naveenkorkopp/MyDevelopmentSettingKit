# -*- coding: utf-8 -*-
import logging
import json

from django.conf import settings

logger = logging.getLogger(__name__)


class QueueableTask:
    """
        Here this is a parent object for all queuable tasks.
    """
    celery_task_function = None
    ACTION_NAME = None

    def __init__(self, immediate=False):
        # [Important] boolean variable for deciding the switching of tasks between workers.
        # if immediate = True then same worker processes the task and finishes it.
        self.immediate = immediate

        logger.debug("[ QueueableTask ] Task --> {}, Continue with same worker ?? --> {}".format(
            self.ACTION_NAME,
            self.immediate)
        )

    @classmethod
    def action_name(cls):
        return cls.ACTION_NAME

    def run(self, *args, **kwargs):
        raise NotImplementedError("Always override run method for any subclass of QueueableTask")

    def decode_args_and_run(self, payload):
        """
            Here This method decode the arguments coming from eb_worker.py
            and in return calls run method defined by child classes.
        """
        self.run(*payload['args'], **payload['kwargs'])

    def queue(self, *args, **kwargs):
        """
            Common method for Queuing the tasks to either sqs(QA,UAT,Prod) or celery(local).
        """
        log_msg = """
                QueueableTask : Task Name: {}
                                args: {}
                                kwargs: {}
            """.format(self.ACTION_NAME, args, kwargs)
        logger.debug(log_msg)

        result = False
        if self.immediate:
            # Process gets called by the same worker.
            self.run(*args, **kwargs)
            result = True
        else:
            # Process is passed to queue which will be handled by another worker.
            if settings.QUEUE_TYPE == 'sqs':
                payload = {
                    'action': self.ACTION_NAME,  # mandatory, used to ID this task in eb_worker.py
                    'args': args,
                    'kwargs': kwargs
                }
                task = json.dumps(payload)

                from apps.tasks.sqs import submit_to_sqs
                result = submit_to_sqs(task)
                logger.debug("Submitted task to SQS: {}".format(task))

                if not result:
                    logging.warn('Failed to submit SQS message: {}'.format(self.ACTION_NAME))
            else:
                try:
                    self.celery_task_function.delay(*args, **kwargs)
                except Exception as e:
                    logger.error('Celery Error {}'.format(e))
                else:
                    result = True
        return result
