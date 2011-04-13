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
using System.Configuration;

namespace Rackspace.Cloud.Server.Common.Configuration {
    public static class SvcConfiguration
    {
        public static string RemotingUriHost {
            get { return ConfigurationManager.AppSettings["RemotingUriHost"]; }
        }

        public static string RemotingUri {
            get { return ConfigurationManager.AppSettings["RemotingUri"]; }
        }

        public static int RemotingPort {
            get { return Convert.ToInt32(ConfigurationManager.AppSettings["RemotingPort"]); }
        }

        public static string AgentPath {
            get { return ConfigurationManager.AppSettings["AgentPath"]; }
        }

        public static string AgentUpdaterPath {
            get { return ConfigurationManager.AppSettings["AgentUpdaterPath"]; }
        }
        
        public static string AgentVersionUpdatesPath {
            get { return ConfigurationManager.AppSettings["AgentVersionUpdatesPath"]; }
        }
    }
}
