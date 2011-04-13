using System;
using NUnit.Framework;
using NUnit.Framework.SyntaxHelpers;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Utilities;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class JsonSpec {
        private Json<Command> _jsonCommand;
        private Json<NetworkInterface> _jsonInterface;
        private string _partialJsonStringForImport;
        private string _jsonStringFromCustomException;
        private string _fullJsonStringWithObjectCompletelyPopulated;
        private string _fullJsonStringWithObjectPartiallyPopulated;
        private string _fullInterfaceJsonString;
        private string _updateJson;

        [SetUp]
        public void Setup()
        {
            _updateJson = "{\"name\":\"agentupdate\",\"value\":\"http://c0473242.cdn.cloudfiles.rackspacecloud.com/AgentService.zip,e6b39323fc3cf982b270fc114b9bb9e5\"}";

            _jsonCommand = new Json<Command>();
            _jsonInterface = new Json<NetworkInterface>();
            _partialJsonStringForImport = "{\"name\":\"password\",\"value\":\"somepassword\"}";
            _fullJsonStringWithObjectCompletelyPopulated = "{\"name\":\"password\",\"value\":\"somepassword\",\"key\":\"67745jhgj7683\"}";
            _fullJsonStringWithObjectPartiallyPopulated = "{\"key\":null,\"name\":\"password\",\"value\":\"somepassword\"}";
            
            _fullInterfaceJsonString = "{\"mac\":\"40:40:ed:65:h6\",\"dns\":[\"1.1.1.1\",\"64.39.2.138\"],\"label\":\"Label 1\",\"ips\":[{\"Ip\":\"3.3.3.3\",\"NetMask\":\"255.255.255.0\"},{\"Ip\":\"4.4.4.4\",\"NetMask\":\"255.255.255.0\"}],\"gateway\":\"10.1.1.100\"}";
        }

        [Test]
        public void should_return_empty_string_if_given_empty_string()
        {
            Assert.That(_jsonCommand.Deserialize(""), Is.Null);
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException), ExpectedMessage = "Problem deserializing the following json: '{'")]
        public void should_throw_exception_with_curly_brace()
        {
            _jsonCommand.Deserialize("{");
        }

        [Test]
        [ExpectedException(typeof(UnsuccessfulCommandExecutionException), ExpectedMessage = "Problem deserializing the following json: '{\"name\":\"password\", \"value\":\"abcdefghijklmnopqrstuvwxyzabcdefghijklmnoqrstuvwxyz'")]
        public void should_throw_exception_with_json_input_is_broken()
        {
            _jsonCommand.Deserialize("{\"name\":\"password\", \"value\":\"abcdefghijklmnopqrstuvwxyzabcdefghijklmnoqrstuvwxyz");
        }

        [Test]
        public void should_return_an_instance_of_a_command_object_from_partial_json_string() {
            var command = _jsonCommand.Deserialize(_partialJsonStringForImport);

            Assert.AreEqual("password", command.name);
            Assert.AreEqual("somepassword", command.value);
            Assert.IsNull(command.key);
        }

        [Test]
        public void should_return_an_instance_of_a_command_object_from_full_json_string() {
            var command = _jsonCommand.Deserialize(_fullJsonStringWithObjectCompletelyPopulated);

            Assert.AreEqual("password", command.name);
            Assert.AreEqual("somepassword", command.value);
            Assert.AreEqual("67745jhgj7683", command.key);
        }

        [Test]
        public void should_return_an_instance_of_an_interface_object()
        {
            var interface1 = _jsonInterface.Deserialize(_fullInterfaceJsonString);
            Assert.AreEqual("64.39.2.138", interface1.dns[1]);
        }

        [Test]
        public void should_serialize_partially_filled_object_to_json()
        {
            var command = new Command {name = "password", value = "somepassword"};

            Assert.AreEqual(_fullJsonStringWithObjectPartiallyPopulated, _jsonCommand.Serialize(command));
        }

        [Test]
        public void should_serialize_custom_exception_to_json() {
            var command = new { returncode = "1", message = "Key init was not called prior to Set Password command" };

            var _jsonObject = new Json<object>();
            _jsonStringFromCustomException = "{\"returncode\":\"1\",\"message\":\"Key init was not called prior to Set Password command\"}";
            Assert.AreEqual(_jsonStringFromCustomException, _jsonObject.Serialize(command));
        }

        [Test]
        public void print_serialized_json_string_and_deserialize()
        {
            const string stringWrong = "{\"mac\":\"40:40:92:9e:44:48\",\"dns\":[\"72.3.128.240\",\"72.3.128.241\"],\"label\":\"public\",\"ips\":[{\"ip\":\"98.129.220.138\",\"netmask\":\"255.255.255.0\"}],\"gateway\":\"98.129.220.1\",\"slice\":74532}";
            const string stringCorrt = "{\"mac\":\"40:40:92:9e:44:48\",\"dns\":[\"72.3.128.240\",\"72.3.128.241\"],\"label\":\"public\",\"ips\":[{\"ip\":\"98.129.220.138\",\"netmask\":\"255.255.255.0\"}],\"gateway\":\"98.129.220.1\"}";
            const string stringSomething =
                "{\"label\": \"private\", \"ips\": [{\"netmask\": \"255.255.224.0\", \"ip\": \"10.176.64.48\"}], \"mac\": \"40:40:d0:ed:cb:96\"}";
            
            var interface1 = new NetworkInterface
                                 {
                                     gateway = "98.129.220.1",
                                     label = "public",
                                     mac = "40:40:92:9e:44:48",
                                     dns = new[] { "72.3.128.240", "72.3.128.241" },
                                     ips =
                                         new[]
                                             {
                                                 new IpTuple {ip = "98.129.220.138", netmask = "255.255.255.0", enabled = "1"},
                                             }
                                 };

            var serialized = _jsonInterface.Serialize(interface1);
            Assert.That(serialized, Is.EqualTo("{\"mac\":\"40:40:92:9e:44:48\",\"dns\":[\"72.3.128.240\",\"72.3.128.241\"],\"label\":\"public\",\"ips\":[{\"ip\":\"98.129.220.138\",\"netmask\":\"255.255.255.0\",\"enabled\":\"1\"}],\"gateway\":\"98.129.220.1\",\"routes\":null}"));
            
            _jsonInterface.Deserialize(stringCorrt);
            _jsonInterface.Deserialize(stringWrong);
            _jsonInterface.Deserialize(stringSomething);
            _jsonCommand.Deserialize(_updateJson);
        }

        [Test]
        public void should_deserilize_agent_update()
        {
            var command = _jsonCommand.Deserialize("{\"name\":\"version\",\"value\":\"agent\"}");
            Assert.That(command.name, Is.EqualTo("version"));
            Assert.That(command.value, Is.EqualTo("agent"));
        }
    }
}
