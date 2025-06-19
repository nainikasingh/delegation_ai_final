import boto3
import json
from botocore.exceptions import ClientError

# Define global variables
JWT_SECRET = None

def load_secrets(secret_name="helpdesk-chatbot-swagger", region_name="ap-south-1"):
    """Fetches secrets from AWS Secrets Manager and assigns them to global variables."""
    global JWT_SECRET

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_messages = {
            'ResourceNotFoundException': f"Secret {secret_name} not found.",
            'InvalidRequestException': f"Invalid request: {e}",
            'InvalidParameterException': f"Invalid parameters: {e}",
            'DecryptionFailure': "Secrets Manager couldn't decrypt the data.",
            'InternalServiceError': "An AWS internal service error occurred."
        }
        raise Exception(error_messages.get(error_code, str(e)))

    # Parse secrets
    secret_data = response.get('SecretString') or response.get('SecretBinary')
    secrets_dict = json.loads(secret_data) if isinstance(secret_data, str) else secret_data

    # Assign to global variables
    JWT_SECRET = secrets_dict.get("JWT_SECRET", "default_jwt_secret")

# Load secrets when imported
load_secrets()