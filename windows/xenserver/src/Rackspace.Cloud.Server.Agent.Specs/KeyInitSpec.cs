using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.DiffieHellman;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class    KeyInitSpec
    {
        private IDiffieHellman _diffieHellman;

        [Test]  
        public void should_create_the_key_exchange()
        {
            _diffieHellman = MockRepository.GenerateMock<IDiffieHellman>();
            _diffieHellman.Stub(x => x.CreateKeyExchange()).Repeat.Once().Return("30");

            var executableResult = new KeyInit(_diffieHellman).Execute("howdydoody");

            Assert.AreEqual(Constants.SuccessfulKeyInit, executableResult.ExitCode);

            _diffieHellman.AssertWasCalled(x => x.CreateKeyExchange());
        }
    }
}