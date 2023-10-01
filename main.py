# TODO: Комментарии к конфигу??
# TODO: Все для шаблона (ссылки, тексты, картинки) вынести в конфиг ?
# TODO: roleid по умолчанию 5 (студент) - вынести в конфиг
import secrets
import string
import random
from time import sleep
import gspread
from email_validator import validate_email, EmailNotValidError
import config
from email_utils import mailto
from log_config import logger
from config import set_option, get_option, check_env
from moodle_utils import call, create_user, Course

# TODO: Надо ли это тут? И надо ли это вообще?
sheets = []


# TODO: Надо ли это тут? И надо ли это вообще?
def get_spreadsheet():
    sa = gspread.service_account(
        filename=get_option('google_sheets', 'credentials_path'))
    sh = sa.open(
        get_option('google_sheets','spreadsheet_name'))
    return sh


# Load list of sheets from spreadsheet
def updateSheets():
    sh = get_spreadsheet()
    global sheets
    sheets = []
    for i in sh.worksheets():
        sheets.append(i.title)


def setup():
    if not get_option('moodle', 'url'):
        set_option('moodle', 'url', input("Please enter the Moodle instance URL: "))

    if not get_option('moodle', 'endpoint'):
        set_option('moodle', 'endpoint', input(
            f"Please enter the Moodle instance endpoint (press Enter for default: "
            f"{get_option('moodle', 'default_endpoint')}): ") or get_option('moodle', 'default_endpoint'))

    check_env()

    if not get_option('moodle', 'student_role_id'):
        set_option('moodle', 'student_role_id', input("Please enter the Moodle student role id: "))

    if not get_option('moodle', 'force_password_change'):
        if input("Do you want to force password change on first login? (y=yes): ") == "y":
            set_option('moodle', 'force_password_change', "1")
        else:
            set_option('moodle', 'force_password_change', "0")

    if not get_option('moodle', 'category_id'):
        set_option('moodle', 'category_id', input(
            f"Please enter the category ID for new courses (press Enter for default: "
            f"{get_option('moodle', 'default_category_id')}): ") or get_option('moodle', 'default_category_id'))

    if not get_option('google_sheets', 'credentials_path'):
        set_option('google_sheets', 'credentials_path', input(
            f"Please enter the path to Google credentials file (press Enter for default: "
            f"{get_option('google_sheets', 'default_credentials_path')}): ") or
                   get_option('google_sheets', 'default_credentials_path'))

    if not get_option('google_sheets', 'spreadsheet_name'):
        set_option('google_sheets', 'spreadsheet_name', input("Please enter the name of the Google spreadsheet: "))

    if not get_option('email', 'credentials_path'):
        set_option('email', 'credentials_path', input(
            f"Please enter the path to Google OAuth credentials file for Gmail Auth (press Enter for default: "
            f"{get_option('email', 'default_credentials_path')}): ") or get_option('email', 'default_credentials_path'))

    if not get_option('email', 'admin_email'):
        set_option('email', 'admin_email', input("Please enter the email address of the administrator: "))

    if not get_option('email', 'subject'):
        set_option('email', 'subject', input(
            f"Please enter the subject for student's emails (press Enter for default: "
            f"{get_option('email', 'default_subject')}): ") or get_option('email', 'default_subject'))

    if not get_option('email', 'no_course_subject'):
        set_option('email', 'no_course_subject', input(
            f"Please enter the subject for administrator's emails (if there is new course) (press Enter for default: "
            f"{get_option('email', 'default_no_course_subject')}): ") or get_option('email', 'default_no_course_subject'))

    # Columns configuration - if any of the columns is empty, ask user to configure columns
    keys_to_check = ['fullname', 'course_name', 'email', 'confirm', 'login']

    if any(not get_option('columns', key) for key in keys_to_check):
        print("Let's configure columns in the Google spreadsheet. Please, wait...")
        updateSheets()
        flag = True
        i = 0  # Index of the sheet
        columns_list = None
        sh = get_spreadsheet()
        while flag:
            wks = sh.worksheet(sheets[i])  # Open the first sheet
            ws_local = wks.get_all_records()  # Get all records from the sheet
            columns_list = list(ws_local[0])  # Get the list of headers
            print(f"Below is a list of all columns for sheet {i}.\nPlease note that for the program to function "
                  f"correctly, the sheet must contain the following columns: \n* Student's full name\n* Course name\n"
                  f"* Student's email\n* Confirmation checkbox for portal registration\n* Field for displaying "
                  f"the login or errors\n\nIf this sheet has all the required columns, simply press Enter, "
                  f"and you'll be prompted to map the existing columns to the required ones.\n"
                  f"If you've selected the wrong sheet or made changes to the table to meet the requirements, "
                  f"please enter the sheet number to open (indexing starts at 0).")
            print("Columns in the sheet:")
            for index, column_name in enumerate(columns_list):
                print(f"{index + 1}. {column_name}")
            i = input("Press enter to continue or enter the sheet number: ").replace(" ", "")
            if not i:
                flag = False
                print("Ok, let's continue")
            else:
                i = int(i)
                print(f"Opening sheet {i}")
        print("Now, let's map the columns. Please enter the number of the column that corresponds to the required")
        set_option('columns', 'fullname', columns_list[int(input(f"Student's full name: ")) - 1])
        set_option('columns', 'course_name', columns_list[int(input(f"Course name: ")) - 1])
        set_option('columns', 'email', columns_list[int(input(f"Student's email: ")) - 1])
        set_option('columns', 'confirm', columns_list[int(input(f"Confirmation checkbox for portal registration: ")) - 1])
        set_option('columns', 'login', columns_list[int(input(f"Field for displaying the login or errors: ")) - 1])


