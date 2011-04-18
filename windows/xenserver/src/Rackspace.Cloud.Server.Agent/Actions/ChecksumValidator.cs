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
using System.IO;
using System.Security.Cryptography;
using System.Text;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IChecksumValidator
    {
        void Validate(string md5Checksum, string filePath);
    }

    public class ChecksumValidator : IChecksumValidator
    {
        private readonly ILogger _logger;

        public ChecksumValidator(ILogger logger)
        {
            _logger = logger;
        }

        public void Validate(string md5Checksum, string filePath)
        {
            if (!File.Exists(filePath))
            {
                throw new ArgumentException(string.Format("Filename '{0}' does not exist.", filePath));
            }

            _logger.Log("Verifying checksum of downloaded item ...");

            using (var fstream = new FileStream(filePath, FileMode.Open))
            {
                var hash = new MD5CryptoServiceProvider().ComputeHash(fstream);

                var result = new StringBuilder();
                foreach (var b in hash)
                    result.AppendFormat("{0:x2}", b);

                var checksum = result.ToString().ToUpper();

                if (checksum != md5Checksum.ToUpper())
                {
                    throw new Exception(String.Format("Checksum verification failed. Incorrect checksum: {0}", checksum));
                }
            }

            _logger.Log("Checksum Validated.");
        }
    }
}