import logging
import boto3
import re
from botocore.exceptions import (
    ClientError,
    NoRegionError,
    EndpointConnectionError,
    NoCredentialsError
)

from apps.notifications.utils import (
    SNSInvalidRegionName,
    SNSPlatformApplicationArnNotEnabled,
    SNSPlatformApplicationArnHasInvalidParams,
    SNSPlatformApplicationArnNotFound,
    SNSCredentialsNotProvided,
    SNSCredentialsInvalid
)

from apps.notifications.settings import (
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_DEFAULT_REGION,
    AWS_SNS_PLATFORM_APPLICATION_ARN_IOS,
    AWS_SNS_PLATFORM_APPLICATION_ARN_ANDROID
)

from loyalty_core_models.audit_core.models import Notification

logger = logging.getLogger(__name__)

CLIENT_VALIDATED = False
PLATFORM_ARNS_ENABLED = False


class SNS(object):
    '''
        -- Reference --
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html

            Important : https://aws.amazon.com/blogs/mobile/mobile-token-management-with-amazon-sns/
    '''
    def __init__(self):
        global CLIENT_VALIDATED  # This is to make sure the client is not validated everytime but only when server restarts.
        global PLATFORM_ARNS_ENABLED

        logger.info("[ SNS ] ------------------------------------------------->>>>CLIENT_VALIDATED {},PLATFORM_ARNS_ENABLED {} ".format(
            CLIENT_VALIDATED,
            PLATFORM_ARNS_ENABLED
        ))
        self.client = self.get_sns_client()
        if not CLIENT_VALIDATED:
            self.validate_client()
            CLIENT_VALIDATED = True

        if not PLATFORM_ARNS_ENABLED:
            if self.are_platform_application_arns_enabled():
                PLATFORM_ARNS_ENABLED = True
                self._platform_application_arn_ios = AWS_SNS_PLATFORM_APPLICATION_ARN_IOS
                self._platform_application_arn_android = AWS_SNS_PLATFORM_APPLICATION_ARN_ANDROID
            else:
                log_msg = "[ SNS ] AWS_SNS_PLATFORM_APPLICATION_ARN_IOS or AWS_SNS_PLATFORM_APPLICATION_ARN_ANDROID are not Enabled"
                raise SNSPlatformApplicationArnNotEnabled(log_msg)
        else:
            self._platform_application_arn_ios = AWS_SNS_PLATFORM_APPLICATION_ARN_IOS
            self._platform_application_arn_android = AWS_SNS_PLATFORM_APPLICATION_ARN_ANDROID

        self._endpoint_arn = None  # This varible stores the endpoint arn for this appuser.

    @property
    def endpoint_arn(self):
        return self._endpoint_arn

    @endpoint_arn.setter
    def endpoint_arn(self, value):
        self._endpoint_arn = value

    def get_sns_client(self):
        '''
            This method returns the SNS client object required to make further calls to SNS
                using AWS SNS default region taken from env variable.
        '''
        try:
            return boto3.client(
                'sns',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_DEFAULT_REGION
            )
        except ValueError as error:
            log_msg = '[ SNS ] region_name is Invalid while creating client. Error - {}'.format(error)
            logger.error(log_msg)
            raise

    def validate_client(self):
        '''
            This method validate the client object by making a simple checking call which should
            return a successful status code. If the client object has not made a correct connection
            with the AWS SNS Region provided then it raises particular errors.
        '''
        try:
            response = self.client.list_platform_applications()
        except EndpointConnectionError as error:
            log_msg = " [ SES ] region_name provided is Invalid. ERROR - {}".format(error)
            logger.error(log_msg)
            raise SNSInvalidRegionName(log_msg)
        except NoCredentialsError as error:
            log_msg = '[ SES ] AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY not provided - {error}'.format(error=error)
            logger.error(log_msg)
            raise SNSCredentialsNotProvided(log_msg)
        except ClientError as error:
            log_msg = '''Provided AWS SES credentials are Incorrect :
                            AWS_ACCESS_KEY_ID
                            AWS_SECRET_ACCESS_KEY
                            AWS_DEFAULT_REGION : Error- {}'''.format(error)
            logger.error(log_msg)
            raise SNSCredentialsInvalid(log_msg)
        else:
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            if status_code == 200:
                logger.info("[ validate_client ] SNS Client  Successfully verified with Status-{}.".format(status_code))
            else:
                logger.info("[ validate_client ] SNS Client returned with Status-{}.".format(status_code))

    def are_platform_application_arns_enabled(self):
        '''
           This method checks for whether PlatformApplicationArn are valid.
           Also checks if they are enabled in AWS SNS account.
           If AWS_SNS_PLATFORM_APPLICATION_ARN_IOS, AWS_SNS_PLATFORM_APPLICATION_ARN_ANDROID are not valid
            then raise error.
        '''
        all_platform_apps_arns = [AWS_SNS_PLATFORM_APPLICATION_ARN_IOS, AWS_SNS_PLATFORM_APPLICATION_ARN_ANDROID]

        for arn in all_platform_apps_arns:
            try:
                response = self.client.get_platform_application_attributes(
                    PlatformApplicationArn=arn
                )
            except self.client.exceptions.InvalidParameterException as error:
                log_msg = "InvalidParameterException for PlatformApplicationArn-{}. Error-{}".format(arn, error)
                logger.error(log_msg)
                raise SNSPlatformApplicationArnHasInvalidParams(log_msg)
            except self.client.exceptions.NotFoundException as error:
                log_msg = "PlatformApplicationArn-{} is not found in AWS SNS account. Error-{}".format(arn, error)
                logger.error(log_msg)
                raise SNSPlatformApplicationArnNotFound(log_msg)
            except ClientError as error:
                logger.error(error)
                raise
            else:
                if response['Attributes']['Enabled'] != 'true':
                    return False
        return True

    def create_platform_endpoint_arn(self, device_type, device_token, custom_user_data):
        '''
            This method performs the first required call before publishing the message.
            It creates the TargetArn or EndpointArn which is required for publish call.
            NOTE :  The CreatePlatformEndpoint action is idempotent,
                    so if the requester already owns an endpoint with the same device token and attributes,
                    that endpoint's ARN is returned without creating a new endpoint.
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns.html#SNS.Client.create_platform_endpoint
        '''
        if device_type == Notification.ANDROID:
            platform_application_arn = self._platform_application_arn_android
        elif device_type == Notification.IOS:
            platform_application_arn = self._platform_application_arn_ios

        endpointArn = None
        try:
            response = self.client.create_platform_endpoint(
                PlatformApplicationArn=platform_application_arn,  # This attribute is created platform for SNS in AWS
                Token=device_token,
                CustomUserData=custom_user_data
            )
            endpointArn = response.get('EndpointArn')
        except self.client.exceptions.InvalidParameterException as error:
            # Here some attributes like token or Enabled doesn't match the existing endpoint.
            message = error.response['Error']['Message']
            match = re.search("Token Reason: Endpoint (arn:aws:sns[^ ]+) already exists with the same Token, but different attributes", message)
            if match:
                endpointArn = match.group(1)
            else:
                raise

        # Whether its a success or the failure store the endpointArn by calling the setter method.
        self.endpoint_arn = endpointArn
        return endpointArn

    def _get_endpoint_attributes(self, endpointArn):
        # This method returns the Attributes stored for the customer endpointArn
        response = self.client.get_endpoint_attributes(
            EndpointArn=endpointArn
        )
        return response.get('Attributes')

    def _set_endpoint_attributes(self, endpointArn, token):
        # This method updates the new attributes for endpointArn
        self.client.set_endpoint_attributes(
            EndpointArn=endpointArn,
            Attributes={
                'Token': token,
                'Enabled': 'true'
            }
        )

    def registerWithSNS(self, device_type, device_token, custom_user_data):
        '''
        This method registers the user for platform application ARN using their device Token as follows:
            1. If such a PlatformEndpoint already exists, doesn’t create anything;
                returns the ARN of the already existing PlatformEndpoint.
            2. If a PlatformEndpoint with the same token, but different attributes already exists,
                doesn’t create anything; also does not return anything but throws an exception.
            3. If such a PlatformEndpoint does not exist, creates it and returns the ARN of that newly created PlatformEndpoint.
            4. If PlatformEndpoint needed any updates for attributes then set the new attributes for new token.

            Refer : https://aws.amazon.com/blogs/mobile/mobile-token-management-with-amazon-sns
        '''
        endpointArn = self.endpoint_arn  # calling the getter method
        updateNeeded = False
        createNeeded = endpointArn is None

        if createNeeded:
            # No endpoint ARN is stored; need to call CreateEndpoint
            endpointArn = self.create_platform_endpoint_arn(device_type, device_token, custom_user_data)
            createNeeded = False

        try:
            # Here we confirm for the attributes if the existing endpointArn is matching the latest Token and Enabled ?
            endpointArn_attributes = self._get_endpoint_attributes(endpointArn)

            updateNeeded = not endpointArn_attributes.get('Token') == device_token or \
                not endpointArn_attributes.get('Enabled').lower() == 'true'
        except self.client.exceptions.NotFoundException:
            # we had a stored ARN, but the endpoint associated with it
            # disappeared. Recreate it.
            createNeeded = True

        if createNeeded:
            self.create_platform_endpoint_arn(device_type, device_token, custom_user_data)

        if updateNeeded:
            self._set_endpoint_attributes(endpointArn, device_token)

    def publish(self, device_type, device_token, custom_user_data, message):
        '''
            This method publishes the message provided to the TargetArn or EndpointArn.
        '''

        self.registerWithSNS(device_type, device_token, custom_user_data)

        logger.info("[ SNS ] publish - {} to customer - {}".format(message, custom_user_data))

        response = self.client.publish(
            TargetArn=self.endpoint_arn,  # This attribute is returned from getter method for _endpoint_arn
            MessageStructure='json',
            Message=message
        )

        if response['MessageId']:
            logger.info("Push Notification Sent...")
            return True
        return False
