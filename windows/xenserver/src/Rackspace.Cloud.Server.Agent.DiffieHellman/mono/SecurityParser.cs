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
// Mono.Xml.SecurityParser.cs class implementation
//
// Author:
//	Sebastien Pouliot (spouliot@motus.com)
//
// (C) 2003 Motus Technologies Inc. (http://www.motus.com)
//

using System;
using System.Collections;
using System.Security;

namespace Mono.Xml {

	// convert an XML document into SecurityElement objects
	[CLSCompliant(false)]
	internal class SecurityParser : MiniParser, MiniParser.IHandler, MiniParser.IReader {

		private SecurityElement root;

		public SecurityParser () : base () 
		{
			stack = new Stack ();
		}

		public void LoadXml (string xml) 
		{
			root = null;
			xmldoc = xml;
			pos = 0;
			stack.Clear ();
			Parse (this, this);
		}

		public SecurityElement ToXml () 
		{
			return root;
		}

		// IReader

		private string xmldoc;
		private int pos;

		public int Read () 
		{
			if (pos >= xmldoc.Length)
				return -1;
			return (int) xmldoc [pos++];
		}

		// IHandler

		private SecurityElement current;
		private Stack stack;

		public void OnStartParsing (MiniParser parser) {}

		public void OnStartElement (string name, MiniParser.IAttrList attrs) 
		{
			SecurityElement newel = new SecurityElement (name); 
			if (root == null) {
				root = newel;
				current = newel;
			}
			else {
				SecurityElement parent = (SecurityElement) stack.Peek ();
				parent.AddChild (newel);
			}
			stack.Push (newel);
			current = newel;
			// attributes
			int n = attrs.Length;
			for (int i=0; i < n; i++)
				current.AddAttribute (attrs.GetName (i), attrs.GetValue (i));
		}

		public void OnEndElement (string name) 
		{
			current = (SecurityElement) stack.Pop ();
		}

		public void OnChars (string ch) 
		{
			current.Text = ch;
		}

		public void OnEndParsing (MiniParser parser) {}
	}
}
