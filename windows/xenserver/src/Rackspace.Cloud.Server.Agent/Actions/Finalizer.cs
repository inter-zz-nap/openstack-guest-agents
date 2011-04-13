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

using System.Collections.Generic;
using System.IO;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IFinalizer
    {
        void Finalize(IList<string> paths);    
    }

    public class Finalizer : IFinalizer
    {
        private readonly ILogger _logger;

        public Finalizer(ILogger logger)
        {
            _logger = logger;
        }

        public void Finalize(IList<string> paths)
        {
            _logger.Log("Cleaning temp folders and files ... ");
            foreach(var path in paths)
            {
                if (Directory.Exists(path)) Directory.Delete(path, true);
                if (File.Exists(path)) File.Delete(path);    
            }
            _logger.Log("Update Complete!");
        }
    }
}