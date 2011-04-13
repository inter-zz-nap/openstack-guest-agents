using NUnit.Framework;

namespace Rackspace.Cloud.Server.DiffieHellman.Specs
{
    [TestFixture]
    public class DiffieHellmanSpec
    {
        private DiffieHellmanManaged _diffieHellmanManaged;

        [Test]
        public void should_create_a_key_exchange_when_all_parameters_are_provided()
        {
            _diffieHellmanManaged = new DiffieHellmanManaged("23", "5", "6");
            var exchange = _diffieHellmanManaged.CreateKeyExchange();
            Assert.AreEqual("8", exchange);

            _diffieHellmanManaged = new DiffieHellmanManaged("23", "5", "15");
            exchange = _diffieHellmanManaged.CreateKeyExchange();
            Assert.AreEqual("19", exchange);
        }

        [Test]
        public void should_create_a_key_exchange_when_providing_just_the_public_parameters()
        {
            var p = "23";
            _diffieHellmanManaged = new DiffieHellmanManaged(p, "5");
            var exchange = _diffieHellmanManaged.CreateKeyExchange();
            
            Assert.IsTrue(exchange.Length <= p.Length);
        }

        [Test]
        public void should_create_a_final_key_with_the_collaborators_key() {
            _diffieHellmanManaged = new DiffieHellmanManaged("23", "5", "15");
            _diffieHellmanManaged.CreateKeyExchange();

            Assert.AreEqual("2", _diffieHellmanManaged.DecryptKeyExchange("8"));

            _diffieHellmanManaged = new DiffieHellmanManaged("23", "5", "6");
            _diffieHellmanManaged.CreateKeyExchange();

            Assert.AreEqual("2", _diffieHellmanManaged.DecryptKeyExchange("19"));
        }

        [Test]
        public void should_be_able_to_create_an_end_to_end_handshake() {
            var diffieHellmanManaged1 = new DiffieHellmanManaged("23", "5");
            string exchange1 = diffieHellmanManaged1.CreateKeyExchange();

            var diffieHellmanManaged2 = new DiffieHellmanManaged("23", "5");
            string exchange2 = diffieHellmanManaged2.CreateKeyExchange();

            Assert.IsTrue(diffieHellmanManaged1.DecryptKeyExchange(exchange2) == diffieHellmanManaged2.DecryptKeyExchange(exchange1));
        }
    }
}
