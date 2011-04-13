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

using log4net;
using log4net.Config;

namespace Rackspace.Cloud.Server.Common.Logging
{
    public static class LogManager {
        private static ILog _logmanager;

        static LogManager()
        {
            ShouldBeLogging = true;
        }

        public static ILog Instance {
            get {
                if (_logmanager == null) {
                    XmlConfigurator.Configure();
                    _logmanager = log4net.LogManager.GetLogger("AgentService");
                }

                return _logmanager;
            }
        }

        public static bool ShouldBeLogging { get; set; }
    }
}