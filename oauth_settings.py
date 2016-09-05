# Load the env vars fomr .env files
import os
try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    raise Exception("Please install the required Python packages in REQUIREMENTS.txt")

# Authorization Service Provider (a suitable class must exist in filters)
# default to Twitter
OAUTH2_AUTHORIZATION_SERVICE_PROVIDER = os.environ.get('OAUTH2_AUTHORIZATION_SERVICE_PROVIDER', 'twitter')

# OAUTH2 credentials
OAUTH2_CLIENT_ID = os.environ.get('OAUTH2_CLIENT_ID')
OAUTH2_CLIENT_SECRET = os.environ.get('OAUTH2_CLIENT_SECRET')
OAUTH2_AUTHENTICATE_URL = os.environ.get('OAUTH2_AUTHENTICATE_URL')
OAUTH2_ACCESS_TOKEN_URL = os.environ.get('OAUTH2_ACCESS_TOKEN_URL')
OAUTH2_SCOPE = os.environ.get('OAUTH2_SCOPE')
# This is optional and provider-dependant
OAUTH2_VERIFY_URL = os.environ.get('OAUTH2_VERIFY_URL', False)
