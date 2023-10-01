import configparser
import os
import platform


config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')


def set_env_variable(key, value):
    """
    Set environment variable for current user. Using for storing Moodle API key
    :param key: Key of variable
    :param value: Value of variable
    """
    system_platform = platform.system()

    if system_platform == "Windows":
        os.system(f'setx {key} "{value}" /M')
    elif system_platform == "Linux" or system_platform == "Darwin":  # Darwin is macOS
        os.system(f'echo "export {key}={value}" >> ~/.bashrc')
        os.system(f'echo "export {key}={value}" >> ~/.bash_profile')
        os.system(f'echo "export {key}={value}" >> ~/.zshrc')
    else:
        raise Exception("Unsupported OS")


def check_env():
    """
    Check if Moodle API key is set. If not - ask user to enter it
    :return: Moodle API key
    """
    # Check if Moodle API key is set
    moodle_api_key = os.environ.get('EDU_AUTOMATOR_MOODLE_API_KEY')
    # If key didn't set, ask user to enter it
    if not moodle_api_key:
        moodle_api_key = input("Please enter the Moodle API key: ")
        set_env_variable('EDU_AUTOMATOR_MOODLE_API_KEY', moodle_api_key)
        os.environ['EDU_AUTOMATOR_MOODLE_API_KEY'] = moodle_api_key
    return moodle_api_key


def set_option(section, option, new_value):
    """
    Set new value to option in config.ini
    :param section: Section of config.ini (moodle, columns etc.)
    :param option: Option of section (url, endpoint etc.)
    :param new_value: New value of option
    """
    config[section][option] = new_value
    with open('config.ini', 'w', encoding='utf-8') as configfile:
        config.write(configfile)


def get_option(section, option):
    """
    Get option's value from config.ini
    :param section: Section of config.ini (moodle, columns etc.)
    :param option: Name of option (url, endpoint etc.)
    :return: Value of option
    """
    return config[section][option]


# General configuration
# Moodle API Configuration
KEY = check_env()
URL = config['moodle']['url']
ENDPOINT = config['moodle']['endpoint']

# Moodle main configuration
roleid = config['moodle']['student_role_id']
force_password = config['moodle']['force_password_change']
category_id = config['moodle']['category_id']

# Columns configuration
col_name_fio = config['columns']['fullname']
col_name_course = config['columns']['course_name']
col_name_mail = config['columns']['email']
col_confirm = config['columns']['confirm']
col_name_login = config['columns']['login']

# E-mail Configuration
admin_email = config['email']['admin_email']
mail_subject = config['email']['subject']
mail_subject_nocourse = config['email']['no_course_subject']
