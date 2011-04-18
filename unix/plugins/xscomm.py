# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
#  Copyright (c) 2011 Openstack, LLC.
#  All Rights Reserved.
#
#     Licensed under the Apache License, Version 2.0 (the "License"); you may
#     not use this file except in compliance with the License. You may obtain
#     a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#     WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#     License for the specific language governing permissions and limitations
#     under the License.
#

"""
JSON agent command parser main code module
"""

import logging
import pyxenstore

try:
    import anyjson
except ImportError:
    import json

    class anyjson(object):
        """Fake anyjson module as a class"""

        @staticmethod
        def serialize(buf):
            return json.write(buf)

        @staticmethod
        def deserialize(buf):
            return json.read(buf)

XENSTORE_REQUEST_PATH = 'data/host'
XENSTORE_RESPONSE_PATH = 'data/guest'


class XSComm(object):
    """
    XenStore communication plugin for nova-agent
    """

    def __init__(self):
        self.xs_handle = pyxenstore.Handle()
        self.requests = []

    def _get_requests(self):
        """
        Get requests out of XenStore and cache for later use
        """

        self.xs_handle.transaction_start()

        entries = self.xs_handle.entries(XENSTORE_REQUEST_PATH)

        for entry in entries:
            path = XENSTORE_REQUEST_PATH + '/' + entry
            data = self.xs_handle.read(path)

            self.requests.append({'path': path, 'data': data})

        self.xs_handle.transaction_end()

    def get_request(self):
        """
        Get a request out of the cache and return it.  If no entries in the
        cache, try to populate it first.
        """

        if len(self.requests) == 0:
            self._get_requests()
        if len(self.requests) == 0:
            return None
        return self.requests.pop(0)

    def put_response(self, req, resp):
        """
        Remove original request from XenStore and write out the response
        """

        self.xs_handle.rm(req['path'])

        basename = req['path'].rsplit('/', 1)[1]
        resp_path = XENSTORE_RESPONSE_PATH + '/' + basename

        self.xs_handle.write(resp_path, resp['data'])
