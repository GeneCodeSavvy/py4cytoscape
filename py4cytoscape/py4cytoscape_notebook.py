# -*- coding: utf-8 -*-

"""Copyright 2020 The Cytoscape Consortium

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# External library imports
import requests
import requests
import json

# Internal module convenience imports
from .py4cytoscape_logger import log_http_result, log_http_request
from .exceptions import CyError



# Call CyREST as a remote service via Jupyter-bridge
import chardet
class SpoofResponse:

    def __init__(self, url, status_code, reason, text):
        self.url = url
        self.status_code = status_code
        self.reason = reason
        self.text = text

    def __repr__(self):
        return '<SpoofResponse [%s]>' % (self.status_code)

    def json(self):
        return json.loads(self.text)

    def raise_for_status(self):
        """Raises stored :class:`HTTPError`, if one occurred."""

        if 400 <= self.status_code < 500:
            raise requests.exceptions.HTTPError(
                u'%s Client Error: %s for url: %s' % (self.status_code, self.reason, self.url), response=self)

        elif 500 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(
                u'%s Server Error: %s for url: %s' % (self.status_code, self.reason, self.url), response=self)


def do_request_remote(method, url, **kwargs):
#        JUPYTER_BRIDGE_URL = 'http://127.0.0.1:9529' # For local testing
#        JUPYTER_BRIDGE_URL = 'http://192.168.2.194:9529' # For production
    JUPYTER_BRIDGE_URL = 'http://70.95.64.191:9529' # For production

    log_http_request(method, url, **kwargs)
    # Params: Method, url + params (cyrest_delete, cyrest_get, cyrest_post, cyrest_put), json (cyrest_post, cyrest_put), data(commands_post), headers (commands_get, commands_help, commands_post)
    #    r = requests.request(method, url, **kwargs)
    if 'json' in kwargs:
        data = kwargs['json']
    elif 'data' in kwargs:
        data = kwargs['data'].decode('utf-8')
    else:
        data = None

    http_request = {'command': method,
                    'url': url,
                    'params': kwargs['params'] if 'params' in kwargs else None,
                    'data': data,
                    'headers': kwargs['headers'] if 'headers' in kwargs else None
                    }
    r = requests.request('POST', JUPYTER_BRIDGE_URL + '/queue_request?channel=1',
                         headers={'Content-Type': 'application/json'}, json=http_request)
    if r.status_code != 200:
        raise CyError('Error posting to Jupyter-bridge: ' + r.text)
    r = requests.request('GET', JUPYTER_BRIDGE_URL + '/dequeue_reply?channel=1')
    if r.status_code != 200:
        raise CyError('Error receiving from Jupyter-bridge: ' + r.text)

    # We really need a JSON message coming from Jupyter-bridge. It will contain the Cytoscape HTTP response in a dict.
    # If the dict is bad, we can't continue. I have seen this happen, but as a consequence of questionable networking.
    # Specifically, I use tcpdump to monitor a message sent from Jupyter-bridge, and the message has an HTTP status,
    # headers, and JSON payload. However, on the receiver side, I use WireShark to see just the HTTP status and no
    # headers or JSON payload. The smoking gun appears to be that the headers and JSON payload are contained in the
    # TCP [FIN] packet, and never make it to the receiver side. Of course, this is bad form for TCP, but it is
    # happening. To mitigate this, I changed Jupyter-bridge to add 1500 bytes to the end of the payload. For normal-size
    # TCP packets (i.e., MTU=1500), this forces the headers and JSON payload to *not* be in the TCP [FIN] packet. This
    # seems to work, tacky as it may be. If it fails, we'll see that 'encoding' ends up being None, and the str() will
    # fail.
    try:
        content = r.content
        encoding = chardet.detect(content)['encoding']
        message = str(content, encoding, errors='replace')
        cy_reply = json.loads(message)
    except:
        content = content or 'None'
        raise CyError(u'Undeciperable message received from Jupyter-bridge: %s' % (str(content)))

    r = SpoofResponse(url, cy_reply['status'], cy_reply['reason'], cy_reply['text'])
    if cy_reply['status'] == 0:
        raise requests.exceptions.HTTPError(u'Could not contact url: %s' % (url), response=r)

    log_http_result(r)
    return r


_notebook_is_running = None
def notebook_is_running(new_state=None):
    global _notebook_is_running
    old_state = _notebook_is_running
    if not new_state is None:
        _notebook_is_running = new_state
    return old_state

def _check_notebook_is_running():
    global notebook_is_running
    if notebook_is_running is None:
        try: # from https://exceptionshub.com/how-can-i-check-if-code-is-executed-in-the-ipython-notebook.html
            shell = get_ipython().__class__.__name__
            if shell == 'ZMQInteractiveShell':
                notebook_is_running = True  # Jupyter notebook or qtconsole
            elif shell == 'TerminalInteractiveShell':
                notebook_is_running = False  # Terminal running IPython
            else:
                notebook_is_running = False  # Other type (?)
        except NameError:
            notebook_is_running = False  # Probably standard Python interpreter
        except:
            notebook_is_running = False  # Safety check ... shouldn't ever happen
            print('WARNING -- _notebook_is_running check failed')

_check_notebook_is_running()


_running_remote = None # Don't know whether Cytoscape is local or remote yet
def running_remote(new_state=None):
    global _running_remote
    old_state = _running_remote
    if not new_state is None:
        _running_remote = new_state
    return old_state

def check_running_remote():
    global _running_remote
    if notebook_is_running:
        if _running_remote is None:
            try:
                print('trying local Cytoscape')
                # Try connecting to a local Cytoscape, first, in case Notebook is on same machine as Cytoscape
                r = requests.request('GET', 'http://localhost:1234/v1', headers={'Content-Type': 'application/json'})
                if r.status_code != 200:
                    raise Exception('Failed to connect to local Cytoscape')
                _running_remote = False
            except:
                # Local Cytoscape doesn't appear to be reachable, so try reaching a remote Cytoscape via Jupyter-bridge
                try:
                    print('trying remote Cytoscape')
                    do_request_remote('GET', 'http://localhost:1234/v1', headers={'Content-Type': 'application/json'})
                    _running_remote = True
                except:
                    print('giving up on all Cytoscape')
                    # Couldn't reach a local or remote Cytoscape ... use probably didn't start a Cytoscape, so assume he will eventually
                    _running_remote = None
    else:
        _running_remote = False
    return _running_remote

check_running_remote()



