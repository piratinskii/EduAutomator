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


# TODO: Может лучше избавиться от классов?
class Course:
    def __init__(self, **data):
        self.__dict__.update(data)

    def create(self):
        try:
            res = call('core_course_create_courses', courses=[self.__dict__])
            if isinstance(res, list) and len(res) > 0:
                self.id = res[0].get('id')
        except Exception as e:
            logger.error('Error while creating course: %s', e)


def create_user(**kwargs):
    valid_keys = ['username',
                  'firstname',
                  'lastname',
                  'email',
                  'password']
    values = {key: kwargs[key] for key in valid_keys}
    values['auth'] = "manual"
    values['idnumber'] = "fromapi"
    preferences = [{'type': 'auth_forcepasswordchange', 'value': config.force_password}]
    values['preferences'] = preferences

    res = call('core_user_create_users', users=[values])
    if isinstance(res, list) and len(res) > 0:
        return res[0].get('id')
    return None


# class User:
#     def __init__(self, **data):
#         self.__dict__.update(data)
#
#     def create(self):
#         valid_keys = ['username',
#                       'firstname',
#                       'lastname',
#                       'email',
#                       'auth',
#                       'idnumber',
#                       'password']
#         values = {key: self.__dict__[key] for key in valid_keys}
#
#         if type(res) == list:
#             self.id = res[0].get('id')