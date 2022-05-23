# -*- coding: utf-8 -*-
import logging
import datetime
import boto3

from django.conf import settings

logger = logging.getLogger(__name__)


def submit_to_sqs(json_payload: str) -> bool:
    now = datetime.datetime.now()
    logger.debug("[SQS-push, {}] apps/tasks/utils.py: submit_to_sqs({})\n".format(json_payload, now))

    '''
    Submit a message into the SQS queue.
    '''
    sqs_queue_name = settings.SQS_QUEUE_NAME
    sqs_region = settings.SQS_REGION
    # Get the service resource
    sqs = boto3.resource('sqs', region_name=sqs_region)
    try:
        # Get the queue
        queue = sqs.get_queue_by_name(QueueName=sqs_queue_name)
        # Create a new message
        response = queue.send_message(MessageBody=json_payload)
        if response.get('MessageId'):
            logger.debug("SQS {}: Message ID: {}".format(sqs_queue_name, response.get('MessageId')))
            return True
    except Exception as error:
        logger.error(error)

    logger.debug("Error sending message to queue: {}, {}, {}".format(sqs_queue_name, sqs_region, json_payload))
    return False
