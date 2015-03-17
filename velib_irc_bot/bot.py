"""
Bot for Velib on IRC
"""
from irc.bot import SingleServerIRCBot


class VelibIRCBot(SingleServerIRCBot):

    def __init__(self):
        SingleServerIRCBot.__init__(
            self, [("irc.freenode.net", 6667)],
            "veliberator",
            "Assistant pour les stations velib")

    def on_welcome(self, serv, ev):
        serv.join("#velib")


def cmdline():
    bot = VelibIRCBot()
    bot.start()