setup()
#

def generate_password():
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


def newUser(name, course_name, email):
    # Check if user with this email already exists
    existing_user = call('core_user_get_users_by_field', field='email', values=[email])
    if existing_user and len(existing_user) > 0:
        userid = existing_user[0]['id']
        login = existing_user[0]['username']
        password = None
    else:
        # If user doesn't exist - create new user
        # Check if name is correct
        if (name.replace(' ', '').replace('\n', '')).isalpha() and len(
                name.split()) > 1:  # Check if name contains only letters and has more than 1 word (name and surname)
            name = name.title()  # Make name and surname title
        else:
            logger.error('Error while creating user with email %s: name is not correct (only letters and more than 1 '
                         'word)!', email)
            return ['error', '', 'ERROR - name is not correct (only letters and more than 1 word)!']

        # Check if email is correct
        try:
            validate_email(email)
        except EmailNotValidError as e:
            logger.error('Incorrect email - %s: %s', email, e)
            return ['error', '', 'ERROR - incorrect email!']

        # Login generation
        """
        In our case we have format of login: first letter of name + '_' + lastname + number (if login is not unique)
        For Example: John Smith - j_smith, j_smith1, j_smith2, etc.
        """
        original_login = name.split(' ')[1][0].lower() + '_' + name.split(' ')[0].lower()
        max_attempts = int(get_option('config', 'max_login_generation_attempts'))
        login = original_login
        # Try to generate unique login max_attempts times. Every time we increase number in login
        for attempt in range(max_attempts):
            response = call('core_user_get_users_by_field', field='username', values=[login])

            # If user with such login is not found, we can use this login
            if not response:
                break

            # If user with such login is found, we need to generate another one
            login = original_login+str(attempt + 1)
        else:
            logger.error('Failed to generate a unique login after %s attempts.', max_attempts)

        # Create new user
        firstname = name.split()[1]
        lastname = name.split()[0]
        password = generate_password()
        # Register user
        try:
            userid = create_user(firstname=firstname, lastname=lastname, email=email, username=login, password=password)
        except Exception as e:
            logger.error('Error while creating user with email %s: %s', email, e)
            return ['error', '', 'ERROR - there is problem while user registration']

    # Check course name
    if len(course_name) > 100:
        logger.error('Course name is too long: %s', course_name)
        return ['error', '',
                'THE COURSE NAME IS TOO LONG.']

    # Check if course exists
    course = call('core_course_get_courses_by_field', field='shortname', value=course_name)['courses']
    if course and len(course) > 0:
        courseid = course[0]['id']
    else:
        # If course doesn't exist - create new course
        try:
            new_course = Course(fullname=course_name, shortname=course_name,
                                categoryid=config.category_id)
            new_course.create()
            logger.info('New course created: %s', course_name)
            courseid = call('core_course_get_courses_by_field', field='shortname', value=course_name)['courses'][0]['id']
            try:
                mailto(course=course_name)  # Send email to administrator about new course
            except Exception as e:
                logger.error('Error while sending email to administrator about new course: %s', e)
        except Exception as e:
            logger.error('Error while creating course %s: %s', course_name, e)
            return ['error', '', 'ERROR - there is problem while creating course']

    # Enrol user to the course
    try:
        # Enrol user to the course
        call('enrol_manual_enrol_users',
             enrolments=[{'roleid': config.roleid, 'userid': userid, 'courseid': courseid}])
    except Exception as e:
        logger.error('Error while enrolling user %s to the course: %s', login, e)
    logger.info('New user registered: %s with login %s and enrolled to the course %s', name, login, course_name)

    try:
        # Send email to user
        mailto(course=course_name, name=name, login=login, password=password, email=email)
    except Exception as e:
        logger.error('Error while sending email to user: %s', e)
    return login


