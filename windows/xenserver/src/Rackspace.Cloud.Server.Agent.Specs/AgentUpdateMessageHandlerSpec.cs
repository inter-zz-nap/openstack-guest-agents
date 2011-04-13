using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Actions;

namespace Rackspace.Cloud.Server.Agent.Specs
{
    [TestFixture]
    public class AgentUpdateMessageHandlerSpec
    {
        [Test]
        public void should_validate_agent_update_message_format()
        {
            var messageHandler = new AgentUpdateMessageHandler();
            var result =
                messageHandler.Handle(
                    "http://c0042202.cdn.cloudfiles.rackspacecloud.com/AgentService.zip,3c36b5aa0b225f415e296b074a815964");
            Assert.That(result.url, Is.EqualTo("http://c0042202.cdn.cloudfiles.rackspacecloud.com/AgentService.zip"));
            Assert.That(result.signature, Is.EqualTo("3c36b5aa0b225f415e296b074a815964"));
        }

        [Test]
        [ExpectedException(typeof(InvalidCommandException))]
        public void should_invalidate_agent_update_message_with_space_after_comma()
        {
            var messageHandler = new AgentUpdateMessageHandler();
            messageHandler.Handle(
                    "http://c0042202.cdn.cloudfiles.rackspacecloud.com/AgentService.zip, 3c36b5aa0b225f415e296b074a815964");
        }
    }
}