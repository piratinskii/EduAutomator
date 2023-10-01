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
from moodle_utils import call, create_user, create_course, get_user_by_field, enroll_user_to_course, get_course_by_field


def get_spreadsheet():
    sa = gspread.service_account(
        filename=get_option('google_sheets', 'credentials_path'))
    sh = sa.open(get_option('google_sheets', 'spreadsheet_name'))

    sheets_data = []
    for worksheet in sh.worksheets():
        title = worksheet.title
        data = worksheet.get_all_values()
        sheets_data.append([title, data])

    return sheets_data


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
            f"{get_option('email', 'default_no_course_subject')}): ") or get_option('email',
                                                                                    'default_no_course_subject'))

    # Columns configuration - if any of the columns is empty, ask user to configure columns
    keys_to_check = ['fullname', 'course_name', 'email', 'confirm', 'login']

    if any(not get_option('columns', key) for key in keys_to_check):
        print("Let's configure columns in the Google spreadsheet. Please, wait...")
        flag = True
        i = 0  # Index of the sheet
        columns_list = None
        sheets_data = get_spreadsheet()
        while flag:
            ws_local = sheets_data[i][1]  # Get all records from the sheet
            columns_list = ws_local[0] if ws_local else []  # Get the list of headers
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
        set_option('columns', 'confirm',
                   columns_list[int(input(f"Confirmation checkbox for portal registration: ")) - 1])
        set_option('columns', 'login', columns_list[int(input(f"Field for displaying the login or errors: ")) - 1])


setup()


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


def validate_name(name):
    if (name.replace(' ', '').replace('\n', '')).isalpha() and len(name.split()) > 1:
        return name.title()
    logger.error('Error: name is not correct (only letters and more than 1 word)!')
    return None


def generate_unique_login(name):
    original_login = name.split(' ')[1][0].lower() + '_' + name.split(' ')[0].lower()
    max_attempts = int(get_option('config', 'max_login_generation_attempts'))
    for attempt in range(max_attempts):
        response = call('core_user_get_users_by_field', field='username', values=[original_login])
        # Если такого пользователя нет, возвращаем этот логин
        if not response:
            return original_login
        # Иначе увеличиваем номер в логине
        original_login = original_login + str(attempt + 1)
    logger.error('Failed to generate a unique login after %s attempts.', max_attempts)
    return None


def newUser(name, course_name, email):
    # 1. Проверка существующего пользователя
    existing_user = get_user_by_field('email', email)
    if existing_user:
        userid = existing_user['id']
        login = existing_user['username']
        password = None
    else:
        # 2. Валидация имени
        name = validate_name(name)
        if not name:
            return ['error', '', 'ERROR - Name is not valid!']

        # 3. Валидация email
        try:
            validate_email(email)
        except EmailNotValidError as e:
            logger.error('Incorrect email - %s: %s', email, e)
            return ['error', '', 'ERROR - Invalid email!']

        # 4. Генерация логина
        login = generate_unique_login(name)
        if not login:
            return ['error', '', 'ERROR - Failed to generate unique login']

        # 5. Создание нового пользователя
        firstname, lastname = name.split()[1], name.split()[0]
        password = generate_password()
        try:
            userid = create_user(firstname, lastname, email, login, password)
        except Exception as e:
            logger.error('Error while creating user with email %s: %s', email, e)
            return ['error', '', 'ERROR - User registration failed!']

    # 6. Проверка курса
    if len(course_name) > 100:
        logger.error('Course name is too long: %s', course_name)
        return ['error', '', 'ERROR - Course name is too long!']

    course = get_course_by_field('shortname', course_name)
    if course:
        courseid = course['id']
    else:
        try:
            courseid = create_course(course_name)
            mailto(course=course_name)  # Send email to admin about new course
        except Exception as e:
            logger.error('Error while creating course %s: %s', course_name, e)
            return ['error', '', 'ERROR - Course creation failed!']

    # 7. Запись пользователя на курс
    if not enroll_user_to_course(userid, courseid):
        return ['error', '', 'ERROR - Failed to enroll user to course']

    # 8. Отправка email пользователю
    try:
        mailto(course=course_name, name=name, login=login, password=password, email=email)
    except Exception as e:
        logger.error('Error while sending email to user: %s', e)

    return login


def check_new():
    sa = gspread.service_account(
        filename=get_option('google_sheets', 'credentials_path'))
    sh = sa.open(get_option('google_sheets', 'spreadsheet_name'))

    sheets_data = get_spreadsheet()

    for ws, ws_local in sheets_data:
        wks = sh.worksheet(ws)  # Получаем объект листа для текущего имени

        if not ws_local:  # Если нет данных в листе
            continue

        headers = ws_local[0]  # Первая строка - заголовки
        if config.col_name_login not in headers:
            logger.error("Login column not found in sheet %s", ws)
            continue

        col_index_login = headers.index(config.col_name_login)
        col_index_confirm = headers.index(config.col_confirm)

        for i, row in enumerate(ws_local[1:], start=2):  # Начнем с 2, так как первая строка - заголовки
            if row[col_index_confirm] == "TRUE" and \
                    (not row[col_index_login] or 'ERROR' in row[col_index_login]):
                if all([row[headers.index(config.col_name_fio)],
                        row[headers.index(config.col_name_course)],
                        row[headers.index(config.col_name_mail)]]):
                    try:
                        wks.update_cell(i, col_index_login + 1, newUser(row[headers.index(config.col_name_fio)],
                                                                        row[headers.index(config.col_name_course)],
                                                                        row[headers.index(config.col_name_mail)]))
                    except Exception as e:
                        if "429" in str(e):
                            logger.error("Google API - Too many requests. Pause for 20 seconds.")
                            sleep(20)
                        elif "502" in str(e):
                            logger.error("Google API - Something went wrong (Bad Gateway). Pause for 30 seconds.")
                            sleep(30)
                        else:
                            logger.error('Error while working with Google Sheets: %s', e)
                            sleep(20)
                else:
                    logger.error("Not all required data has been filled in for row %d in sheet %s", i, ws)
                    wks.update_cell(i, col_index_login + 1, 'ERROR: Not all required data has been filled in')


if __name__ == "__main__":
    logger.info('Program started successfully!')

    while True:
        check_new()
        # Pause for 20 seconds to avoid too many requests to Google Sheets API
        sleep(20)
