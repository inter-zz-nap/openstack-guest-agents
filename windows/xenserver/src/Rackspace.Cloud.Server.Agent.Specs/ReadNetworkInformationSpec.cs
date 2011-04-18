using System;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Configuration;
using Rackspace.Cloud.Server.Agent.Interfaces;
using Rhino.Mocks;

namespace Rackspace.Cloud.Server.Agent.Specs {
    public class ReadNetworkInformationBase {
        protected XenNetworkInformation _reader;
        protected IXenStore _store;
        protected String _baseconfig = "vm-data/networking";
        protected Network _network;

        internal void Setup(string[] interfaces) {
            _store.Stub(st => st.Read(_baseconfig)).Return(interfaces);
        }
    }

    [TestFixture]
    public class ReadNetworkInterformationWithTwoInterfacesSpec : ReadNetworkInformationBase {
        private string mac1;
        private string mac2;

        private void SetupTwoInterfacesInVmDataNetworking() {
            string stubinterface1 = "fakemac";
            string stubinterface2 = "fakemac2";

            Setup(new[] { stubinterface1, stubinterface2 });

            mac1 = "40:40:92:9e:44:48".ToUpper();
            mac2 = "40:40:de:f2:37:4a".ToUpper();

            const string returnFullInterface = "{\"mac\":\"40:40:92:9e:44:48\",\"dns\":[\"72.3.128.240\",\"72.3.128.241\"],\"label\":\"public\",\"ips\":[{\"ip\":\"98.129.220.138\",\"netmask\":\"255.255.255.0\"}],\"gateway\":\"98.129.220.1\",\"slice\":74532}";
            const string returnPartialInterface = "{\"mac\":\"40:40:de:f2:37:4a\",\"ips\":[{\"ip\":\"10.176.1.144\",\"netmask\":\"255.255.255.0\"}],\"label\":\"private\"}";

            _store.Stub(st => st.ReadVmDataKey(stubinterface1))
                .Return(returnFullInterface);
            _store.Stub(st => st.ReadVmDataKey(stubinterface2)).Return(returnPartialInterface);
        }

        [SetUp]
        public void Setup() {
            _store = MockRepository.GenerateMock<IXenStore>();
            _reader = new XenNetworkInformation(_store);
            SetupTwoInterfacesInVmDataNetworking();
            _network = _reader.Get();
        }

        [Test]
        public void should_only_have_two_interfaces() {
            Assert.AreEqual(2, _network.Interfaces.Count);
        }

        [Test]
        public void should_get_fakemac_information() {
            Assert.AreEqual("public", _network.Interfaces[mac1].label);
            Assert.AreEqual("98.129.220.138", _network.Interfaces[mac1].ips[0].ip);
            Assert.AreEqual("255.255.255.0", _network.Interfaces[mac1].ips[0].netmask);
            Assert.AreEqual("98.129.220.1", _network.Interfaces[mac1].gateway);
            Assert.AreEqual("72.3.128.240", _network.Interfaces[mac1].dns[0]);
            Assert.AreEqual("72.3.128.241", _network.Interfaces[mac1].dns[1]);
        }

        [Test]
        public void should_get_fakemac2_information() {
            Assert.AreEqual("private", _network.Interfaces[mac2].label);
            Assert.AreEqual("10.176.1.144", _network.Interfaces[mac2].ips[0].ip);
            Assert.AreEqual("255.255.255.0", _network.Interfaces[mac2].ips[0].netmask);
            Assert.IsNull(_network.Interfaces[mac2].gateway);
            Assert.IsNull(_network.Interfaces[mac2].dns);
        }
    }
}
