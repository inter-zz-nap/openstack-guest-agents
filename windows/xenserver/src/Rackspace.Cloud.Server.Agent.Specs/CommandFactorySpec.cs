using System;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Commands;
using Rackspace.Cloud.Server.Agent.Security;

namespace Rackspace.Cloud.Server.Agent.Specs {
    public class CommandReadBaseContext {
        protected CommandFactory Factory;

        protected void EstablishContext() {
            Utility.ConfigureStructureMap();
            Factory = new CommandFactory();
        }
    }

    [TestFixture]
    public class CommandInterpreter_When_Reading_Receiving_Valid_Command : CommandReadBaseContext {
        [SetUp]
        public void Setup() {
            EstablishContext();
        }

        [Test]
        public void should_pass_this_test() {
            var executableCommand = Factory.CreateCommand("resetnetwork");
            Assert.AreEqual(typeof (ResetNetwork), executableCommand.GetType());
        }
    }

    [TestFixture]
    public class CommandRead_When_Reading_Command_Store_Which_Has_No_Matching_Commands : CommandReadBaseContext {
        [SetUp]
        public void Setup() {
            EstablishContext();
        }

        [Test]
        public void should_return_throw_invalid_command_found() {
            try {
                Factory.CreateCommand("n");
                Assert.Fail();
            }
            catch (InvalidCommandException) {
            }
        }
    }
}