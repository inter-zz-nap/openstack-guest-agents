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
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IServiceRestarter
    {
        void Restart(string serviceName);
    }

    public class ServiceRestarter : IServiceRestarter
    {
        private readonly IServiceStopper _serviceStopper;
        private readonly IServiceStarter _serviceStarter;
        private readonly ILogger _logger;

        public ServiceRestarter(IServiceStopper _serviceStopper, IServiceStarter _serviceStarter, ILogger logger)
        {
            this._serviceStopper = _serviceStopper;
            this._serviceStarter = _serviceStarter;
            _logger = logger;
        }

        public void Restart(string serviceName)
        {
            _logger.Log(String.Format("Restarting service '{0}' ...", serviceName));
            _serviceStopper.Stop(serviceName);
            _serviceStarter.Start(serviceName);
            _logger.Log(String.Format("Restart of service '{0}' successful.", serviceName));
        }
    }
}