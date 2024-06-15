import base64
import io
import os
import pandas as pd
import pickle
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://mail.google.com/']


def gmail_authenticate(path):
    creds = None
    path_token = os.path.join(path, "token.pickle")
    if os.path.exists(path_token):
        with open(path_token, "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            path_cred = os.path.join(path, "credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(path_cred, SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open(path_token, "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def get_mail_id(service, subject):
    messages = service.users().messages().list(
        userId='me',
        labelIds=['INBOX', 'CATEGORY_PERSONAL'],
    ).execute().get('messages', [])

    for message in messages:
        headers = service.users().messages().get(
            userId='me', id=message['id']
        ).execute()['payload']['headers']

        for header in headers:
            if subject in str(header['value']):
                id = message['id']
                return id, str(header['value'])


def get_file_by_mail_id(service, subject):
    id, subject = get_mail_id(service, subject)
    message = service.users().messages().get(userId='me', id=id).execute()
    for part in message['payload']['parts']:
        if part['filename']:
            if 'data' in part['body']:
                data = part['body']['data']
            else:
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(
                    userId='me', messageId=id, id=att_id
                ).execute()
                data = att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            toread = io.BytesIO()
            toread.write(file_data)
            df = pd.read_excel(toread)
            return df, subject
