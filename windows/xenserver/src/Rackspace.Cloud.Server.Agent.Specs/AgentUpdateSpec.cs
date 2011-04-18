using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.AgentUpdate;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class AgentUpdateSpec {
        private IAgentUpdateMessageSender _agentUpdateMessageSender;
        private AgentUpdate _agentUpdate;
        private string _agentUpdateInfo;
        private IConnectionChecker _connectionChecker;
        private ILogger _logger;

        [SetUp]
        public void Setup()
        {
            _agentUpdateInfo = "http://something.com/file.zip,544564abc453de787ad";

            _agentUpdateMessageSender = MockRepository.GenerateMock<IAgentUpdateMessageSender>();
            _connectionChecker = MockRepository.GenerateMock<IConnectionChecker>();
            _logger = MockRepository.GenerateMock<ILogger>();

            _connectionChecker.Stub(x => x.Check());

            _agentUpdate = new AgentUpdate(_agentUpdateMessageSender, _connectionChecker, new AgentUpdateMessageHandler(), _logger);

            _agentUpdate.Execute(_agentUpdateInfo);
        }

        [Test]
        public void should_send_a_message_to_the_updater_using_remoting()
        {
            _agentUpdateMessageSender.AssertWasCalled(x=>x.Send(Arg<AgentUpdateInfo>.Is.Anything));
        }

        [Test]
        public void should_throw_UnsuccessfulCommandExecutionException_if_connection_to_updater_service_fails() {
            _agentUpdateMessageSender.Stub(x => x.Send(Arg<AgentUpdateInfo>.Is.Anything))
                .Throw(new UnsuccessfulCommandExecutionException("error message", new ExecutableResult {ExitCode = "1"}));
            var result = _agentUpdate.Execute(_agentUpdateInfo);
            Assert.That(result.ExitCode, Is.EqualTo("1"));
            Assert.That(result.Error[0], Is.EqualTo("Update failed"));
        }
    }
}
