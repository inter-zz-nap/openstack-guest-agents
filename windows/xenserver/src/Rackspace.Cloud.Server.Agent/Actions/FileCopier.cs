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
using System.IO;
using System.Linq;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IFileCopier
    {
        void CopyFiles(string fromPath, string toPath, ILogger logger);
    }

    public class FileCopier : IFileCopier
    {
        public void CopyFiles(string fromPath, string toPath, ILogger logger)
        {
            if(!Directory.Exists(fromPath))
                throw new DirectoryNotFoundException(String.Format("{0} does not exist", fromPath));

            foreach (var file in Directory.GetFiles(fromPath).Where(file => !file.Contains(".zip")))
            {
                //logger.Log(String.Format("Copying file {0} to {1}", file, Path.Combine(toPath,Path.GetFileName(file))));
                File.Copy(file, Path.Combine(toPath, Path.GetFileName(file)), true);
            }
        }
    }
}
