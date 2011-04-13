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

using System.Timers;
using Rackspace.Cloud.Server.Agent.Interfaces;

namespace Rackspace.Cloud.Server.Agent
{
    public class ProdTimer : ITimer {
        private readonly Timer _timer;
        private ProdTimer(Timer timer) {
            _timer = timer;
        }

        public ProdTimer()
            : this(new Timer()) {
            }

        public bool Enabled {
            get { return _timer.Enabled; }
            set { _timer.Enabled = value; }
        }

        public double Interval {
            get { return _timer.Interval; }
            set { _timer.Interval = value; }
        }

        public void Elapsed(ElapsedEventHandler method) {
            _timer.Elapsed += method;
        }
    }
}