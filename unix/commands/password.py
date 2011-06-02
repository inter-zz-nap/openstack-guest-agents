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
JSON password reset handling plugin
"""

import base64
import binascii
import logging
import os
import subprocess
import time

from Crypto.Cipher import AES
import commands

# This is to support older python versions that don't have hashlib
try:
    import hashlib
except ImportError:
    import md5

    class hashlib(object):
        """Fake hashlib module as a class"""

        @staticmethod
        def md5():
            return md5.new()


class PasswordError(Exception):
    """
    Class for password command exceptions
    """

    def __init__(self, response):
        # Should be a (ResponseCode, ResponseMessage) tuple
        self.response = response

    def __str__(self):
        return "%s: %s" % self.response

    def get_response(self):
        return self.response


class PasswordCommands(commands.CommandBase):
    """
    Class for password related commands
    """

    def __init__(self, *args, **kwargs):
        # prime to use
        self.prime = 162259276829213363391578010288127
        self.base = 5
        self.kwargs = {}
        self.kwargs.update(kwargs)

    def _mod_exp(self, num, exp, mod):
        result = 1
        while exp > 0:
            if (exp & 1) == 1:
                result = (result * num) % mod
            exp = exp >> 1
            num = (num * num) % mod
        return result

    def _make_private_key(self):
        """
        Create a private key using /dev/urandom
        """

        return int(binascii.hexlify(os.urandom(16)), 16)

    def _dh_compute_public_key(self, private_key):
        """
        Given a private key, compute a public key
        """

        return self._mod_exp(self.base, private_key, self.prime)

    def _dh_compute_shared_key(self, public_key, private_key):
        """
        Given public and private keys, compute the shared key
        """

        return self._mod_exp(public_key, private_key, self.prime)

    def _compute_aes_key(self, key):
        """
        Given a key, compute the corresponding key that can be used
        with AES
        """

        m = hashlib.md5()
        m.update(key)

        aes_key = m.digest()

        m = hashlib.md5()
        m.update(aes_key)
        m.update(key)

        aes_iv = m.digest()

        return (aes_key, aes_iv)

    def _decrypt_password(self, aes_key, data):

        aes = AES.new(aes_key[0], AES.MODE_CBC, aes_key[1])
        passwd = aes.decrypt(data)

        cut_off_sz = ord(passwd[len(passwd) - 1])
        if cut_off_sz > 16 or len(passwd) < 16:
            raise PasswordError((500, "Invalid password data received"))

        passwd = passwd[: - cut_off_sz]

        return passwd

    def _decode_password(self, data):

        try:
            real_data = base64.b64decode(data)
        except Exception:
            raise PasswordError((500, "Couldn't decode base64 data"))

        try:
            aes_key = self.aes_key
        except AttributeError:
            raise PasswordError((500, "Password without key exchange"))

        try:
            passwd = self._decrypt_password(aes_key, real_data)
        except PasswordError, e:
            raise e
        except Exception, e:
            raise PasswordError((500, str(e)))

        return passwd

    def _change_password(self, passwd):
        """Actually change the password"""

        if self.kwargs.get('testmode', False):
            return None

        pipe = subprocess.PIPE

        try:
            p = subprocess.Popen(["/usr/sbin/chpasswd"],
                    stdin=pipe, stdout=pipe, stderr=pipe, env={})
            p.communicate("root:%s\n" % passwd)
            ret = p.returncode
            if ret:
                raise PasswordError((500,
                    "Return code from chpasswd was %d" % ret))

        except Exception, e:
            p = subprocess.Popen(["/usr/bin/passwd", "root"],
                    stdin=pipe, stdout=pipe, stderr=pipe, env={})
            # Some password programs clear stdin after they display
            # prompts.  So, we can hack around this by sleeping.  Another
            # Option would be to do some read()s, but we might need to
            # poll on where to read(stderr vs stdout).  It seems stderr
            # is the one mostly used, but can I trust that?
            time.sleep(1)
            p.stdin.write("%s\n" % passwd)
            time.sleep(1)
            p.communicate("%s\n" % passwd)
            ret = p.returncode
            if ret:
                raise PasswordError((500,
                    "Return code from passwd was %d" % ret))

    def _wipe_key(self):
        """
        Remove key from a previous keyinit command
        """

        try:
            del self.aes_key
        except AttributeError:
            pass

    @commands.command_add('keyinit')
    def keyinit_cmd(self, data):

        # Remote pubkey comes in as large number
        remote_public_key = data

        my_private_key = self._make_private_key()
        my_public_key = self._dh_compute_public_key(my_private_key)

        shared_key = str(self._dh_compute_shared_key(remote_public_key,
                my_private_key))

        self.aes_key = self._compute_aes_key(shared_key)

        # The key needs to be a string response right now
        return ("D0", str(my_public_key))

    @commands.command_add('password')
    def password_cmd(self, data):

        try:
            passwd = self._decode_password(data)
            self._change_password(passwd)
        except PasswordError, e:
            return e.get_response()

        self._wipe_key()

        return (0, "")
