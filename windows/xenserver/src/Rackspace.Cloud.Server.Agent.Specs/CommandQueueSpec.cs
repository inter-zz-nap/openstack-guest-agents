using System.Collections.Generic;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rackspace.Cloud.Server.Common.Logging;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    public class BaseCommandQueueContext {
        protected IXenStore xenStore;
        protected ICommandFactory commandFactory;
        protected CommandQueue commandQueue;
        protected IExecutableCommand executableCommand;
        protected ILogger logger;

        protected void CreateContext() {
            xenStore = MockRepository.GenerateMock<IXenStore>();
            commandFactory = MockRepository.GenerateMock<ICommandFactory>();
            executableCommand = MockRepository.GenerateMock<IExecutableCommand>();
            logger = MockRepository.GenerateMock<ILogger>();
            commandQueue = new CommandQueue(xenStore, commandFactory, logger);
        }
        protected void XenSetup(params Command[] xendata) {
            xenStore.Stub(x => x.GetCommands()).Return(xendata);
        }
    }

    [TestFixture]
    public class CommandQueueSpec_When_XenStore_Has_More_Than_One_Command : BaseCommandQueueContext {
        private Command firstcommand;
        private Command secondcommand;

        [SetUp]
        public void Setup() {
            CreateContext();
            firstcommand = new Command { key = "key1", name = "Command1", value = "12345" };
            secondcommand = new Command { key = "key2", name = "Command2", value = "23456" };
            XenSetup(firstcommand, secondcommand);
            executableCommand.Stub(x => x.Execute(Arg<string>.Is.Anything)).Return(new ExecutableResult { ExitCode = "0", Error = new List<string> { "Error1" } });
            commandFactory.Stub(x => x.CreateCommand(Arg<string>.Is.Anything)).Return(executableCommand);
            commandQueue.Work();
        }
        [Test]
        public void should_pass_each_command_to_the_command_interpreter() {
            commandFactory.AssertWasCalled(x => x.CreateCommand(firstcommand.name));
            commandFactory.AssertWasCalled(x => x.CreateCommand(secondcommand.name));
        }
    }
    [TestFixture]
    public class CommandQueueSpec_When_XenStore_Has_No_Commands : BaseCommandQueueContext {
        [SetUp]
        public void Setup() {
            CreateContext();
            xenStore.Stub(x => x.GetCommands()).Return(new List<Command>());
            commandQueue.Work();
        }
        [Test]
        public void should_only_retrieve_first_command_and_hand_that_to_command_interpreter() {
            commandFactory.AssertWasNotCalled(x => x.CreateCommand(Arg<string>.Is.Anything));
        }
    }
    [TestFixture]
    public class CommandQueueSpec_When_Command_Interpreter_Throws_InvalidCommandException : BaseCommandQueueContext {
        private Command xendata;

        [SetUp]
        public void Setup() {
            CreateContext();
            xenStore.GetMockRepository().Ordered();
            xendata = new Command { key = "key1", name = "BadCommand", value = "Valuewrong" };
            XenSetup(xendata);
            commandFactory.Stub(x => x.CreateCommand(Arg<string>.Is.Anything)).Throw(new InvalidCommandException("BadCommand"));
        }
        [Test]
        public void should_catch_exception() {
            commandQueue.Work();
        }

        [Test]
        public void should_still_remove_command_key() {
            commandQueue.Work();
            xenStore.AssertWasCalled(x => x.Remove("key1"));
        }

        [Test]
        public void should_write_no_command_found_response() {
            commandQueue.Work();
            xenStore.AssertWasCalled(x => x.Write("key1", "{\"returncode\":\"1\",\"message\":\"Unrecognizable Command in Xen Store: BadCommand\"}"));
        }
    }

    [TestFixture]
    public class CommandQueueSpec_When_Command_Interpreter_Has_Valid_Command_To_Process : BaseCommandQueueContext {
        private Command command;

        [SetUp]
        public void Setup() {
            CreateContext();

            command = new Command { key = "key1", name = "12345", value = "Valuewrong" };
            XenSetup(command);
            executableCommand.Stub(x => x.Execute(Arg<string>.Is.Anything)).Return(new ExecutableResult { ExitCode = "0", Error = new List<string>() });
            commandFactory.Stub(x => x.CreateCommand(Arg<string>.Is.Anything)).Return(executableCommand);

            commandQueue.Work();
        }

        [Test]
        public void should_write_response_from_command_processor_to_xen_store() {
            xenStore.AssertWasCalled(x => x.Write("key1", "{\"returncode\":\"0\",\"message\":\"\"}"));
        }

        [Test]
        public void should_remove_xen_store_value_after_processing_command() {
            xenStore.AssertWasCalled(x => x.Remove("key1"));
        }
    }
}