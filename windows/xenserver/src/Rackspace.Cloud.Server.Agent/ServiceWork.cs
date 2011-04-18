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
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent {
    public class ServiceWork {
        private readonly ITimer _timer;
        private readonly ICommandQueue _queue;

        public ServiceWork(ITimer timer, ICommandQueue queue) {
            _timer = timer;
            _queue = queue;
        }

        public void Do() {
            _timer.Enabled = false;
            _queue.Work();
            if(Statics.ShouldPollXenStore)  _timer.Enabled = true;
        }
    }
}