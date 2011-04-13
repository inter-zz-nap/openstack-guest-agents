using System;
using NUnit.Framework;
using Rackspace.Cloud.Server.Agent.Security;

namespace Rackspace.Cloud.Server.Agent.Specs {
    [TestFixture]
    public class EncryptionSpec {

        [Test]
        public void decryotion_test_using_base64() {
            //base64 rendering of the encrypted string 'rackspace'
            var base64 = "OTfAog/nwyzIcYOhvCBL0w==";
            var _encryptedData = Convert.FromBase64String(base64);
            var decryptedData = Encryption.Decrypt(_encryptedData, "secret", new byte[0]);
            Assert.AreEqual("rackspace", decryptedData);
        }

    }
}