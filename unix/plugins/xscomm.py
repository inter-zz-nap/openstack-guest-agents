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

    def __init__(self, *args, **kwargs):

        self.request_path = kwargs.get("request_path",
                XENSTORE_REQUEST_PATH)
        self.response_path = kwargs.get("response_path",
                XENSTORE_RESPONSE_PATH)

        self.xs_handle = pyxenstore.Handle()
        self.xs_handle.mkdir(self.request_path)
        self.requests = []

    def _check_handle(self):
        if not self.xs_handle:
            self.xs_handle = pyxenstore.Handle()

    def _get_requests(self):
        """
        Get requests out of XenStore and cache for later use
        """

        self._check_handle()

        try:
            self.xs_handle.transaction_start()
        except pyxenstore.PyXenStoreError, e:
            # Need to have the handle reopened later
            self.xs_handle = None
            raise e

        try:
            entries = self.xs_handle.entries(self.request_path)
        except pyxenstore.NotFoundError:
            # Someone removed the path on us ?
            try:
                self.xs_handle.transaction_end()
            except Exception:
                # No matter what exception we get, since we couldn't
                # end the transaction, we're going to need to reopen
                # the handle later
                self.xs_handle = None

            try:
                self.xs_handle.mkdir(self.request_path)
            except pyxenstore.PyXenStoreError, e:
                # Need to have the handle reopened later
                self.xs_handle = None
                raise e
            # Re-try after mkdir()
            return self._get_requests()
        except pyxenstore.PyXenStoreError, e:
            # Any other XenStore errors need to have handle reopened
            self.xs_handle = None
            raise e
        except Exception, e:
            try:
                self.xs_handle.transaction_end()
            except:
                # No matter what exception we get, since we couldn't
                # end the transaction, we're going to need to reopen
                # the handle later
                self.xs_handle = None
                raise e
            raise e

        for entry in entries:
            path = self.request_path + '/' + entry
            try:
                data = self.xs_handle.read(path)
            except pyxenstore.NotFoundError:
                continue
            except pyxenstore.PyXenStoreError, e:
                # Any other XenStore errors need to have handle reopened
                self.xs_handle = None
                raise e
            except Exception, e:
                try:
                    self.xs_handle.transaction_end()
                except:
                    # No matter what exception we get, since we couldn't
                    # end the transaction, we're going to need to reopen
                    # the handle later
                    self.xs_handle = None
                raise e

            try:
                self.requests.append({'path': path, 'data': data})
            except Exception, e:
                try:
                    self.xs_handle.transaction_end()
                except:
                    # No matter what exception we get, since we couldn't
                    # end the transaction, we're going to need to reopen
                    # the handle later
                    self.xs_handle = None
                raise e

        try:
            self.xs_handle.transaction_end()
        except:
            # No matter what exception we get, since we couldn't
            # end the transaction, we're going to need to reopen
            # the handle later
            self.xs_handle = None
            raise e
        return len(self.requests) > 0

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

        self._check_handle()

        try:
            self.xs_handle.rm(req['path'])
        except pyxenstore.PyXenStoreError, e:
            self.xs_handle = None
            self._check_handle()
            # Fall through...

        basename = req['path'].rsplit('/', 1)[1]
        resp_path = self.response_path + '/' + basename

        try:
            self.xs_handle.write(resp_path, resp['data'])
        except pyxenstore.PyXenStoreError, e:
            self.xs_handle = None
            raise e
