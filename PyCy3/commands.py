# -*- coding: utf-8 -*-

import requests
import urllib.parse
import json
import webbrowser

from .pycy3_utils import *
from .exceptions import CyError
from PyCy3.decorators import debug

def __init__(self):
    pass

#TODO: Refactor functions to centralize HTTP handling and error handling

def cyrest_api(base_url=DEFAULT_BASE_URL):
    res = webbrowser.open(base_url + '/swaggerUI/swagger-ui/index.html?url=' + base_url + '/swagger.json#/', new=2, autoraise=True)
    return res

def cyrest_delete(operation=None, parameters=None, base_url=DEFAULT_BASE_URL, require_json=True):
    try:
        url = build_url(base_url, operation)
        r = requests.delete(url, params=parameters)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            if require_json:
                raise
            else:
                return r.text
    except requests.exceptions.RequestException as e:
        content = json.loads(e.response.content)
        print("In commands:cyrest_delete(): " + str(e) + '\n' + str(content))
        raise

def cyrest_get(operation=None, parameters=None, base_url=DEFAULT_BASE_URL, require_json=True):
    """ Perform HTTP GET and return a list object if JSON is returned; otherwise, just text """
    try:
        url = build_url(base_url, operation)
        r = requests.get(url, params=parameters)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            if require_json:
                raise
            else:
                return r.text
    except requests.exceptions.RequestException as e:
        content = json.loads(e.response.content) if e.response and e.response.content else ''
        print("In commands:cyrest_get(): " + str(e) + '\n' + str(content))
        raise


def cyrest_post(operation=None, parameters=None, body=None, base_url=DEFAULT_BASE_URL, require_json=True):
    """ Perform HTTP POST and return a list object if JSON is returned; otherwise, just text """
    try:
        url = build_url(base_url, operation)
        r = requests.post(url, params=parameters, json=body)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            if require_json:
                raise
            else:
                return r.text
    except requests.exceptions.RequestException as e:
        content = json.loads(e.response.content)
        print("In commands:cyrest_post(): " + str(e) + '\n' + str(content))
        raise


def cyrest_put(operation=None, parameters=None, body=None, base_url=DEFAULT_BASE_URL, require_json=True):
    """ Perform HTTP PUT and return a list object if JSON is returned; otherwise, just text """
    try:
        url = build_url(base_url, operation)
        r = requests.put(url, params=parameters, json=body)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError as e:
            if require_json:
                raise
            else:
                return r.text
    except requests.exceptions.RequestException as e:
        content = json.loads(e.response.content)
        print("In commands:cyrest_put(): " + str(e) + '\n' + str(content))
        raise

def commands_api(base_url=DEFAULT_BASE_URL):
    res = webbrowser.open(base_url + '/swaggerUI/swagger-ui/index.html?url=' + base_url + '/commands/swagger.json#/', new=2, autoraise=True)
    return res

# TODO: Make sure this works the same as in R
def commands_get(cmd_string, base_url=DEFAULT_BASE_URL):
    try:
        get_url, parameters = _command_2_get_query(cmd_string, base_url=base_url)
        r = requests.get(get_url, params=parameters)
        r.raise_for_status()

        # Break response into a list of lines and return it
        res_list = re.split('\n\\s*', r.text)
        res_list = [line   for line in res_list if line != 'Finished']
        return res_list
    except requests.exceptions.RequestException as e:
        print("In commands:commands_get(): " + str(e) + '\n' + str(e.response.content))
        raise CyError(e.response.content)

# TODO: Make sure this works the same as in R
def commands_help(cmd_string='help', base_url=DEFAULT_BASE_URL):
    try:
        cmd_string = re.sub(r'help *', cmd_string, cmd_string) # remove 'help ' if it's already in the request
        get_url, parameters = _command_2_get_query(cmd_string, base_url=base_url)
        r = requests.get(get_url, params=parameters)
        r.raise_for_status()

        # Break response into a list of lines and return it
        res_list = re.split('\n\\s*', r.text)[1:] # create a list of command options, and leave off the header
        res_list = [line.strip()   for line in res_list]
        return res_list
    except requests.exceptions.RequestException as e:
        print("In commands:commands_help(): " + str(e) + '\n' + str(e.response.content))
        raise CyError(e.response.content)

def commands_post(cmd, base_url=DEFAULT_BASE_URL, require_json=True):
    try:
        post_url = _command_2_post_query_url(cmd, base_url=base_url)
        post_body = _command_2_post_query_body(cmd)
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
        r = requests.post(post_url, data=post_body, headers=headers)
        r.raise_for_status()
        return json.loads(r.text)['data']
    except requests.exceptions.RequestException as e:
        content = json.loads(e.response.content)
        print("In commands:commands_post(): " + str(e) + '\n' + str(content))

        raise CyError(content['errors'][0]['message'])

def commands_run(cmd_string, base_url=DEFAULT_BASE_URL):
    return commands_get(cmd_string, base_url=base_url)

# TODO: Take another look at the R version ... it seems to be passing in the wrong parameter name
def command_echo(variable_name='*', base_url=DEFAULT_BASE_URL):
    return commands_post('command echo message="' + variable_name + '"', base_url=base_url)

