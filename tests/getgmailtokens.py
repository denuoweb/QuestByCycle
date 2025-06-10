from google_auth_oauthlib.flow import InstalledAppFlow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://mail.google.com/']

def get_tokens():
                                         
    redirect_uri = 'http://localhost'

                                                                           
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

                                    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )

                                   
    logger.info('Please go to this URL and authorize access:')
    logger.info(auth_url)

                                              
    code = input('Enter the authorization code: ')

                                                     
    flow.fetch_token(code=code)

                         
    creds = flow.credentials

                                         
    with open('credentials.json', 'w') as token_file:
        token_file.write(creds.to_json())

if __name__ == '__main__':
    get_tokens()

