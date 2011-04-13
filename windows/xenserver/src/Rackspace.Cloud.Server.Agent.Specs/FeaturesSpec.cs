using System;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class FeaturesSpec
    {
        [Test]
        public void should_return_comma_delimited_list_of_features()
        {
            var expected = "";
            foreach (var val in Enum.GetValues(typeof(Utilities.Commands)))
            {
                if (val.ToString() == "features") continue;
                expected += val + ",";
            }
            expected = expected.Substring(0, expected.Length - 1);
            expected = expected.Replace(Environment.NewLine, "");
            var actual = new Features().Execute(null);
            Assert.That(actual.Output.Value(), Is.EqualTo(expected + "\r\n"));
        }

    }
}