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
// Mono.Math.Prime.Generator.NextPrimeFinder.cs - Prime Generator
//
// Authors:
//	Ben Maurer
//
// Copyright (c) 2003 Ben Maurer. All rights reserved
//

using System;

namespace Mono.Math.Prime.Generator {

	/// <summary>
	/// Finds the next prime after a given number.
	/// </summary>
	[CLSCompliant(false)]
	internal class NextPrimeFinder : SequentialSearchPrimeGeneratorBase {
		
		protected override BigInteger GenerateSearchBase (int bits, object Context) 
		{
			if (Context == null) throw new ArgumentNullException ("Context");
			BigInteger ret = new BigInteger ((BigInteger)Context);
			ret.setBit (0);
			return ret;
		}
	}
}
