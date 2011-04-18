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
using System.Text;
using Rackspace.Cloud.Server.Agent.Utilities;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Actions
{
    public interface IFileCreator
    {
        void CreateFile(FileInfo fileInfo);
        void HandleBackup(string filePath);
    }

    public class FileCreator : IFileCreator
    {
        private readonly ILogger _logger;

        public FileCreator(ILogger logger)
        {
            _logger = logger;
        }

        public void CreateFile(FileInfo fileInfo)
        {
            if (!fileInfo.Path.IsValidFilePath()) 
                throw new Exception("File path invalid: " + fileInfo.Path);
            if (Array.Find(Environment.GetLogicalDrives(), x => x.ToLower() == Path.GetPathRoot(fileInfo.Path.ToLower())) == null)
                throw new Exception("Drive does not exist: " + Path.GetPathRoot(fileInfo.Path));
            if (!Directory.Exists(Path.GetDirectoryName(fileInfo.Path)))
                Directory.CreateDirectory(Path.GetDirectoryName(fileInfo.Path));

            var content = fileInfo.Content;
            HandleBackup(fileInfo.Path);

            using (var fs = File.Create(fileInfo.Path, 1024))
            {
                var info = new UTF8Encoding(true).GetBytes(content);
                fs.Write(info, 0, info.Length);
                _logger.Log(String.Format("File '{0}' created successfully", fileInfo.Path));
            }    
        }

        public void HandleBackup(string filePath)
        {
            if(!File.Exists(filePath)) return;
            var fileExtension = String.Format(".bak.{0:dMyyyyHHmmss}", DateTime.Now);
            var path = String.Format("{0}{1}", filePath, fileExtension);
            File.Copy(filePath, path); 
        }
    }
}
