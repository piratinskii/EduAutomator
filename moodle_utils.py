import config
from requests import post
from log_config import logger


# Function for transforming parameters to Moodle API format
def rest_api_parameters(in_args, prefix='', out_dict=None):
    if out_dict is None:
        out_dict = {}
    if not type(in_args) in (list, dict):
        out_dict[prefix] = in_args
        return out_dict
    if prefix == '':
        prefix = prefix + '{0}'
    else:
        prefix = prefix + '[{0}]'
    if type(in_args) == list:
        for idx, item in enumerate(in_args):
            rest_api_parameters(item, prefix.format(idx), out_dict)
    elif type(in_args) == dict:
        for key, item in in_args.items():
            rest_api_parameters(item, prefix.format(key), out_dict)
    return out_dict


# Function for calling Moodle API
def call(fname, **kwargs):
    response = None
    try:
        parameters = rest_api_parameters(kwargs)
        parameters.update({"wstoken": config.KEY, 'moodlewsrestformat': 'json', "wsfunction": fname})
        response = post(config.URL + config.ENDPOINT, parameters)
        response = response.json()
        if type(response) == dict and response.get('exception'):
            raise SystemError("Error calling Moodle API\n", response)
    except Exception as e:
        logger.error('Error while calling Moodle API: %s', e)
    return response


def create_course(name):
    course_data = {
        'fullname': name,
        'shortname': name,
        'categoryid': config.get_option('moodle', 'category_id'),
    }
    res = call('core_course_create_courses', courses=[course_data])
    if isinstance(res, list) and len(res) > 0:
        logger.info('Course %s created', name)
        return res[0].get('id')
    return None


def create_user(firstname, lastname, email, username, password):
    user_data = {
        'username': username,
        'firstname': firstname,
        'lastname': lastname,
        'email': email,
        'password': password,
        'auth': 'manual',
        'preferences': [{'type': 'auth_forcepasswordchange', 'value': config.force_password}]
    }
    res = call('core_user_create_users', users=[user_data])
    if isinstance(res, list) and len(res) > 0:
        logger.info('User %s (%s) created', lastname + " " + firstname, username)
        return res[0].get('id')
    return None


def enroll_user_to_course(userid, courseid):
    try:
        call('enrol_manual_enrol_users', enrolments=[{'roleid': config.roleid, 'userid': userid, 'courseid': courseid}])
        user = get_user_by_field('id', userid)
        logger.info('User %s (%s) enrolled to the course %s', user.get("lastname") + " " + user.get("firstname"),
                    user.get("username"), get_course_by_field('id', courseid).get("fullname"))
        return True
    except Exception as e:
        logger.error('Error while enrolling user %s to the course: %s', userid, e)
        return False


def get_user_by_field(field, value):
    user = call('core_user_get_users_by_field', field=field, values=[value])
    if user and len(user) > 0:
        return user[0]
    return None


def get_course_by_field(field, value):
    course = call('core_course_get_courses_by_field', field=field, value=value)['courses']
    if course and len(course) > 0:
        return course[0]
    return None