
# Copyright 2013, AnsibleWorks Inc.
# Michael DeHaan <michael@ansibleworks.com>
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

import exceptions
import optparse
import datetime
import getpass
import json
import urllib2

class BaseException(exceptions.Exception):
    def __init__(self, msg):
        super(BaseException, self).__init__()
        self.msg = msg

    def __str__(self):
        return "ERROR: %s" % self.msg

class CommandNotFound(BaseException):
    pass

class SortedOptParser(optparse.OptionParser):

    def format_help(self, formatter=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)

def get_parser():

    usage = "%prog [options]"
    parser = SortedOptParser(usage)

    parser.add_option('-u', '--username', dest='username', default=None, type='str')
    parser.add_option('-p', '--password', dest='password', default=None, type='str')
    parser.add_option('-s', '--server',   dest='server',   default=None, type='str')
  
    return parser

class Connection(object):

    def __init__(self, server):
        self.server = server

    def get(self, endpoint):
        url = "%s%s" % (self.server, endpoint)
        print "accessing: %s" % url
        response = urllib2.urlopen(url)
        data = response.read()
        return json.loads(data)

def connect(options):
    if type(options) != dict:
        options = dict(
            username = options.username,
            password = options.password,
            server   = options.server
        )
    username = options.get("username", None)
    password = options.get("password", None)
    server   = options.get("server", "https://127.0.0.1")

    if username is None:
        raise Exception("--username is required")
    if password is None:
        raise BaseException("--password is required")
    if server is None:
        server = "https://127.0.0.1"
    print "connecting to: %s" % server

    # Setup urllib2 for basic password authentication.
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, server, username, password)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)

    conn = Connection(server)
    print conn.get('/api/v1/')
    return conn



