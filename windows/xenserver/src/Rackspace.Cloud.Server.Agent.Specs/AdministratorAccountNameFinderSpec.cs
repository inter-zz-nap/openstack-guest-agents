using NUnit.Framework;

namespace Rackspace.Cloud.Server.Agent.Specs {

    [TestFixture]
    public class AdministratorAccountNameFinderSpec {

        [Test]
        public void Should_verify_the_local_administrator_account_name() {
            Assert.IsNotNull(new AdministratorAccountNameFinder().Find());
        }
        
    }
}