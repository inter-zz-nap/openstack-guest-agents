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
using System.Diagnostics;
using System.IO;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IVersionChecker
    {
        string Check(string filePath);
    }

    public class VersionChecker : IVersionChecker
    {
        private readonly ILogger _logger;

        public VersionChecker(ILogger logger)
        {
            _logger = logger;
        }

        public string Check(string filePath)
        {
            _logger.Log(string.Format("Checking version of '{0}'", filePath));
            string result;
            try
            {
                result = FileVersionInfo.GetVersionInfo(filePath).ProductVersion;
            }
            catch(FileNotFoundException e)
            {
                _logger.Log(String.Format("Exception was : {0}\nStackTrace Was: {1}", e.Message, e.StackTrace));
                result = String.Format("File {0} not found", filePath);
            }
            catch(Exception e)
            {
                _logger.Log(String.Format("Exception was : {0}\nStackTrace Was: {1}", e.Message, e.StackTrace));
                result = String.Format("Error trying to check version of {0}", filePath);
            }
            return result;
            
        }
    }
}