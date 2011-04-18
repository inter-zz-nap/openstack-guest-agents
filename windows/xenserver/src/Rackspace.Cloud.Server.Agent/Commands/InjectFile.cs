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
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Commands
{
    public class InjectFile : IExecutableCommand
    {
        private readonly IInjectFileMessageHandler _injectFileMessageHandler;
        private readonly IFileCreator _fileCreator;
        private readonly ILogger _logger;
        private FileInfo _fileInfo;

        public InjectFile(IInjectFileMessageHandler injectFileMessageHandler, IFileCreator fileCreator, ILogger logger)
        {
            _injectFileMessageHandler = injectFileMessageHandler;
            _fileCreator = fileCreator;
            _logger = logger;
        }

        public ExecutableResult Execute(string value)
        {
            try
            {
                _logger.Log(String.Format("Getting file injection information from {0}", value));
                _fileInfo = _injectFileMessageHandler.Handle(value);
                _logger.Log(String.Format("Injection File Path: {0}", _fileInfo.Path));

                _fileCreator.CreateFile(_fileInfo);    
            }
            catch(Exception e)
            {
                _logger.Log("Exception was : " + e.Message + "\nStackTrace Was: " + e.StackTrace);
                throw new UnsuccessfulCommandExecutionException("File injection failed: " + e.Message,
                    new ExecutableResult { ExitCode = "1" });
            }
            

            return new ExecutableResult();
        }
    }
}