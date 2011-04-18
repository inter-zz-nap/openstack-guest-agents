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

using Rackspace.Cloud.Server.Agent.Configuration;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IConnectionChecker
    {
        void Check();
    }

    public class ConnectionChecker : IConnectionChecker {
        public void Check()
        {
            try
            {
                System.Net.Dns.GetHostEntry("www.google.com");
            }
            catch
            {
                throw new UnsuccessfulCommandExecutionException(
                    "No Network Connection available to update Agent, please try again later!", 
                    new ExecutableResult { ExitCode = "1" }
                    );
            }
        }
    }
}