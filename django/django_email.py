import logging

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

logger = logging.getLogger(__name__)


class EmailSender:
    "Sends email using SMPT"

    def send(self, email_message):
        '''
            This method sends the email to list of to_emails provided.
        '''
        logger.info(f"[SMPT] send - message - {email_message}")

        result = None
        error = None

        try:
            if not email_message.get('to'):
                error = 'No to address provided'
            elif not email_message.get('alternatives'):
                error = 'No text content or html content provided'
            elif not settings.EMAIL_HOST_USER:
                error = 'No EMAIL HOST USER found'
            elif not settings.EMAIL_HOST_PASSWORD:
                error = 'No EMAIL HOST PASSWORD USER found'
            else:
                email = EmailMultiAlternatives(**email_message)
                result = email.send()

        except Exception as e:
            result = None
            error = e

        logger.info(f"Result ==>{result}, Error ==> {error}-------")
        return result, error
