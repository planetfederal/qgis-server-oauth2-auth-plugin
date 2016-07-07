# Load the env vars fomr .env files
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Authorization Service Provider (a suitable class must exist in filters)
# default to Twitter
OAUTH2_AUTHORIZATION_SERVICE_PROVIDER = os.environ.get('OAUTH2_AUTHORIZATION_SERVICE_PROVIDER', 'twitter')

# OAUTH2 credentials
OAUTH2_CLIENT_ID = os.environ.get('OAUTH2_CLIENT_ID')
OAUTH2_CLIENT_SECRET = os.environ.get('OAUTH2_CLIENT_SECRET')
