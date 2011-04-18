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
Misc commands tester
"""

import base64
import binascii
import os
import subprocess

import agent_test
import agentlib


class TestPasswordCommands(agent_test.TestCase):

    def setUp(self):
        super(TestPasswordCommands, self).setUp()
        self.pw_inst = self.commands.command_instance("password")

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

        return self._mod_exp(5, private_key,
                162259276829213363391578010288127)

    def _dh_compute_shared_key(self, public_key, private_key):
        """
        Given public and private keys, compute the shared key
        """

        return self._mod_exp(public_key, private_key,
                162259276829213363391578010288127)

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

    def _make_b64_password(self, key, password):

        cmd = ["openssl", "enc", "-aes-128-cbc", "-a", "-nosalt",
                "-pass", "pass:%s" % key]

        p = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.stdin.write(password)
        p.stdin.close()
        b64_pass = p.stdout.read().rstrip()
        err = p.stderr.read()
        del p

        return b64_pass

    def test_1_same_shared_key(self):
        """Test 'password' command computes shared key correctly"""

        self.pw_inst._wipe_key()

        our_private_key = self._make_private_key()
        our_public_key = self._dh_compute_public_key(our_private_key)

        their_private_key = self.pw_inst._make_private_key()
        their_public_key = self.pw_inst._dh_compute_public_key(
                their_private_key)

        self.assertEqual(self._dh_compute_shared_key(
                            their_public_key, our_private_key),
                        self.pw_inst._dh_compute_shared_key(
                            our_public_key, their_private_key))

    def test_2_password_matches(self):
        """Test 'password' comamnd decoding password correctly"""

        test_passwd = "TeStPaSsWoRd"

        self.pw_inst._wipe_key()

        our_private_key = self._make_private_key()
        our_public_key = self._dh_compute_public_key(our_private_key)

        resp = self.pw_inst.keyinit_cmd(our_public_key)

        self.assertEqual(resp[0], "D0")

        their_public_key = int(resp[1])

        shared_key = self._dh_compute_shared_key(their_public_key,
                our_private_key)

        our_b64passwd = self._make_b64_password(shared_key, test_passwd)

        their_passwd = self.pw_inst._decode_password(our_b64passwd)

        self.assertEqual(test_passwd, their_passwd)

    def test_3_password_without_keyinit(self):
        """Test the 'password' command without keyinit first"""

        self.pw_inst._wipe_key()

        test_passwd = "PaSsWoRdTeSt"
        our_b64passwd = self._make_b64_password(123456789, test_passwd)

        resp = self.commands.run_command('password', our_b64passwd)
        expected = (500, "Password without key exchange")
        self.assertEqual(resp, expected)

    def test_4_password_with_bogus_data(self):
        """Test the 'password' command with bogus data"""

        resp = self.commands.run_command('password', 'kjadfkjaf')
        expected = (500, "Couldn't decode base64 data")
        self.assertEqual(resp, expected)

    def test_5_password_with_valid_data(self):
        """Test the 'password' command with valid data"""

        test_passwd = "mEoW4567"

        our_private_key = self._make_private_key()
        our_public_key = self._dh_compute_public_key(our_private_key)

        resp = self.commands.run_command('keyinit', our_public_key)

        self.assertEqual(resp[0], "D0")

        their_public_key = int(resp[1])

        shared_key = self._dh_compute_shared_key(their_public_key,
                our_private_key)

        our_b64_passwd = self._make_b64_password(shared_key, test_passwd)

        resp = self.commands.run_command('password', our_b64_passwd)

        self.assertEqual(resp[0], 0)

if __name__ == "__main__":
    agent_test.main()
