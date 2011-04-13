using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs.RestartServiceSpec
{
    [TestFixture]
    public class When_restart_a_service
    {
        private IServiceRestarter _serviceRestarter;
        private IServiceStopper _serviceStopper;
        private IServiceStarter _serviceStarter;
        private ILogger logger;

        [SetUp]
        public void Setup()
        {
            _serviceStopper = MockRepository.GenerateMock<IServiceStopper>();
            _serviceStarter = MockRepository.GenerateMock<IServiceStarter>();
            logger = MockRepository.GenerateMock<ILogger>();
            _serviceRestarter = new ServiceRestarter(_serviceStopper, _serviceStarter, logger);
        }

        [Test]
        public void should_stop_then_start_the_service()
        {
            _serviceStopper.Expect(x => x.Stop("testServiceName"));
            _serviceStarter.Expect(x => x.Start("testServiceName"));

            _serviceRestarter.Restart("testServiceName");
        }
    }
}