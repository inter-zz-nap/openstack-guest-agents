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

using ICSharpCode.SharpZipLib.Zip;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IUnzipper
    {
        void Unzip(string zipFileName, string targetDirectory, string fileFilter);
    }

    public class Unzipper : IUnzipper
    {
        private readonly ILogger _logger;

        public Unzipper(ILogger logger)
        {
            _logger = logger;
        }

        public void Unzip(string zipFileName, string targetDirectory, string fileFilter)
        {
            _logger.Log("Unzipping files");
            new FastZip().ExtractZip(zipFileName, targetDirectory, fileFilter);
            _logger.Log("Unzipping files complete");
        }
    }
}