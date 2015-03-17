"""
Bot for Velib on IRC
"""
from irc.strings import lower
from irc.bot import SingleServerIRCBot

from veliberator import __version__


class VelibIRCBot(SingleServerIRCBot):

    def __init__(self):
        SingleServerIRCBot.__init__(
            self, [("irc.freenode.net", 6667)],
            "veliberator",
            "Assistant pour les stations velib")

    def on_nicknameinuse(self, server, event):
        server.nick(server.get_nickname() + '_')

    def on_welcome(self, server, event):
        server.join("#velib")

    def on_privmsg(self, server, event):
        self.do_command(event, event.arguments[0])

    def on_pubmsg(self, server, event):
        a = event.arguments[0].split(', ', 1)
        if len(a) > 1 and (lower(a[0]) ==
                           lower(self.connection.get_nickname())):
            self.do_command(event, a[1].strip())
        return

    def do_command(self, event, cmd):
        nick = event.source.nick
        c = self.connection

        if cmd == 'disconnect':
            self.disconnect('I will be bike !')
        elif cmd == 'die':
            self.die('Road rage !')
        elif cmd == 'version':
            c.notice(nick, 'Veliberator v' + __version__)
        else:
            c.notice(nick, "Not understood: " + cmd)


def cmdline():
    bot = VelibIRCBot()
    bot.start()
