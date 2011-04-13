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

//
// Mono.Math.Prime.ConfidenceFactor.cs - Confidence factor for prime generation
//
// Authors:
//	Ben Maurer
//
// Copyright (c) 2003 Ben Maurer. All rights reserved
//

using System;

namespace Mono.Math.Prime {
	/// <summary>
	/// A factor of confidence.
	/// </summary>
	internal enum ConfidenceFactor {
		/// <summary>
		/// Only suitable for development use, probability of failure may be greater than 1/2^20.
		/// </summary>
		ExtraLow,
		/// <summary>
		/// Suitable only for transactions which do not require forward secrecy.  Probability of failure about 1/2^40
		/// </summary>
		Low,
		/// <summary>
		/// Designed for production use. Probability of failure about 1/2^80.
		/// </summary>
		Medium,
		/// <summary>
		/// Suitable for sensitive data. Probability of failure about 1/2^160.
		/// </summary>
		High,
		/// <summary>
		/// Use only if you have lots of time! Probability of failure about 1/2^320.
		/// </summary>
		ExtraHigh,
		/// <summary>
		/// Only use methods which generate provable primes. Not yet implemented.
		/// </summary>
		Provable
	}
}
