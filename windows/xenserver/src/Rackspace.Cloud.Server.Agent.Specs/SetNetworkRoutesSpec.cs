using System.Collections.Generic;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class SetNetworkRoutesSpec : SetNetworkInterfaceSpecBase
    {
        private SetNetworkRoutes _setNetworkRoutes;
        private NetworkInterface _networkInterface1;
        private NetworkInterface _networkInterface2;
        private Network _network;
        private IExecutableProcessQueue _executableProcessQueue;
        private IRegistryReader _registryReader;
        private ILogger _logger;

        [SetUp]
        public void Setup()
        {
            _network = new Network();
 

            Setup("fakemac");
            SetupRoutesOnInterface(new[]
                                          {
                                              new NetworkRoute
                                                  {
                                                      gateway = "10.1.10.20",
                                                      netmask = "255.255.255.0",
                                                      route = "10.1.10.1"
                                                  },
                                                  new NetworkRoute
                                                  {
                                                      gateway = "10.1.10.20",
                                                      netmask = "255.255.255.0",
                                                      route = "10.1.10.2"
                                                  }

                                          });
            _networkInterface1 = NetworkInterface;
            _networkInterface1.label = "public";
            _network.Interfaces.Add("fakemac", _networkInterface1);

            Setup("fakemac1");
            SetupRoutesOnInterface(new[]
                                          {
                                              new NetworkRoute
                                                  {
                                                      gateway = "10.1.10.20",
                                                      netmask = "255.255.255.0",
                                                      route = "10.1.10.1"
                                                  },
                                                  new NetworkRoute
                                                  {
                                                      gateway = "10.1.10.20",
                                                      netmask = "255.255.255.0",
                                                      route = "10.1.10.3"
                                                  }

                                          });
            _networkInterface2 = NetworkInterface;
            _networkInterface2.gateway = "10.1.1.1";
            _network.Interfaces.Add("fakemac1", _networkInterface2);

            _executableProcessQueue = MockRepository.GenerateMock<IExecutableProcessQueue>();
            _executableProcessQueue.Expect(x => x.Go()).Repeat.Once();

            _registryReader = MockRepository.GenerateMock<IRegistryReader>();
            _registryReader.Stub(x => x.GetValuesFrom(Arg<string>.Is.Anything))
                .Return(new List<string> {
                                             "0.0.0.0,0.0.0.0,172.16.251.2,2",
                                             "1.2.3.4,5.6.7.8,9.10.11.12.13,10"
                                         });
            
            _logger = MockRepository.GenerateMock<ILogger>();

            ExecutableProcessQueue.Replay();
            _setNetworkRoutes = new SetNetworkRoutes(_executableProcessQueue, _registryReader, _logger);
            _setNetworkRoutes.Execute(_network);
        }

        [Test]
        public void should_delete_all_persisted_routes() {
            _executableProcessQueue.AssertWasCalled(x => x.Enqueue("route", "delete 0.0.0.0"));
            _executableProcessQueue.AssertWasCalled(x => x.Enqueue("route", "delete 1.2.3.4"));
        }

        [Test]
        public void should_add_the_routes_for_both_interfaces()
        {
            _executableProcessQueue.AssertWasCalled(
                x => x.Enqueue("route", "-p add 0.0.0.0 mask 0.0.0.0 192.168.1.1 metric 2"));
            _executableProcessQueue.AssertWasCalled(
                x => x.Enqueue("route", "-p add 10.1.10.1 mask 255.255.255.0 10.1.10.20 metric 10"));
            _executableProcessQueue.AssertWasCalled(
                x => x.Enqueue("route", "-p add 10.1.10.2 mask 255.255.255.0 10.1.10.20 metric 10"));
            _executableProcessQueue.AssertWasCalled(
                x => x.Enqueue("route", "-p add 10.1.10.3 mask 255.255.255.0 10.1.10.20 metric 10"));
        }

        [TearDown]
        public void Teardown() {
            _executableProcessQueue.VerifyAllExpectations();
        }
    }
}