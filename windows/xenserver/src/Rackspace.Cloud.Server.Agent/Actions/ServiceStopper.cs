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
    public interface IServiceStopper
    {
        void Stop(string serviceName);
    }

    public class ServiceStopper : IServiceStopper
    {
        private readonly ILogger _logger;

        public ServiceStopper(ILogger logger)
        {
            _logger = logger;
        }

        public void Stop(string serviceName)
        {
            _logger.Log(String.Format("Stopping Service '{0}' ...", serviceName));

            var serviceController = new ServiceController(serviceName);
            if (serviceController.Status == ServiceControllerStatus.Stopped)
            {
                _logger.Log(String.Format("Service '{0}' already stopped.", serviceName));
                return;
            }

            if (!serviceController.CanStop)
                throw new ApplicationException(
                    String.Format("Service '{0}' can't be stop at this time, please try again later", serviceName));

            serviceController.Stop();
            serviceController.WaitForStatus(ServiceControllerStatus.Stopped);

            serviceController.Close();

            _logger.Log(String.Format("Service '{0}' successfully stopped.", serviceName));
        }
    }
}