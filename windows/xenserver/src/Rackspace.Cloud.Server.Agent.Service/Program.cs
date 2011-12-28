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

using System.ServiceProcess;
using System;
using System.Reflection;

namespace Rackspace.Cloud.Server.Agent.Service {
    static class Program {
        static void Main(string[] args) {
            ServiceBase[] ServicesToRun;
            ServicesToRun = new ServiceBase[] 
                                { 
                                    new Agent.Service.AgentService() 
                                };
            if (Environment.UserInteractive)
            {
                // Enable debugging from the command-line or Visual Studio
                // Only run this code if we are run from the command line (or from the Visual Studio debugger)
                // This is a common pattern for debugging Windows NT Services:
                // http://stackoverflow.com/questions/2629720/debug-windows-service
                //
                // Another approach would be to use the Windows Service Helper from CodePlex:
                // http://windowsservicehelper.codeplex.com/
                Type type = typeof(ServiceBase);
                BindingFlags flags = BindingFlags.Instance | BindingFlags.NonPublic;
                MethodInfo method = type.GetMethod("OnStart", flags);

                // Handle the case where we might have multiple service entry points by spinning through
                // all of them
                foreach (ServiceBase service in ServicesToRun)
                {
                    method.Invoke(service, new object[] { args });
                }
                Console.WriteLine("Press any key to exit");
                Console.Read();
                foreach (ServiceBase service in ServicesToRun)
                {
                    service.Stop();
                }
            }
            else
            {
                // This is what normally runs when we are run as a service
                ServiceBase.Run(ServicesToRun);
            }
        }
    }
}