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

using Rackspace.Cloud.Server.Agent.Interfaces;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IActivateWindowsUsingKms {
        void Execute(string kmsServerAndPort);
    }

    public class ActivateWindowsUsingKms : IActivateWindowsUsingKms {
        private readonly IExecutableProcessQueue _executableProcessQueue;
        private readonly IOperatingSystemChecker _operatingSystemChecker;

        public ActivateWindowsUsingKms(IExecutableProcessQueue executableProcessQueue, IOperatingSystemChecker operatingSystemChecker)
        {
            _executableProcessQueue = executableProcessQueue;
            _operatingSystemChecker = operatingSystemChecker;
        }

        public void Execute(string kmsServerAndPort) {
            if(!_operatingSystemChecker.IsWindows2008) return;

            _executableProcessQueue
                .Enqueue("cscript", Constants.KmsActivationVbsPath + " /skms " + kmsServerAndPort)
                .Enqueue("cscript", Constants.KmsActivationVbsPath + " /ato")
                .Go();
        }
    }
}