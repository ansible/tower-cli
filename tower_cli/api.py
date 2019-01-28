# Copyright 2015, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import contextlib
import copy
import functools
import json
import stat
import warnings

try:
    from urlparse import urljoin, urlparse
except Exception:
    from urllib.parse import urljoin, urlparse

from datetime import datetime as dt

from requests.exceptions import ConnectionError, SSLError
from requests.sessions import Session
from requests.models import Response
from requests.packages import urllib3
from requests.auth import AuthBase, HTTPBasicAuth

from tower_cli import exceptions as exc
from tower_cli.conf import settings
from tower_cli.utils import data_structures, debug, secho, supports_oauth
from tower_cli.constants import CUR_API_VERSION


TOWER_DATETIME_FMT = r'%Y-%m-%dT%H:%M:%S.%fZ'


class BasicTowerAuth(AuthBase):

    def __init__(self, username, password, cli_client):
        self.username = username
        self.password = password
        self.cli_client = cli_client
        self.use_legacy_token = settings.use_token

    def _acquire_token(self):
        return self.cli_client._make_request(
            'POST', self.cli_client.get_prefix() + 'authtoken/', [],
            {'data': json.dumps({'username': self.username, 'password': self.password}),
             'headers': {'Content-Type': 'application/json'}}
        ).json()

    def _get_auth_token(self):
        filename = os.path.expanduser('~/.tower_cli_token.json')
        token_json = None
        try:
            with open(filename) as f:
                token_json = json.load(f)
            if not isinstance(token_json, dict) or self.cli_client.get_prefix() not in token_json or \
                    'token' not in token_json[self.cli_client.get_prefix()] or \
                    'expires' not in token_json[self.cli_client.get_prefix()] or \
                    dt.utcnow() > dt.strptime(token_json[self.cli_client.get_prefix()]['expires'], TOWER_DATETIME_FMT):
                raise Exception("Current token expires.")
            return 'Token ' + token_json[self.cli_client.get_prefix()]['token']
        except Exception as e:
            debug.log('Acquiring and caching auth token due to:\n%s' % str(e), fg='blue', bold=True)
            if not isinstance(token_json, dict):
                token_json = {}
            token_json[self.cli_client.get_prefix()] = self._acquire_token()
            if not isinstance(token_json[self.cli_client.get_prefix()], dict) or \
                    'token' not in token_json[self.cli_client.get_prefix()] or \
                    'expires' not in token_json[self.cli_client.get_prefix()]:
                raise exc.AuthError('Invalid Tower auth token format: %s' % json.dumps(
                    token_json[self.cli_client.get_prefix()]
                ))
            with open(filename, 'w') as f:
                json.dump(token_json, f)
            try:
                os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR)
            except Exception as e:
                warnings.warn(
                    'Unable to set permissions on {0} - {1} '.format(filename, e),
                    UserWarning
                )
            return 'Token ' + token_json[self.cli_client.get_prefix()]['token']

    def __call__(self, r):
        if 'Authorization' in r.headers:
            return r
        if settings.oauth_token:
            if supports_oauth:
                r.headers['Authorization'] = 'Bearer {}'.format(settings.oauth_token)
                return r
            else:
                warnings.warn(
                    'This version of Tower does not support OAuth2.0'
                )
        if self.use_legacy_token:
            resp = self.cli_client._make_request(
                'OPTIONS', self.cli_client.get_prefix() + 'authtoken/', [], {}
            )
            if resp.ok:
                r.headers['Authorization'] = self._get_auth_token()
            else:
                warnings.warn(
                    'use_token is not supported in this version of Tower '
                    '(the Auth Token API has been replaced with OAuth2.0 support)',
                )
                HTTPBasicAuth(self.username, self.password)(r)
        else:
            HTTPBasicAuth(self.username, self.password)(r)
        return r


