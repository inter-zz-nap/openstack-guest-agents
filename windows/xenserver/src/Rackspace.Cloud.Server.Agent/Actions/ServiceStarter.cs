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
using System.ServiceProcess;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IServiceStarter
    {
        void Start(string serviceName);
    }

    public class ServiceStarter : IServiceStarter
    {
        private readonly ILogger _logger;

        public ServiceStarter(ILogger logger)
        {
            _logger = logger;
        }

        public void Start(string serviceName)
        {
            _logger.Log(String.Format("Starting '{0}' Service ...", serviceName));
            var serviceController = new ServiceController(serviceName);
            if (serviceController.Status == ServiceControllerStatus.Running)
            {
                _logger.Log(String.Format("'{0}' service already started.", serviceName));
                return;
            }

            serviceController.Start();
            serviceController.WaitForStatus(ServiceControllerStatus.Running);

            serviceController.Close();
            _logger.Log(String.Format("Service '{0}' started and now running ...", serviceName));
        }
    }
}