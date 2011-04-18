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
using System.Collections.Generic;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Commands
{
    public class XentoolsUpdate : IExecutableCommand
    {
        private readonly ISleeper _sleeper;
        private readonly IDownloader _downloader;
        private readonly IChecksumValidator _checksumValidator;
        private readonly IUnzipper _unzipper;
        private readonly IInstaller _installer;
        private readonly IFinalizer _finalizer;
        private readonly IServiceRestarter _serviceRestarter;
        private readonly IConnectionChecker _connectionChecker;
        private readonly IAgentUpdateMessageHandler _agentUpdateMessageHandler;
        private readonly ILogger _logger;

        public XentoolsUpdate(ISleeper sleeper, IDownloader downloader, IChecksumValidator checksumValidator, IUnzipper unzipper, IInstaller installer, IFinalizer finalizer, IServiceRestarter _serviceRestarter,IConnectionChecker connectionChecker, IAgentUpdateMessageHandler agentUpdateMessageHandler, ILogger logger)
        {
            _sleeper = sleeper;
            _downloader = downloader;
            _checksumValidator = checksumValidator;
            _unzipper = unzipper;
            _installer = installer;
            _finalizer = finalizer;
            this._serviceRestarter = _serviceRestarter;
            _connectionChecker = connectionChecker;
            _agentUpdateMessageHandler = agentUpdateMessageHandler;
            _logger = logger;
        }

        public ExecutableResult Execute(string value)
        {
            try
            {
                Statics.ShouldPollXenStore = false;
                _logger.Log(String.Format("XenTools Update value: {0}\r\nWill resume in 60 seconds", value));
                _sleeper.Sleep(60);
                _connectionChecker.Check();
                var agentUpdateInfo = _agentUpdateMessageHandler.Handle(value);
                _downloader.Download(agentUpdateInfo.url, Constants.XenToolsReleasePackage);
                _checksumValidator.Validate(agentUpdateInfo.signature, Constants.XenToolsReleasePackage);
                _unzipper.Unzip(Constants.XenToolsReleasePackage, Constants.XenToolsUnzipPath, "");
                _installer.Install(new Dictionary<string, string>
                                       {
                                           {Constants.XenToolsSetupExecutablePath,
                                               String.Format("/S /norestart /D={0}", Constants.XenToolsPath)}
                                       });
                _serviceRestarter.Restart("xensvc");
                _serviceRestarter.Restart("XenServerVssProvider");
                Statics.ShouldPollXenStore = true;
                return new ExecutableResult();
            }
            catch (Exception ex)
            {

                _logger.Log(String.Format("Exception was : {0}\nStackTrace Was: {1}", ex.Message, ex.StackTrace));
                return new ExecutableResult { Error = new List<string> { "Update failed" }, ExitCode = "1" };
            }
            finally
            {
                _finalizer.Finalize(new List<string>{Constants.XenToolsUnzipPath,Constants.XenToolsReleasePackage});
            }
        }

    }
}