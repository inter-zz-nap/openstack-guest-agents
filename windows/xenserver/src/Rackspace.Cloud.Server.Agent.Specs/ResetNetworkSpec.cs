using System.Collections.Generic;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class ResetNetworkSpec {
        private ResetNetwork command;
        private IXenNetworkInformation xenNetworkInformation;
        private ISetNetworkInterface setNetworkInterface;
        private Network network;
        private ExecutableResult result;
        private NetworkInterface networkInterface;
        private ISetNetworkRoutes setNetworkRoutes;

        [SetUp]
        public void Setup() {
            xenNetworkInformation = MockRepository.GenerateMock<IXenNetworkInformation>();
            setNetworkInterface = MockRepository.GenerateMock<ISetNetworkInterface>();
            setNetworkRoutes = MockRepository.GenerateMock<ISetNetworkRoutes>();

            networkInterface = new NetworkInterface();
            network = new Network();
            network.Interfaces.Add("fakemac", networkInterface);

            command = new ResetNetwork(setNetworkInterface, xenNetworkInformation, setNetworkRoutes);
            xenNetworkInformation.Stub(x => x.Get()).Return(network);

            setNetworkInterface.Expect(x => x.Execute(networkInterface)).Repeat.Once();

            result = command.Execute(null);

            setNetworkInterface.Replay();
        }

        [Test]
        public void should_set_interface_from_interfaceconfigiuration() {
            setNetworkInterface.AssertWasCalled(x => x.Execute(networkInterface));
            setNetworkRoutes.AssertWasCalled(x => x.Execute(network));
        }

        [TearDown]
        public void TearDown() {
            setNetworkInterface.VerifyAllExpectations();
        }
    }
}
