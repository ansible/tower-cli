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

import requests
from requests.sessions import Session

from tower_cli.api import APIResponse, client
from tower_cli.conf import settings
from tower_cli.utils import debug, exceptions as exc
from tower_cli.utils.data_structures import OrderedDict

from tests.compat import unittest, mock
import click

REQUESTS_ERRORS = [requests.exceptions.ConnectionError,
                   requests.exceptions.SSLError]


class ClientTests(unittest.TestCase):
    """A set of tests to ensure that the API Client class works in the
    way that we expect.
    """
    def test_prefix_implicit_https(self):
        """Establish that the prefix property returns the appropriate
        URL prefix given a host with no specified protocol.
        """
        with settings.runtime_values(host='33.33.33.33'):
            self.assertEqual(client.prefix, 'https://33.33.33.33/api/v1/')

    def test_prefix_explicit_protocol(self):
        """Establish that the prefix property returns the appropriate
        URL prefix and don't clobber over an explicit protocol.
        """
        with settings.runtime_values(host='bogus://33.33.33.33/'):
            self.assertEqual(client.prefix, 'bogus://33.33.33.33/api/v1/')

    def test_request_ok(self):
        """Establish that a request that returns a valid JSON response
        returns without incident and comes back as an APIResponse.
        """
        with client.test_mode as t:
            t.register_json('/ping/', {'status': 'ok'})
            r = client.get('/ping/')

            # Establish that our response is an APIResponse and that our
            # JSONification method returns back an ordered dict.
            self.assertIsInstance(r, APIResponse)
            self.assertIsInstance(r.json(), OrderedDict)

            # Establish that our headers have expected auth.
            request = r.request
            self.assertEqual(request.headers['Authorization'],
                             'Basic bWVhZ2FuOlRoaXMgaXMgdGhlIGJlc3Qgd2luZS4=')

            # Make sure the content matches what we expect.
            self.assertEqual(r.json(), {'status': 'ok'})

    def test_request_post(self):
        """Establish that on a POST request, we encode the provided data
        to JSON automatically.
        """
        with client.test_mode as t:
            t.register_json('/ping/', {'status': 'ok'}, method='POST')
            r = client.post('/ping/', {'payload': 'this is my payload.'})

            # Establish that our request has the expected payload, and
            # is sent using an application/json content type.
            headers = r.request.headers
            self.assertEqual(headers['Content-Type'], 'application/json')
            self.assertEqual(r.request.body,
                             '{"payload": "this is my payload."}')

    def test_connection_ssl_error(self):
        """Establish that if we get a ConnectionError or an SSLError
        back from requests, that we deal with it nicely.
        """
        for ErrorType in REQUESTS_ERRORS:
            with settings.runtime_values(verbose=False, host='https://foo.co'):
                with mock.patch.object(Session, 'request') as req:
                    req.side_effect = ErrorType
                    with self.assertRaises(exc.ConnectionError):
                        client.get('/ping/')

    def test_connection_ssl_error_verbose(self):
        """Establish that if we get a ConnectionError or an SSLError
        back from requests, that we deal with it nicely, and
        additionally print the internal error if verbose is True.
        """
        for ErrorType in REQUESTS_ERRORS:
            with settings.runtime_values(verbose=True, host='https://foo.co'):
                with mock.patch.object(Session, 'request') as req:
                    req.side_effect = ErrorType
                    with mock.patch.object(debug, 'log') as dlog:
                        with self.assertRaises(exc.ConnectionError):
                            client.get('/ping/')
                        self.assertEqual(dlog.call_count, 5)

    def test_server_error(self):
        """Establish that server errors raise the ServerError
        exception as expected.
        """
        with client.test_mode as t:
            t.register('/ping/', 'ERRORED!!', status_code=500)
            with self.assertRaises(exc.ServerError):
                client.get('/ping/')

    def test_auth_error(self):
        """Establish that authentication errors raise the AuthError
        exception.
        """
        with client.test_mode as t:
            t.register('/ping/', 'ERRORED!!', status_code=401)
            with self.assertRaises(exc.AuthError):
                client.get('/ping/')

    def test_forbidden_error(self):
        """Establish that forbidden errors raise the ForbiddenError
        exception.
        """
        with client.test_mode as t:
            t.register('/ping/', 'ERRORED!!', status_code=403)
            with self.assertRaises(exc.Forbidden):
                client.get('/ping/')

    def test_not_found_error(self):
        """Establish that authentication errors raise the NotFound
        exception.
        """
        with client.test_mode as t:
            t.register('/ping/', 'ERRORED!!', status_code=404)
            with self.assertRaises(exc.NotFound):
                client.get('/ping/')

    def test_method_not_allowed_error(self):
        """Establish that authentication errors raise the MethodNotAllowed
        exception.
        """
        with client.test_mode as t:
            t.register('/ping/', 'ERRORED!!', status_code=405)
            with self.assertRaises(exc.MethodNotAllowed):
                client.get('/ping/')

    def test_bad_request_error(self):
        """Establish that other errors not covered above raise the
        BadRequest exception.
        """
        with client.test_mode as t:
            t.register('/ping/', "I'm a teapot!", status_code=418)
            with self.assertRaises(exc.BadRequest):
                client.get('/ping/')

    def test_insecure_connection(self):
        """Establish that the --insecure flag will cause the program to
        call request with verify=False.
        """
        with mock.patch('requests.sessions.Session.request') as g:
            mock_response = type('statobj', (), {})()  # placeholder object
            mock_response.status_code = 200
            g.return_value = mock_response
            with client.test_mode as t:
                t.register('/ping/', "I'm a teapot!", status_code=200)
                with settings.runtime_values(verify_ssl=False):
                    client.get('/ping/')
                    g.assert_called_once_with(
                        # The pont is to assure verify=False below
                        'GET', mock.ANY, allow_redirects=True,
                        auth=(mock.ANY, mock.ANY), verify=False
                    )

    def test_http_contradiction_error(self):
        """Establish that commands can not be ran with verify_ssl set
        to false and an http connection."""
        with settings.runtime_values(
                host='http://33.33.33.33', verify_ssl=True):
            with self.assertRaises(exc.TowerCLIError):
                client.prefix

    def test_failed_suggestion_protocol(self):
        """Establish that if connection fails and protocol not given,
        tower-cli suggests that to the user."""
        with settings.runtime_values(verbose=False, host='foo.co'):
            with mock.patch.object(Session, 'request') as req:
                req.side_effect = requests.exceptions.SSLError
                with mock.patch.object(click, 'secho') as secho:
                    with self.assertRaises(exc.ConnectionError):
                        client.get('/ping/')
                    self.assertTrue(secho.called)
