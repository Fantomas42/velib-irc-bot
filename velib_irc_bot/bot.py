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
ADDRESS_RE = re.compile('^address ([\w\s-]+)$')


class VelibIRCBot(SingleServerIRCBot):

    def __init__(self):
        db_connection(DATABASE_URI)
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

        if cmd == 'disco':
            self.disconnect('I will be bike !')
        elif cmd == 'die':
            self.die('Road rage !')
        elif cmd == 'version':
            c.notice(nick, 'Veliberator v' + __version__)
        elif cmd == 'synchronize':
            self.synchronize(c, nick)
        elif STATUS_RE.match(cmd):
            station_id = STATUS_RE.match(cmd).group(1)
            self.status(c, nick, station_id)
        elif ADDRESS_RE.match(cmd):
            address = ADDRESS_RE.match(cmd).group(1)
            self.address(c, nick, address)
        else:
            c.privmsg(nick, "Gneh: " + cmd)

    def synchronize(self, c, nick):
        c.notice(nick, 'Synchronizing...')
        Cartography.synchronize()
        c.notice(nick, 'Synchronization completed !')

    def status(self, c, nick, station_id):
        min_places = 2
        max_display = 3

        try:
            station = Station(station_id)
        except UnknowStation:
            c.privmsg(nick, station_id + ' station inconnue !')
            return
        self.show_station(c, nick, station)
        if not station.is_free(min_places):
            c.privmsg(nick, 'Trop peu de places, recherche aux alentours...')
            displayed = 0
            for station_information_around in station.stations_around:
                station_around = Station(station_information_around.id)
                if displayed == max_display:
                    break
                if station_around.is_free(min_places):
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

    def address(self, c, nick, address):
        min_places = 2
        max_display = 3
        finder = AddressGeoFinder(address)
        stations = finder.get_stations_around(STATION_AROUND_RADIUS)

        displayed = 0
        for station_information_around in stations:
            station_around = Station(station_information_around.id)
            if displayed == max_display:
                break
            if station_around.is_free(min_places):
                self.show_station(c, nick, station_around,
                                  station_information_around)
                displayed += 1


def cmdline():
    bot = VelibIRCBot()
    bot.start()