# Main function - check if we have new users in the table
def check_new():
    ws_local = None
    sh = get_spreadsheet()
    # Check all sheets in the spreadsheet
    for ws in sheets:
        wks = sh.worksheet(ws)
        try:
            # Copy all data from the sheet to the local variable (less requests to Google Sheets API)
            ws_local = wks.get_all_records(
                expected_headers=[config.col_name_fio, config.col_name_course, config.col_name_login, config.col_name_mail,
                                  config.col_confirm])
        except Exception as e:
            logger.error("Error while getting data from the sheet %s: %s", ws, e)

        if ws_local:  # If we have data in the sheet
            try:
                headers = wks.row_values(1)
                # Get column index of the login column
                col_index = headers.index(config.col_name_login) + 1
                for i in range(0, len(ws_local)):  # Check all rows
                    if ws_local[i][config.col_confirm] == "TRUE" \
                            and (ws_local[i][config.col_name_login] == "" or 'ERROR' in ws_local[i][config.col_name_login]):
                        # If user is confirmed to enrollment and not created or was error - create new user
                        if all([ws_local[i][config.col_name_fio], ws_local[i][config.col_name_course],
                                ws_local[i][config.col_name_mail]]):
                            # If we have all required data - create new user
                            wks.update_cell(i + 2, col_index,
                                            newUser(ws_local[i][config.col_name_fio], ws_local[i][config.col_name_course],
                                                    ws_local[i][config.col_name_mail]))
                        else:
                            logger.error("Not all required data has been filled in for row %d in sheet %s", i, ws)
                            wks.update_cell(i + 2, col_index, 'ERROR: Not all required data has been filled in')
            except Exception as e:
                if str(e).find("429") != -1:
                    logger.error("Google API - Too many requests. Pause for 20 seconds.")
                    sleep(20)
                elif str(e).find("502") != -1:
                    logger.error("Google API - Something went wrong (Bad Gateway). Pause for 30 seconds.")
                    sleep(30)
                else:
                    logger.error('Error while working with Google Sheets (list %s): %s', wks, e)
                    sleep(20)


if __name__ == "__main__":
    logger.info('Program started successfully!')


    while True:
        updateSheets()
        check_new()
        # Pause for 20 seconds to avoid too many requests to Google Sheets API
        sleep(20)
