## IRC bot for fetching information from URL
from twisted.internet import reactor, protocol, defer
from twisted.words.protocols import irc

class Bot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    def _get_username(self):
        return self.factory.username
    def _get_realname(self):
        return self.factory.realname
    def _get_versionname(self):
        return self.factory.versionName

    nickname = property(_get_nickname)
    username = property(_get_username)
    realname = property(_get_realname)
    versionName = property(_get_versionname)


    def signedOn(self):
        print("Signed on as %s." % self.nickname)
        print("Logged in.")
        print("Joining channels...")
        reactor.callLater(2, self.join, self.factory.channel)


class BotFactory(protocol.ClientFactory):
    global bot_nickname, bot_channel, server_ipaddress

    protocol = Bot

    def __init__(self, channel, nickname='EnterNickHere'):
        self.channel = "#bot-test"
        self.nickname = "EnterNickHere"
        self.realname = 'Bot Nick'
        self.username = 'botnick'
        self.versionName = "Twisted IRC"
        
if __name__ == "__main__":

    reactor.connectTCP("enter server address here", 6667, BotFactory("#bot-test"))

reactor.run()