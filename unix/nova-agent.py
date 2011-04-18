# Needed to register the exchange/parser plugin combiniation with the
# main daemon
import agentlib

# To get jsonparser and xscomm
import plugins

# Loads 'commands' plus all modules that contain command classes
import commands.command_list

# Not required, as the default is False
test_mode = False

# Inits all command classes
c = commands.init()

# Creates instance of JsonParser, passing in available commands
parser = plugins.JsonParser(c)
# Create the XSComm intance
xs = plugins.XSComm()

# Register an exchange/parser combination with the main daemon
agentlib.register(xs, parser)
