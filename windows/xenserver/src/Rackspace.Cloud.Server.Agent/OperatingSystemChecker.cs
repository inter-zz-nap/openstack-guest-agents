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

namespace Rackspace.Cloud.Server.Agent
{
    public interface IOperatingSystemChecker
    {
        bool IsWindows2008 { get; }
        bool IsWindows2008SP2 { get; }
        bool IsWindows2008R2 { get; }
    }

    public class OperatingSystemChecker : IOperatingSystemChecker
    {
        private const int WINDOWS_2008_MAJOR_BUILD_NUMBER = 6;
        private const int WINDOWS_2008_R2_MINOR_BUILD_NUMBER = 1;
        private const int WINDOWS_2008_SP2_MINOR_BUILD_NUMBER = 0;

        public bool IsWindows2008
        {
            get { return IsWindows2008R2 || IsWindows2008SP2; }
        }

        public bool IsWindows2008SP2
        {
            get
            {
                return Environment.OSVersion.Version.Major == WINDOWS_2008_MAJOR_BUILD_NUMBER &&
                    Environment.OSVersion.Version.Minor == WINDOWS_2008_SP2_MINOR_BUILD_NUMBER;
            }
        }

        public bool IsWindows2008R2
        {
            get
            {
                return Environment.OSVersion.Version.Major == WINDOWS_2008_MAJOR_BUILD_NUMBER &&
                     Environment.OSVersion.Version.Minor == WINDOWS_2008_R2_MINOR_BUILD_NUMBER;
            }
        }
    }
}