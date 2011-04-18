// Copyright 2011 OpenStack LLC.
// All Rights Reserved.
//
//    Licensed under the Apache License, Version 2.0 (the "License"); you may
//    not use this file except in compliance with the License. You may obtain
//    a copy of the License at
//
//         http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
//    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
//    License for the specific language governing permissions and limitations
//    under the License.

using System;
using System.Security.Cryptography;
using System.Text;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Security {
    public class Encryption {
        public static string Decrypt(byte[] encryptedData, string sharedKey, byte[] salt) {
            var aesData = encryptedData;
            var password = Encoding.UTF8.GetBytes(sharedKey);
            var md5 = MD5.Create();

            var preKeyLength = password.Length + salt.Length;
            var preKey = new byte[preKeyLength];

            Buffer.BlockCopy(password, 0, preKey, 0, password.Length);
            Buffer.BlockCopy(salt, 0, preKey, password.Length, salt.Length);

            var key = md5.ComputeHash(preKey);
            var preIVLength = key.Length + preKeyLength;
            var preIV = new byte[preIVLength];

            Buffer.BlockCopy(key, 0, preIV, 0, key.Length);
            Buffer.BlockCopy(preKey, 0, preIV, key.Length, preKey.Length);

            var iv = md5.ComputeHash(preIV);
            md5.Clear();

            // Decrypt using AES
            var rijndael = new RijndaelManaged
                               {
                                   Mode = CipherMode.CBC,
                                   Padding = PaddingMode.None,
                                   KeySize = 128,
                                   BlockSize = 128,
                               };

            var rijndaelDecryptor = rijndael.CreateDecryptor(key, iv);
            var clearData = rijndaelDecryptor.TransformFinalBlock(aesData, 0, aesData.Length);
            var clearText = new ASCIIEncoding().GetString(clearData);

            ////When decrypted it comes back with a new line character at the end, whcih it gets rid of
            return clearText.SplitOnNewLine().First();
        }
    }
}