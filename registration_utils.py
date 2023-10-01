import random
import secrets
import string
from log_config import logger
from moodle_utils import get_user_by_field


def generate_password():
    """
    Generate a password with the following requirements:
    - 9 characters
    - 1 lowercase letter
    - 1 uppercase letter
    - 1 digit
    - 1 punctuation
    :return: generated password
    """
    length = 9  # Length of the password

    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    punctuation = secrets.choice(string.punctuation)

    remaining_length = length - 4
    remaining_characters = ''.join(
        secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(remaining_length))
    # List of generated characters
    password_characters = list(lowercase + uppercase + digit + punctuation + remaining_characters)
    # Shuffle all characters
    random.shuffle(password_characters)
    # Convert the list to string
    password = ''.join(password_characters)

    return password


def validate_name(name):
    """
    Check if the name is correct (only letters and more than 1 word - first name and last name)
    :param name: Full name of the user
    :return: Title case full name if it is correct, None otherwise
    """
    if (name.replace(' ', '').replace('\n', '')).isalpha() and len(name.split()) > 1:
        return name.title()
    logger.error('Error: name is not correct (only letters and more than 1 word)!')
    return None


def generate_unique_login(name):
    """
    Generate a unique login for a user like this:
    <first letter of the last name>_<first name><number (it login not unique)>
    :param name: full name of the user
    :return: generated login
    """
    original_login = name.split(' ')[1][0].lower() + '_' + name.split(' ')[0].lower()
    login = original_login
    attempt = 1
    while True:
        response = get_user_by_field('username', login)
        # If there is no user with such login, return it
        if not response:
            return login
        # Otherwise, add a number to the login and try again
        login = original_login + str(attempt)
        attempt += 1
