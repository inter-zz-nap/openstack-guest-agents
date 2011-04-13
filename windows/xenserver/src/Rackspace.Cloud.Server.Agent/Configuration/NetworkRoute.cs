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

namespace Rackspace.Cloud.Server.Agent.Configuration {
    public class NetworkRoute : IEquatable<NetworkRoute>
    {
        public string route { get; set; }
        public string netmask { get; set; }
        public string gateway { get; set; }

        public bool Equals(NetworkRoute other)
        {
            if (ReferenceEquals(null, other)) return false;
            if (ReferenceEquals(this, other)) return true;
            return Equals(other.route, route) && Equals(other.netmask, netmask) && Equals(other.gateway, gateway);
        }

        public override bool Equals(object obj)
        {
            if (ReferenceEquals(null, obj)) return false;
            if (ReferenceEquals(this, obj)) return true;
            if (obj.GetType() != typeof (NetworkRoute)) return false;
            return Equals((NetworkRoute) obj);
        }

        public override int GetHashCode()
        {
            unchecked
            {
                int result = (route != null ? route.GetHashCode() : 0);
                result = (result*397) ^ (netmask != null ? netmask.GetHashCode() : 0);
                result = (result*397) ^ (gateway != null ? gateway.GetHashCode() : 0);
                return result;
            }
        }
    }
}