# TODO: It doesn't look like the command space supports open ... does the R version work?
def command_open_dialog(base_url=DEFAULT_BASE_URL):
    return commands_post('command open dialog', base_url=base_url)

def command_pause(message='', base_url=DEFAULT_BASE_URL):
    return commands_post('command pause message="' + message + '"', base_url=base_url)

def command_quit(base_url=DEFAULT_BASE_URL):
    return commands_post('command quit', base_url=base_url)

def command_run_file(file, args=None, base_url=DEFAULT_BASE_URL):
    args_str = ' args="' + args + '"' if args else ''

    return commands_post('command run' + args_str + ' file="' + file + '"', base_url=base_url)

def command_sleep(duration=None, base_url=DEFAULT_BASE_URL):
    dur_str = ' duration="' + str(duration) + '"' if duration else ''

    return commands_post('command sleep' + dur_str, base_url=base_url)


def _command_2_get_query(cmd_string, base_url=DEFAULT_BASE_URL):
    # Wipe out parameters so we can focus just on the Cytoscape command
    # For example, 'network get attribute network="test" namespace="default" columnList="SUID"'
    # becomes 'network get attributeXXXXXXnetwork="test"XXXXXXnamespace="default"XXXXXXcolumnList="SUID"'
    cmd_mark_params = re.sub(r' ([A-Za-z0-9_-]*=)', 'XXXXXX\\1', cmd_string)

    # Separate Cytoscape command and parameters. Using the above:
    # 'network get attribute', 'network="test"', 'namespace="default"', 'columnList="SUID"'
    split_cmd = cmd_mark_params.split('XXXXXX')

    # Assemble just the cy_cmd as a CyREST command URL
    cy_cmd = split_cmd[0] or ''
    url = base_url + urllib.parse.quote('/commands/' + re.sub(' ', '/', cy_cmd, count=1))

    # Create a dict of parameter names/values
    args = ' '.join(split_cmd[1:])
    if args:
        args = re.sub(r'"', '', args) # Get rid of all " (presumably surrounding command argument values)
        name_list = re.findall('[A-Za-z0-9_-]+=', args)  # Find all parameter names (e.g., 'abc=')
        name_list = [re.sub(r'=', '', name)  for name in name_list] # Get rid of all '=' at the end of parameter names
        val_list = re.split(' *[A-Za-z0-9_-]+=', args)[1:] # Find all parameter values (.e.g., the '123' part of 'abc=123')
        arg_dict = {key: val   for key, val in zip(name_list, val_list)} # Create dictionary out of param names and values
    else:
        arg_dict = None

    return url, arg_dict

def _command_2_post_query_url(cmd, base_url=DEFAULT_BASE_URL):
    """ Construct complete command URL from base URL and Cytoscape command """

    # Wipe out parameters so we can focus just on the Cytoscape command
    # For example, 'network get attribute network="test" namespace="default" columnList="SUID"'
    # becomes 'network get attributeXXXXXXnetwork="test"XXXXXXnamespace="default"XXXXXXcolumnList="SUID"'
    cmd_mark_params = re.sub(r' ([A-Za-z0-9_-]*=)', 'XXXXXX\\1', cmd)

    # Separate Cytoscape command and parameters. Using the above:
    # 'network get attribute', 'network="test"', 'namespace="default"', 'columnList="SUID"'
    split_cmd = cmd_mark_params.split('XXXXXX')

    # Assemble just the cy_cmd as a CyREST command URL
    cy_cmd = split_cmd[0] or ''
    url = base_url + urllib.parse.quote('/commands/' + re.sub(' ', '/', cy_cmd, count=1))

    return url

def _command_2_post_query_body(cmd):
    """ Construct body of POST as JSON representing inline parameters """

    # Set markers 'XXXXXX" on each parameter so we can see where they are.
    # For example, 'network get attribute network="test" namespace="default" columnList="SUID"'
    # becomes 'network get attributeXXXXXXnetwork="test"XXXXXXnetwork="default"XXXXXXcolumnList="SUID"'
    cmd_mark_params = re.sub(r' ([A-Za-z0-9_-]*=)', 'XXXXXX\\1', cmd)
    split_cmd = cmd_mark_params.split("XXXXXX")

    # Extract just the parameters ... if there are none, invent one
    params = split_cmd[1:]
    if params is None: params = ['atLeastOneArg=required']

    # Create a dictionary containing params as key-value, squeezing out quotes
    param_dict = {}
    for x in params:
        p = re.sub('"', '', x).split('=', 1)
        if p[0] is None: raise CyError('Missing parameter name')
        param_dict[p[0]] = p[1]

    return str.encode(json.dumps(param_dict))

def prep_post_query_lists(cmd_list=None, cmd_by_col=None):
    if cmd_list is None:
         cmd_list_ready = 'selected'
    elif not cmd_by_col is None:
        cmd_list_col = [cmd_by_col + ':' + cmd    for cmd in cmd_list]
        cmd_list_ready = ','.join(cmd_list_col)
    else:
        cmd_list_ready = cmd_list if isinstance(cmd_list, str) else ','.join(cmd_list)

    return cmd_list_ready
