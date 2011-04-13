using NUnit.Framework;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class XenDataLocationSpec
    {
        [Test]
        public void should_combine_location_values()
        {
            Assert.AreEqual("Key1/Key2/Key3", Constants.Combine("Key1", "Key2", "Key3")) ;
        }
    }
}
