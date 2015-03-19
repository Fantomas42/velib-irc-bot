"""
Bot for Velib on IRC
"""
import re
from random import choice

from irc.strings import lower
from irc.bot import SingleServerIRCBot
from irc.buffer import DecodingLineBuffer

from veliberator import __version__
from veliberator.models import db_connection
from veliberator.settings import DATABASE_URI
from veliberator.settings import STATION_AROUND_RADIUS
from veliberator.cartography import Cartography
from veliberator.geofinder import GeoFinderError
from veliberator.geofinder import AddressGeoFinder
from veliberator.station import Station
from veliberator.station import UnknowStation

STATUS_RE = re.compile('^status (\d+)$')
ADDRESS_RE = re.compile('^address ([\,\w\s-]+)$')


class CompliantDecodingLineBuffer(DecodingLineBuffer):

    def lines(self):
        lines = [l for l in super(DecodingLineBuffer, self).lines()]
        try:
            # Note: skipping parent in super to go up one class in the branch
            # (to avoid trying to decode with 'replace')
            return iter([line.decode('utf-8') for line in lines])
        except UnicodeDecodeError:
            return iter([line.decode('latin-1') for line in lines])
        # fallback
        return iter([line.decode('utf-8', 'replace') for line in lines])


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
        self.connection.buffer = CompliantDecodingLineBuffer()
        server.join(self.channel)
        server.privmsg(self.channel, "Welcome bike !")
        self.pubmsgre = re.compile('^%s[:\,]?[\s]+([\w\W]+)$' %
                                   self.connection.get_nickname())

    def on_privmsg(self, server, event):
        nick = event.source.nick
        self.do_command(event, event.arguments[0], nick)

    def on_pubmsg(self, server, event):
        command = self.pubmsgre.match(event.arguments[0])
        if command:
            self.do_command(event, command.group(1), self.channel,
                            event.source.nick)
        return

    def do_command(self, event, cmd, nick, user=''):
        c = self.connection
        if user:
            user = '%s ' % user

        if cmd == 'die':
            if 'fantomas' in user:
                c.privmsg(nick, 'I will be bike !')
                self.die('I will be bike !')
            c.privmsg(nick, "%sdie toi meme, bourreau d'enfant !" % user)
        elif cmd == 'help':
            c.privmsg(nick, '%sCommandes disponibles: '
                      'synchronize|status ID|address LOCATION|version' % user)
        elif cmd == 'version':
            c.privmsg(nick, '%sJe tourne sous la version %s' % (
                user, __version__))
        elif cmd == 'synchronize':
            self.synchronize(c, nick, user)
        elif STATUS_RE.match(cmd):
            station_id = STATUS_RE.match(cmd).group(1)
            self.status(c, nick, station_id, user)
        elif ADDRESS_RE.match(cmd):
            address = ADDRESS_RE.match(cmd).group(1)
            self.address(c, nick, address, user)
        elif cmd[-1] == '?':
            self.fortune(c, nick, user)
        else:
            c.privmsg(nick, "%sNi ! %s ?" % (user, cmd))

    def synchronize(self, c, nick, user):
        c.privmsg(nick, '%sSynchronisation des stations...' % user)
        Cartography.synchronize()
        c.privmsg(nick, '%sSynchronisation complete !' % user)

    def status(self, c, nick, station_id, user):
        try:
            station = Station(station_id)
        except UnknowStation:
            c.privmsg(nick, "%sLa station %s n'existe que dans tes reves !" % (
                user, station_id))
            return
        if user:
            c.privmsg(nick, '%s:' % user.strip())
        self.show_station(c, nick, station)
        if not station.is_free(self.min_places):
            c.privmsg(nick, 'Trop peu de places pour se garer, '
                      'je recherche aux alentours...')
            displayed = 0
            for station_information_around in station.stations_around:
                station_around = Station(station_information_around.id)
                if displayed == self.max_display:
                    break
                if station_around.is_free(self.min_places):
                    self.show_station(c, nick, station_around,
                                      station_information_around)
                    displayed += 1

    def address(self, c, nick, address, user):
        try:
            finder = AddressGeoFinder(address)
        except GeoFinderError:
            c.privmsg(nick, '%sEt pourquoi pas ouvrir '
                      'un garage a velo dans ton cul ?' % user)
            return

        stations = finder.get_stations_around(STATION_AROUND_RADIUS)
        if not stations:
            c.privmsg(nick, "%s%s... C'est la brousse la-bas... "
                      "Je ne travaille pas dans ces conditions !" % (
                          user, address))
            return

        displayed = 0
        if user:
            c.privmsg(nick, '%s:' % user.strip())
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
            c.privmsg(
                nick,
                'Station %s: %s/%s velos, %s places libres. %.2fm. %s' %
                (station.id,
                 station.status.available,
                 station.status.total,
                 station.status.free,
                 infos.distance,
                 infos.full_address))

    def fortune(self, c, nick, user):
        fortune = choice(['Oui', 'Non', 'Certain', 'Absolument',
                          'Jamais', 'Tu reves', 'Peut-etre', '42'])
        fortune += choice(['', '', '', ' ?', ' !'])
        c.privmsg(nick, '%s%s' % (user, fortune))


def cmdline():
    bot = VelibIRCBot()
    bot.start()
