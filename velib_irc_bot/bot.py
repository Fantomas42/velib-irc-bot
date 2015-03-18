"""
Bot for Velib on IRC
"""
import re

from irc.strings import lower
from irc.bot import SingleServerIRCBot

from veliberator import __version__
from veliberator.models import db_connection
from veliberator.settings import DATABASE_URI
from veliberator.settings import STATION_AROUND_RADIUS
from veliberator.cartography import Cartography
from veliberator.geofinder import AddressGeoFinder
from veliberator.station import Station
from veliberator.station import UnknowStation

STATUS_RE = re.compile('^status (\d+)$')
ADDRESS_RE = re.compile('^address ([\,\w\s-]+)$')


class VelibIRCBot(SingleServerIRCBot):

    def __init__(self, nickname='veliberator', channel='#velib'):
        self.min_places = 3
        self.max_display = 3
        self.channel = channel
        self.nickname = nickname

        db_connection(DATABASE_URI)
        SingleServerIRCBot.__init__(
            self, [("irc.freenode.net", 6667)],
            self.nickname,
            "Assistant pour les stations velib")

    def on_nicknameinuse(self, server, event):
        server.nick(server.get_nickname() + '_')

    def on_welcome(self, server, event):
        server.join(self.channel)

    def on_privmsg(self, server, event):
        nick = event.source.nick
        self.do_command(event, event.arguments[0], nick)

    def on_pubmsg(self, server, event):
        a = event.arguments[0].split(', ', 1)
        if len(a) > 1 and (lower(a[0]) ==
                           lower(self.connection.get_nickname())):
            self.do_command(event, a[1].strip(), self.channel)
        return

    def do_command(self, event, cmd, nick):
        c = self.connection

        if cmd == 'disconnect':
            self.disconnect('I will be bike !')
        elif cmd == 'die':
            self.die('Road rage !')
        elif cmd == 'help':
            c.privmsg(nick, 'Commandes disponibles: '
                      'synchronize|status ID|address LOCATION|version')
        elif cmd == 'version':
            c.privmsg(nick, 'Je tourne sous la version %s' % __version__)
        elif cmd == 'synchronize':
            self.synchronize(c, nick)
        elif STATUS_RE.match(cmd):
            station_id = STATUS_RE.match(cmd).group(1)
            self.status(c, nick, station_id)
        elif ADDRESS_RE.match(cmd):
            address = ADDRESS_RE.match(cmd).group(1)
            self.address(c, nick, address)
        else:
            c.privmsg(nick, "Gne ? %s ?" % cmd)

    def synchronize(self, c, nick):
        c.privmsg(nick, 'Synchronisation des stations...')
        Cartography.synchronize()
        c.privmsg(nick, 'Synchronisation complete !')

    def status(self, c, nick, station_id):
        try:
            station = Station(station_id)
        except UnknowStation:
            c.privmsg(nick, station_id + ' station inconnue !')
            return
        self.show_station(c, nick, station)
        if not station.is_free(self.min_places):
            c.privmsg(nick, 'Trop peu de places, recherche aux alentours...')
            displayed = 0
            for station_information_around in station.stations_around:
                station_around = Station(station_information_around.id)
                if displayed == self.max_display:
                    break
                if station_around.is_free(self.min_places):
                    self.show_station(c, nick, station_around,
                                      station_information_around)
                    displayed += 1

    def address(self, c, nick, address):
        finder = AddressGeoFinder(address)
        stations = finder.get_stations_around(STATION_AROUND_RADIUS)

        displayed = 0
        for station_information_around in stations:
            station_around = Station(station_information_around.id)
            if displayed == self.max_display:
                break
            if station_around.is_free(self.min_places):
                self.show_station(c, nick, station_around,
                                  station_information_around)
                displayed += 1

    def show_station(self, c, nick, station, infos=None):
        if not infos:
            c.privmsg(nick, 'Station %s: %s/%s velos, %s places libres.' %
                      (station.id,
                       station.status.available,
                       station.status.total,
                       station.status.free))
        else:
            c.privmsg(nick,
                      'Station %s: %s/%s velos, %s places libres. %.2fm. %s' %
                      (station.id,
                       station.status.available,
                       station.status.total,
                       station.status.free,
                       infos.distance,
                       infos.full_address))


def cmdline():
    bot = VelibIRCBot()
    bot.start()
