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

try:
    import anyjson
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

    class anyjson(object):
        """Fake anyjson module as a class"""

        @staticmethod
        def serialize(buf):
            return json.dumps(buf)

        @staticmethod
        def deserialize(buf):
            return json.loads(buf)


class JsonParser(object):
    """
    JSON command parser plugin for nova-agent
    """

    def __init__(self, command_cls, *args, **kwargs):
        if not getattr(command_cls, "run_command", None):
            raise TypeError("Command class has no 'run_command' method")

        self._command_cls = command_cls

    def encode_result(self, result):

        our_format = {"returncode": str(result[0]),
                      "message": result[1]}

        return {"data": anyjson.serialize(our_format)}

    def parse_request(self, request):

        try:
            request = anyjson.deserialize(request['data'])
        except KeyError, e:
            logging.error("Request dictionary contains no 'data' key")
            return self.encode_result((500, "Internal error with request"))
        except Exception, e:
            logging.error("Invalid JSON in 'data' key for request")
            return self.encode_result((500, "Request is malformed"))

        try:
            cmd_name = request['name']
        except KeyError:
            logging.error("Request is missing 'name' key")
            return self.encode_result((500, "Request is missing 'name' key"))
        cmd_string = request.get('value', '')

        # XXX Major kludge here to not log activation keys for redhat
        if isinstance(cmd_string, dict) and \
                'activation_key' in cmd_string:
            cs_copy = cmd_string.copy()
            cs_copy['activation_key'] = "<removed>"
            logging.info("Received command '%s' with argument: '%s'" % \
                (cmd_name, cs_copy))
        else:
            logging.info("Received command '%s' with argument: '%s'" % \
                (cmd_name, cmd_string))

        try:
            result = self._command_cls.run_command(cmd_name, cmd_string)
        except self._command_cls.CommandNotFoundError, e:
            logging.warn(str(e))
            return self.encode_result((404, str(e)))
        except Exception, e:
            logging.exception('Exception while trying to process '
                    'command %r' % cmd_name)
            return self.encode_result((500, str(e)))

        logging.info("'%s' completed with code '%s', message '%s'" % \
                (cmd_name, result[0], result[1]))

        return self.encode_result(result)
