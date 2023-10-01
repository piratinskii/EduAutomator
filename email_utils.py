import os
import ssl
import sys
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import sleep
import qrcode
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError
from retrying import retry
from log_config import logger
import base64
import config


def auth_gmail():
    """
    Authorize in Gmail API
    If token already exists - use it (path to token is in config.ini)
    Otherwise - get new token. This function displays QR code and URL for authorization
    instead of default browser authorization because we use this application on the server
    without GUI
    :return: service for working with Gmail API
    """
    # If we already have token - use it
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')

    # If we don't have token now - get them (first run or token expired)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.get_option('email', 'credentials_path'),
                ['https://www.googleapis.com/auth/gmail.send']
            )
            """
            Because we use this application on the server, we can't use browser to authorize and we use this 
            redirect_uri instead of default http://localhost:8080/ for just recieve the code and then
            manually enter it in the terminal
            """
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            auth_url, _ = flow.authorization_url(prompt='consent')

            # For convenience, we generate and show a QR code for the auth_url
            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
            qr.add_data(auth_url)
            qr.make(fit=True)
            qr.print_ascii(invert=True)

            print("\nPlease scan the above QR code or go to this URL and authorize the app:", auth_url)
            code = input("Enter the authorization code: ")
            flow.fetch_token(code=code)
            creds = flow.credentials
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        gmail_service = build('gmail', 'v1', credentials=creds)
        return gmail_service


def mailto(**kwargs):
    """
    Send email to user or admin depending on kwargs
    If you provide login - send email to user (registration if password provided, enrollment if not).
    If you don't provide login - send email to admin (no course)
    :param kwargs: Some variables for template (login, email, password, course_name etc.)
    """
    try:
        if kwargs.get('login'):  # Letters for users
            msg_to = kwargs.get('email')
            msg_subject = config.mail_subject
            if not kwargs.get('password'):
                # Template for existing users
                with open('letters/enrollment.html', encoding='UTF-8') as f:
                    letter = f.read()
            else:
                # Template for new users
                with open('letters/registration.html', encoding='UTF-8') as f:
                    letter = f.read()

        else:  # Letters for admin
            with open('letters/nocourse.html', encoding='UTF-8') as f:
                letter = f.read()
            msg_to = config.admin_email
            msg_subject = config.mail_subject_nocourse
        """
        Because we also have some variables for template not from kwargs we use additional_vars for them
        If you want to add some variables to template - add them to additional_vars and 
        to the config.ini file in the [moodle] section, like 'url' option
        """
        additional_vars = {
            'URL': config.get_option('moodle', 'url'),
        }
        combined_vars = {**kwargs, **additional_vars}
        email_content = letter.format_map(defaultdict(str, **combined_vars))
        message = create_message(msg_to, msg_subject, email_content)
        send_message(service, 'me', message)
        logger.info('Message sent to %s', msg_to)
    except Exception as e:  # If something went wrong-wrong - restart program
        logger.error('Error while sending mail: %s. Trying again', e)
        logger.info('Restarting program...')
        sleep(20)
        os.execv(sys.executable, ['python'] + sys.argv)  # Restart program


def create_message(to, subject, message_text):
    """
    Create message for sending
    :param to: To whom we send message
    :param subject: Subject of message
    :param message_text: Text of message
    :return: Raw message for sending
    """
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['subject'] = subject
    message.attach(MIMEText(message_text, 'html'))
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}


# If something went wrong while sending message, retry 3 times with 5 seconds delay
@retry(stop_max_attempt_number=3, wait_fixed=5000,
       retry_on_exception=lambda exception: isinstance(exception, HttpError))
def send_message(gmail_service, user_id, message):
    """
    Send message. This function is decorated with retry decorator, so if something went wrong while sending message,
    it will retry 3 times with 5 seconds delay before raising exception
    :param gmail_service: Gmail service (from auth_gmail function)
    :param user_id: ID of sender (usually it's "me" - sender name from Gmail API)
    :param message: RAW message for sending (from create_message function)
    :return: Message object
    """
    try:
        message = gmail_service.users().messages().send(userId=user_id, body=message).execute()
        return message
    except HttpError as e:
        logger.error('Error while sending message to %s: %s', message["to"], e)
        raise  # raise exception to retry


service = auth_gmail()
