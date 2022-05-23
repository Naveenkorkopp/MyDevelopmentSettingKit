import logging
import boto3

from botocore.exceptions import (
    ClientError,
    NoRegionError,
    NoCredentialsError,
    EndpointConnectionError
)

from apps.notifications.utils import (
    EmailIdentityNotVerified,
    SESInvalidRegionName,
    SESCredentialsNotProvided,
    SESCredentialsInvalid
)

from apps.notifications.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION,
    AWS_SES_EMAIL_IDENTITY
)

logger = logging.getLogger(__name__)

CLIENT_VALIDATED = False
EMAIL_IDENTITY_VERIFIED = False


class SES(object):
    '''
        -- Reference --
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ses.html
    '''
    def __init__(self):
        global CLIENT_VALIDATED  # This is to make sure the client is not validated everytime but only when server restarts.
        global EMAIL_IDENTITY_VERIFIED

        logger.info("[ SES ] ----------------------------------------->>>>CLIENT_VALIDATED {},EMAIL_IDENTITY_VERIFIED {} ".format(
            CLIENT_VALIDATED,
            EMAIL_IDENTITY_VERIFIED
        ))
        self.client = self.get_ses_client()

        # Validate client connection and raise if connection has some problems.
        if not CLIENT_VALIDATED:
            self.validate_client()
            CLIENT_VALIDATED = True

        if not EMAIL_IDENTITY_VERIFIED:
            if self.is_email_identity_verified():
                # TODO: find out why getting this value from AWS Beanstalk doesn't work, perhaps related to the double quotes
                # self.from_email = AWS_SES_EMAIL_IDENTITY
                self.from_email = '"ParticipACTION" <no-reply@participaction.com>'
                EMAIL_IDENTITY_VERIFIED = True
            else:
                raise EmailIdentityNotVerified('AWS_SES_EMAIL_IDENTITY-{}'.format(AWS_SES_EMAIL_IDENTITY))
        else:
            # TODO: find out why getting this value from AWS Beanstalk doesn't work, perhaps related to the double quotes
            #self.from_email = AWS_SES_EMAIL_IDENTITY
            self.from_email = '"ParticipACTION" <no-reply@participaction.com>'

    def get_ses_client(self):
        '''
            This method returns the SES client object required to make further calls to SES
                using AWS SES credentials taken from env variables.
        '''
        try:
            return boto3.client(
                'ses',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_DEFAULT_REGION
            )
        except ValueError as error:
            log_msg = '[SES] region_name is Invalid while creating client. - Error-{}'.format(error)
            logger.error(log_msg)
            raise

    def validate_client(self):
        '''
            This method validate the client object by making a simple checking call which should
            return a successful status code. If the client object has not made a correct connection
            with the AWS SES Credentials or Account provided then it raises particular errors.
        '''
        try:
            response = self.client.list_identities()
            logger.info("[SES] validate_client ")
        except EndpointConnectionError as error:
            log_msg = " [ SES ] region_name provided is Invalid. ERROR - {}".format(error)
            logger.error(log_msg)
            raise SESInvalidRegionName(log_msg)
        except NoCredentialsError as error:
            log_msg = '[ SES ] AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not provided - {error}'.format(error=error)
            logger.error(log_msg)
            raise SESCredentialsNotProvided(log_msg)
        except ClientError as error:
            log_msg = '''Provided AWS SES credentials are Incorrect :
                            AWS_ACCESS_KEY_ID
                            AWS_SECRET_ACCESS_KEY
                            AWS_DEFAULT_REGION : Error- {}'''.format(error)
            logger.error(log_msg)
            raise SESCredentialsInvalid(log_msg)
        else:
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            if status_code == 200:
                logger.info("[ validate_client ] SES Client  Successfully verified with Status-{}.".format(status_code))
            else:
                logger.info("[ validate_client ] SES Client returned with Status-{}.".format(status_code))

    def get_all_verified_email_addresses(self):
        '''
            This method returns the list of all verified email addresses in AWS SES account.
        '''
        try:
            response = self.client.list_verified_email_addresses()
        except ClientError as error:
            logger.error(error)
            return []
        else:
            return response['VerifiedEmailAddresses']

    def is_email_identity_verified(self):
        '''
            This method checks weather AWS_SES_EMAIL_IDENTITY is in list of verified email
            addresses in AWS SES account.
        '''
        if AWS_SES_EMAIL_IDENTITY in self.get_all_verified_email_addresses():
            logger.info("[SES] is_email_identity_verified - True")
            return True
        else:
            logger.info("[SES] is_email_identity_verified - False")
            return False

    def send(self, destination, message):
        '''
            This method sends the email to list of to_emails provided.
        '''
        logger.info("[SES] send - destination - {} , message - {}".format(destination, message))

        try:
            response = self.client.send_email(
                Source=self.from_email,
                Destination=destination,
                Message=message
            )
            if response['MessageId']:
                logger.info(" [SES] Email Sent to - {}".format(destination['ToAddresses']))
                return True
        except Exception as error:
            logger.error('[SES] Email Send - Error-{}'.format(error))

        return False
