
import sys
import agentlib
import plugins
import commands.command_list


test_mode = False

args = {"test": "test123"}
c = commands.init(**args)

parser = plugins.JsonParser(c)
xs = plugins.XSComm()

agentlib.register(xs, parser)