class Client(Session):
    """A class for making HTTP requests to the Ansible Tower API and
    returning the responses.

    This functions as a wrapper around [requests][1], and returns its
    responses; therefore, interact with response objects to this class the
    same way you would with objects you get back from `requests.get` or
    similar.

      [1]: http://docs.python-requests.org/en/latest/
    """
    def __init__(self):
        super(Client, self).__init__()
        for adapter in self.adapters.values():
            adapter.max_retries = 3

    def _make_request(self, method, url, args, kwargs):
        # Decide whether to require SSL verification
        verify_ssl = True
        if (settings.verify_ssl is False) or hasattr(settings, 'insecure'):
            verify_ssl = False
        elif settings.certificate:
            verify_ssl = settings.certificate

        # Call the superclass method.
        try:
            with warnings.catch_warnings():
                warnings.simplefilter(
                    "ignore", urllib3.exceptions.InsecureRequestWarning)
                return super(Client, self).request(
                    method, url, *args, verify=verify_ssl, **kwargs)
        except SSLError as ex:
            # Throw error if verify_ssl not set to false and server
            #  is not using verified certificate.
            if settings.verbose:
                debug.log('SSL connection failed:', fg='yellow', bold=True)
                debug.log(str(ex), fg='yellow', bold=True, nl=2)
            if not settings.host.startswith('http'):
                secho('Suggestion: add the correct http:// or '
                      'https:// prefix to the host configuration.',
                      fg='blue', bold=True)
            raise exc.ConnectionError(
                'Could not establish a secure connection. '
                'Please add the server to your certificate '
                'authority.\nYou can run this command without verifying SSL '
                'with the --insecure flag, or permanently disable '
                'verification by the config setting:\n\n '
                'tower-cli config verify_ssl false'
            )
        except ConnectionError as ex:
            # Throw error if server can not be reached.
            if settings.verbose:
                debug.log('Cannot connect to Tower:', fg='yellow', bold=True)
                debug.log(str(ex), fg='yellow', bold=True, nl=2)
            raise exc.ConnectionError(
                'There was a network error of some kind trying to connect '
                'to Tower.\n\nThe most common  reason for this is a settings '
                'issue; is your "host" value in `tower-cli config` correct?\n'
                'Right now it is: "%s".' % settings.host
            )

    def get_prefix(self, include_version=True):
        """Return the appropriate URL prefix to prepend to requests,
        based on the host provided in settings.
        """
        host = settings.host
        if '://' not in host:
            host = 'https://%s' % host.strip('/')
        elif host.startswith('http://') and settings.verify_ssl:
            raise exc.TowerCLIError(
                'Can not verify ssl with non-https protocol. Change the '
                'verify_ssl configuration setting to continue.'
            )
        # Validate that we have either an http or https based URL
        url_pieces = urlparse(host)
        if url_pieces[0] not in ['http', 'https']:
            raise exc.ConnectionError('URL must be http(s), {} is not valid'.format(url_pieces[0]))

        prefix = urljoin(host, '/api/')
        if include_version:
            # We add the / to the end of {} so that our URL has the ending slash.
            prefix = urljoin(prefix, "{}/".format(CUR_API_VERSION))

        return prefix

    @functools.wraps(Session.request)
    def request(self, method, url, *args, **kwargs):
        """Make a request to the Ansible Tower API, and return the
        response.
        """

        # If the URL has the api/vX at the front strip it off
        # This is common to have if you are extracting a URL from an existing object.
        # For example, any of the 'related' fields of an object will have this
        import re
        url = re.sub("^/?api/v[0-9]+/", "", url)

        # Piece together the full URL.
        use_version = not url.startswith('/o/')
        url = '%s%s' % (self.get_prefix(use_version), url.lstrip('/'))

        # Ansible Tower expects authenticated requests; add the authentication
        # from settings if it's provided.
        kwargs.setdefault(
            'auth',
            BasicTowerAuth(
                settings.username,
                settings.password,
                self
            )
        )

        # POST and PUT requests will send JSON by default; make this
        # the content_type by default.  This makes it such that we don't have
        # to constantly write that in our code, which gets repetitive.
        headers = kwargs.get('headers', {})
        if method.upper() in ('PATCH', 'POST', 'PUT'):
            headers.setdefault('Content-Type', 'application/json')
            kwargs['headers'] = headers

        # If debugging is on, print the URL and data being sent.
        debug.log('%s %s' % (method, url), fg='blue', bold=True)
        if method in ('POST', 'PUT', 'PATCH'):
            debug.log('Data: %s' % kwargs.get('data', {}),
                      fg='blue', bold=True)
        if method == 'GET' or kwargs.get('params', None):
            debug.log('Params: %s' % kwargs.get('params', {}),
                      fg='blue', bold=True)
        debug.log('')

        # If this is a JSON request, encode the data value.
        if headers.get('Content-Type', '') == 'application/json':
            kwargs['data'] = json.dumps(kwargs.get('data', {}))

        r = self._make_request(method, url, args, kwargs)

        # Sanity check: Did the server send back some kind of internal error?
        # If so, bubble this up.
        if r.status_code >= 500:
            raise exc.ServerError('The Tower server sent back a server error. '
                                  'Please try again later.')

        # Sanity check: Did we fail to authenticate properly?
        # If so, fail out now; this is always a failure.
        if r.status_code == 401:
            raise exc.AuthError('Invalid Tower authentication credentials (HTTP 401).')

        # Sanity check: Did we get a forbidden response, which means that
        # the user isn't allowed to do this? Report that.
        if r.status_code == 403:
            raise exc.Forbidden("You don't have permission to do that (HTTP 403).")

        # Sanity check: Did we get a 404 response?
        # Requests with primary keys will return a 404 if there is no response,
        # and we want to consistently trap these.
        if r.status_code == 404:
            raise exc.NotFound('The requested object could not be found.')

        # Sanity check: Did we get a 405 response?
        # A 405 means we used a method that isn't allowed. Usually this
        # is a bad request, but it requires special treatment because the
        # API sends it as a logic error in a few situations (e.g. trying to
        # cancel a job that isn't running).
        if r.status_code == 405:
            raise exc.MethodNotAllowed(
                "The Tower server says you can't make a request with the "
                "%s method to that URL (%s)." % (method, url),
            )

        # Sanity check: Did we get some other kind of error?
        # If so, write an appropriate error message.
        if r.status_code >= 400:
            raise exc.BadRequest(
                'The Tower server claims it was sent a bad request.\n\n'
                '%s %s\nParams: %s\nData: %s\n\nResponse: %s' %
                (method, url, kwargs.get('params', None),
                 kwargs.get('data', None), r.content.decode('utf8'))
            )

        # Django REST Framework intelligently prints API keys in the
        # order that they are defined in the models and serializer.
        #
        # We want to preserve this behavior when it is possible to do so
        # with minimal effort, because while the order has no explicit meaning,
        # we make some effort to order keys in a convenient manner.
        #
        # To this end, make this response into an APIResponse subclass
        # (defined below), which has a `json` method that doesn't lose key
        # order.
        r.__class__ = APIResponse

        # Return the response object.
        return r

    @property
    @contextlib.contextmanager
    def test_mode(self):
        """Replace the HTTP adapters with a fauxquests.FauxAdapter, which
        will make the client into a faux client.
        """
        # Import this here, because we don't want to require fauxquests
        # in order for the app to work.
        from fauxquests.adapter import FauxAdapter
        with settings.runtime_values(host='20.12.4.21', username='meagan',
                                     password='This is the best wine.',
                                     verbose=False, format='json'):
            adapters = copy.copy(self.adapters)
            faux_adapter = FauxAdapter(
                url_pattern=self.get_prefix().rstrip('/') + '%s',
            )

            try:
                self.adapters.clear()
                self.mount('https://', faux_adapter)
                self.mount('http://', faux_adapter)
                yield faux_adapter
            finally:
                self.adapters = adapters


class APIResponse(Response):
    """A Response subclass which preseves JSON key order (but makes no other
    changes).
    """
    def json(self, **kwargs):
        kwargs.setdefault('object_pairs_hook', data_structures.OrderedDict)
        try:
            return super(APIResponse, self).json(**kwargs)
        except Exception:
            kwargs.pop('object_pairs_hook', None)
            return super(APIResponse, self).json(**kwargs)


client = Client()
