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

using System.Security.Cryptography;
using Mono.Math;
using StructureMap;

namespace Rackspace.Cloud.Server.DiffieHellman {
    public class DiffieHellmanManaged : IDiffieHellman {
        private BigInteger _p;
        private BigInteger _g;
        private BigInteger _x;
        private bool _disposed;

        public DiffieHellmanManaged(string prime, string generator, string secret) {
            Initialize(BigInteger.Parse(prime), BigInteger.Parse(generator), secret == null ? null : BigInteger.Parse(secret));
        }

        [DefaultConstructor]
        public DiffieHellmanManaged(string prime, string generator) : this(prime, generator, null) { }

        ~DiffieHellmanManaged() { Dispose(); }

        private void Initialize(BigInteger p, BigInteger g, BigInteger x) {
            if (!p.isProbablePrime() || g <= 0 || g >= p)
                throw new CryptographicException("Inputs p or g are not as expected. P probably isn't a prime or G is less than zero or more than P.");

            if(x != null) {
                _x = x;
            } else {
                var pMinus1 = p - 1;
                var secretLen = p.bitCount();
                for (_x = BigInteger.genRandom(secretLen); _x >= pMinus1 || _x == 0; _x = BigInteger.genRandom(secretLen)) { }
            }

            _p = p;
            _g = g;
        }

        private void Dispose() {
            if (!_disposed) {
                _p.Clear(); _g.Clear(); _x.Clear();
            }
            
            _disposed = true;
        }

        public string CreateKeyExchange() {
            var y = _g.modPow(_x, _p);
            var initialKey = y.ToString();
            y.Clear();
            
            return initialKey;
        }

        public string DecryptKeyExchange(string key) {
            var pvr = BigInteger.Parse(key);
            var z = pvr.modPow(_x, _p);
            var finalKey = z.ToString();
            z.Clear();
            
            return finalKey;
        }
    }
}