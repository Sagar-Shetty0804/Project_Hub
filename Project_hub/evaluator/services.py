from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Load your credentials from the service account file
def authenticate_google_sheets():
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    credentials = Credentials.from_service_account_file(
        'evaluatorsheet-a695b628917a.json', scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=credentials)
    return service