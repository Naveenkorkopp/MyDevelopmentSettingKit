import logging
import copy

from django.conf import settings

from pyfcm import FCMNotification
from pyfcm.errors import (
    InvalidDataError,
    FCMError,
    AuthenticationError,
    FCMNotRegisteredError,
    FCMServerError,
    InternalPackageError,
    RetryAfterException
)

logger = logging.getLogger(__name__)


class FCMNotifier:
    '''
    Firebase cloud messaging service.
    '''

    # List of named args that pyfcm accepts
    FIREBASE_SERVER_ARGS = (
        'registration_id',
        'registration_ids',
        'message_body',
        'message_title',
        'message_icon',
        'sound',
        'condition',
        'collapse_key',
        'delay_while_idle',
        'time_to_live',
        'restricted_package_name',
        'low_priority',
        'dry_run',
        'data_message',
        'click_action',
        'badge',
        'color',
        'tag',
        'body_loc_key',
        'body_loc_args',
        'title_loc_key',
        'title_loc_args',
        'content_available',
        'android_channel_id',
        'timeout',
        'extra_notification_kwargs',
        'extra_kwargs'
    )

    def __init__(self):
        self.__push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)

    @classmethod
    def chunks(cls, registration_ids_list, rate_limit):
        """Yield successive rate_limit-sized chunks from registration_ids_list."""
        for index in range(0, len(registration_ids_list), rate_limit):
            yield registration_ids_list[index:index + rate_limit]

    @classmethod
    def throttle_notifications(cls, registration_ids):
        '''
        This method is used for throttling messages if registration_ids are more than 1000.
        (As FCM has limit of 1000 per bulk send)
        '''
        return list(cls.chunks(registration_ids, 900))  # keep rate_limit to 900

    def send(self, **kwargs):
        '''
        This method is used for pushing messages to Firebase for single device
        or multiple device depending on kwargs.
        '''
        response = None
        try:
            # Create an object to collect extra data to be used by client
            # This object should not contain the fields used by the fcm library
            extra_notification_kwargs = copy.copy(kwargs)

            for item in FCMNotifier.FIREBASE_SERVER_ARGS:
                extra_notification_kwargs.pop(item, None)

            if all(name in kwargs for name in ['registration_id', 'message_title', 'message_body']):

                response = self.__notify_single_device(
                    kwargs['registration_id'],
                    kwargs['message_title'],
                    kwargs['message_body'],
                    kwargs.get('data_message', None),
                    extra_notification_kwargs,
                )
            elif all(name in kwargs for name in ['registration_ids', 'message_title', 'message_body']):

                # Throttle and send
                for registration_ids in self.throttle_notifications(kwargs['registration_ids']):
                    response = self.__notify_multiple_devices(
                        registration_ids,
                        kwargs['message_title'],
                        kwargs['message_body'],
                        kwargs.get('data_message', None),
                        extra_notification_kwargs
                    )
        except (InvalidDataError, FCMError, AuthenticationError, FCMNotRegisteredError,
                FCMServerError, InternalPackageError, RetryAfterException) as error:
            logger.error(error)

        return response

    def __notify_single_device(
        self,
        reg_id,
        msg_title,
        msg_body,
        data_message,
        extra_notification_kwargs={},
    ):
        '''
        Send push notification to a single device.
        '''
        return self.__push_service.notify_single_device(
            registration_id=reg_id,
            message_title=msg_title,
            message_body=msg_body,
            data_message=data_message,
            extra_notification_kwargs=extra_notification_kwargs
        )

    def __notify_multiple_devices(
        self,
        reg_ids,
        msg_title,
        msg_body,
        data_message,
        extra_notification_kwargs={},
    ):
        '''
        Sends push notification to multiple devices, can send to over 1000 devices at once.
        '''
        return self.__push_service.notify_multiple_devices(
            registration_ids=reg_ids,
            message_title=msg_title,
            message_body=msg_body,
            data_message=data_message,
            extra_notification_kwargs=extra_notification_kwargs
        )
