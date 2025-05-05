from google_auth_oauthlib.flow import InstalledAppFlow
import json

SCOPES = ['https://mail.google.com/']

def get_tokens():
    # Specify the redirect URI explicitly
    redirect_uri = 'http://localhost'

    # Initialize the flow with the client secrets, scopes, and redirect URI
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',
        scopes=SCOPES,
        redirect_uri=redirect_uri
    )

    # Generate the authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent'
    )

    # Display the authorization URL
    print('Please go to this URL and authorize access:')
    print(auth_url)

    # Get the authorization code from the user
    code = input('Enter the authorization code: ')

    # Exchange the authorization code for credentials
    flow.fetch_token(code=code)

    # Get the credentials
    creds = flow.credentials

    # Save the credentials for future use
    with open('credentials.json', 'w') as token_file:
        token_file.write(creds.to_json())

if __name__ == '__main__':
    get_tokens()

