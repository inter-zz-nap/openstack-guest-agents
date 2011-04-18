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
using System.Collections.Generic;
using System.IO;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;

namespace Rackspace.Cloud.Server.Agent.Utilities
{
    public interface ISystemInformation
    {
        Dictionary<string, string> getDriveWithBootConfigurationDataStore();
        string getWindowsBootLoaderUniqueIdentifer(string output);
        string getDriveLetterWithOriginalWindowsFolder();
        List<string> LogicalDrives { get; set; }
    }

    public class SystemInformation : ISystemInformation
    {
        private readonly IExecutableProcess _execProcess;
        private readonly ILogger _logger;
        private const string C_DRIVE = @"C:\";
        private const string WINDOWS_BOOT_LOADER_TEXT = "Windows Boot Loader";
        public const string DRIVE_KEY = "drive";
        public const string UNIQUE_IDENTIFIER_KEY = "uniqueidentifier";

        public SystemInformation(IExecutableProcess execProcess, ILogger logger)
        {
            _execProcess = execProcess;
            _logger = logger;
        }

        public IList<string> GetLogicalDrives()
        {
            var driveArray = Environment.GetLogicalDrives();
            var currentDriveList = new List<string>(driveArray.Length);
            currentDriveList.AddRange(driveArray);
            var drives = LogicalDrives ?? currentDriveList;
            drives.Remove(C_DRIVE);
            return drives;    
        }

        public List<string> LogicalDrives { get; set; }

        public Dictionary<string, string> getDriveWithBootConfigurationDataStore()
        {
            var driveAndUniqueIdentifier = new Dictionary<string, string>();
            foreach (var drive in GetLogicalDrives())
            {
                var operation = new ExecutableOperation 
                { Command = "bcdedit", Arguments = "/store " + drive + "boot\\bcd" };
                var executableResult = _execProcess.Run(operation.Command, operation.Arguments);

                if (!executableResult.Output.Value().Contains(WINDOWS_BOOT_LOADER_TEXT))
                    continue;

                _logger.Log(String.Format("Windows Boot Loader Drive: {0}", drive));
                driveAndUniqueIdentifier.Add(DRIVE_KEY, drive);
                var uniqueIdentifier = getWindowsBootLoaderUniqueIdentifer
                    (executableResult.Output.Value());
                _logger.Log(String.Format("Windows Boot Loader Unique Identifier: {0}", uniqueIdentifier));
                driveAndUniqueIdentifier.Add(UNIQUE_IDENTIFIER_KEY, uniqueIdentifier);
                break;
            }
            if(!driveAndUniqueIdentifier.ContainsKey(DRIVE_KEY) ||
                !driveAndUniqueIdentifier.ContainsKey(UNIQUE_IDENTIFIER_KEY) ||
                String.IsNullOrEmpty(driveAndUniqueIdentifier[DRIVE_KEY]) ||
                String.IsNullOrEmpty(driveAndUniqueIdentifier[UNIQUE_IDENTIFIER_KEY]))
                throw new UnsuccessfulCommandExecutionException
                    ("BCD boot configuration data store not present",
                    new ExecutableResult{ExitCode = "0"});
            return driveAndUniqueIdentifier;
        }

        public string getWindowsBootLoaderUniqueIdentifer(string output)
        {
            if (!output.Contains(WINDOWS_BOOT_LOADER_TEXT) ||
                !output.Contains("{") || !output.Contains("}"))
                throw new UnsuccessfulCommandExecutionException
                    ("BCD data store output does not have Windows Boot Loader information",
                    new ExecutableResult { ExitCode = "0" });
            var windowsBootLoaderTextIndex = output.IndexOf(WINDOWS_BOOT_LOADER_TEXT);
            var firstCurlyBracketIndex = output.IndexOf("{", windowsBootLoaderTextIndex);
            var closingCurlyBracketIndex = output.IndexOf("}", firstCurlyBracketIndex);
            var identifierLength = closingCurlyBracketIndex - firstCurlyBracketIndex + 1;
            return output.Substring(firstCurlyBracketIndex, identifierLength);
        }

        public string getDriveLetterWithOriginalWindowsFolder()
        {
            var driveWithOriginalWindowsFolder = "";
            foreach (var drive in GetLogicalDrives())
            {
                if (drive == @"C:\") continue;
                if (!Directory.Exists(drive + "Windows")) continue;
                driveWithOriginalWindowsFolder = drive.Substring(0, drive.Length-1);
                break;
            }
            return driveWithOriginalWindowsFolder;
        }
    }
}