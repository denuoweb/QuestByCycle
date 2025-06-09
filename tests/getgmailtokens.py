from google_auth_oauthlib.flow import InstalledAppFlow
import json

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

                                   
    print('Please go to this URL and authorize access:')
    print(auth_url)

                                              
    code = input('Enter the authorization code: ')

                                                     
    flow.fetch_token(code=code)

                         
    creds = flow.credentials

                                         
    with open('credentials.json', 'w') as token_file:
        token_file.write(creds.to_json())

if __name__ == '__main__':
    get_tokens()

