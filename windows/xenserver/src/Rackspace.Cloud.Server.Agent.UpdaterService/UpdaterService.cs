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

namespace Rackspace.Cloud.Server.Agent.UpdaterService {
    public partial class UpdaterService : ServiceBase {
        private readonly HostUpdater _hostUpdater;
        private readonly Logger _logger;

        public UpdaterService() {
            InitializeComponent();
            _logger = new Logger();
            _hostUpdater = new HostUpdater(_logger);
        }

        protected override void OnStart(string[] args) {
            try {
                _hostUpdater.OnStart();
            } catch (Exception ex) {
                _logger.Log("Exception was : " + ex.Message + "\nStackTrace Was: " + ex.StackTrace);
            }
        }

        protected override void OnStop() {
            _hostUpdater.OnStop();
        }
    }
}
