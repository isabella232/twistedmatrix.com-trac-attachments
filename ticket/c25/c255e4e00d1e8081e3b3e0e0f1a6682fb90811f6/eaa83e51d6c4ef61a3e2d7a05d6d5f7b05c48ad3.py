from twisted.words.protocols import irc
from twisted.words import iwords, ewords
from twisted.python import log, failure, reflect
from twisted.internet import protocol, reactor, defer
from twisted.words.service import WordsRealm
from twisted.cred import portal, credentials, error as ecred
from twisted.python import failure
from zope.interface import implements, Interface, Attribute

from time import time, ctime


USESERV = "Ares!@logon.serverCloud" # A ficticious "services" 

WATCH=128 
SILENCE=5 
MODES=12 
MAXCHANNELS=30 
MAXBANS=60 
NICKLEN=30 
TOPICLEN=307 
KICKLEN=307 
CHANTYPES='#'
PREFIX= {   'o' : '@', 
            'a' : '&',
            'h' : '%', 
            'q' : '~', 
            'v' : '+',
        }
PREFIXPRIO = { 'q': 0, 
             'a': 1,
             'o': 2,
             'h': 3,
             'v': 4
            }
CHANMODES='ohvbeqa,kfL,l,psmntirRcOAQKVHGCuzN'
UMODES = 'oOiwghskSaHANcCfrxeWqBFzdvtGj'
PMODES = 'lvhopsmntikrRcaqOALQbSeKVfGCuzNoOiwghskSaHANcCfrxeWqBFzdvtGj'

class User(object):
    implements(iwords.IUser)
    realm = None
    mind = None
    authorised = False
    shunned = True # All users start shunned

    def __init__(self, name):
        self.name = name
        self.groups = []
        self.lastMessage = time()

    def authoriseUser(self):
        self.authorised = True
        self.shunned = False

    def shunUser(self):
        shunned = True

    def loggedIn(self, realm, mind):
        self.realm = realm
        self.mind = mind
        self.signOn = time()

    def join(self, group):
        def cbJoin(result):
            self.groups.append(group)
            return result
        return group.add(self.mind).addCallback(cbJoin)

    def leave(self, group, reason=None):
        def cbLeave(result):
            self.groups.remove(group)
            return result
        return group.remove(self.mind, reason).addCallback(cbLeave)

    def send(self, recipient, message):
        self.lastMessage = time()
        return recipient.receive(self.mind, recipient, message)

    def itergroups(self):
        return iter(self.groups)

    def logout(self):
        for g in self.groups[:]:
            self.leave(g)

class Group(object):
    implements(iwords.IGroup)

    def __init__(self, name):
        self.name = name
        self.users = {}
        self.meta = {
            "topic": "",
            "topic_author": "",
            "modes": ['n', 't'],
            "bans": [],
            "prefixes": {} # Mode flags, like @ and + etc...
            }

    def getModes(self):
        return '+' + ''.join(self.meta['modes'])

    def isBanned(self, nick):
        return nick in self.meta['bans']

    def _ebUserCall(self, err, p):
        return failure.Failure(Exception(p, err))

    def _cbUserCall(self, results):
        for (success, result) in results:
            if not success:
                user, err = result.value # XXX
                self.remove(user, err.getErrorMessage())

    def modeUser(self, nickname, mode):
        if nickname in self.users:
            if self.meta['prefixes'].get(nickname, False):
                # Only bother changing if the prefix is a higher "priority" (inverse for whatever reason i decided) 
                if PREFIXPRIO[self.meta['prefixes'][nickname]] > PREFIXPRIO[mode]: 
                    self.meta['prefixes'][nickname] = mode
            else: # obviously set it anyway if the user has no prefix..
                self.meta['prefixes'][nickname] = mode

    def getUserMode(self, nickname):
        return self.meta['prefixes'].get(nickname, None)

    def getPrefixedNames(self):
        print "GET NAMES"
        names = []
        print self.users.keys()
        for n in self.users.keys():
            if n in self.meta['prefixes'].keys():
                names.append(PREFIX[self.meta['prefixes'][n]]+n)
            else:
                names.append(n)
        print names, self.meta['prefixes']
        return names

    def add(self, user):
        assert iwords.IChatClient.providedBy(user), "%r is not a chat client" % (user,)
        if user.name not in self.users:
            additions = []
            self.users[user.name] = user
            for p in self.users.itervalues():
                if p is not user:
                    d = defer.maybeDeferred(p.userJoined, self, user)
                    d.addErrback(self._ebUserCall, p=p)
                    additions.append(d)
            defer.DeferredList(additions).addCallback(self._cbUserCall)
        return defer.succeed(None)

    def remove(self, user, reason=None):
        assert reason is None or isinstance(reason, unicode)
        try:
            del self.users[user.name]
            del self.meta['prefixes'][user.name]
        except KeyError:
            pass
        else:
            removals = []
            for p in self.users.itervalues():
                if p is not user:
                    d = defer.maybeDeferred(p.userLeft, self, user, reason)
                    d.addErrback(self._ebUserCall, p=p)
                    removals.append(d)
            defer.DeferredList(removals).addCallback(self._cbUserCall)
        return defer.succeed(None)

    def size(self):
        return defer.succeed(len(self.users))

    def receive(self, sender, recipient, message):
        assert recipient is self
        receives = []
        for p in self.users.itervalues():
            if p is not sender:
                d = defer.maybeDeferred(p.receive, sender, self, message)
                d.addErrback(self._ebUserCall, p=p)
                receives.append(d)
        defer.DeferredList(receives).addCallback(self._cbUserCall)
        return defer.succeed(None)

    def setMetadata(self, meta):
        self.meta = meta
        sets = []
        for p in self.users.itervalues():
            d = defer.maybeDeferred(p.groupMetaUpdate, self, meta)
            d.addErrback(self._ebUserCall, p=p)
            sets.append(d)
        defer.DeferredList(sets).addCallback(self._cbUserCall)
        return defer.succeed(None)

    def iterusers(self):
        # XXX Deferred?
        return iter(self.users.values())

class IRCRealm(WordsRealm):
    def __init__(self, *a, **kw):
        super(IRCRealm, self).__init__(*a, **kw)
        self.users = {}
        self.groups = {}

    def itergroups(self):
        return defer.succeed(self.groups.itervalues())

    def requestAvatar(self, avatarId, mind, *interfaces):
        if isinstance(avatarId, str):
            avatarId = avatarId.decode(self._encoding)

        def gotAvatar(avatar):
            if avatar.realm is not None:
                raise ewords.AlreadyLoggedIn()
            for iface in interfaces:
                facet = iface(avatar, None)
                if facet is not None:
                    avatar.loggedIn(self, mind)
                    mind.name = avatarId
                    mind.realm = self
                    mind.avatar = avatar
                    return iface, facet, self.logoutFactory(avatar, facet)
            raise NotImplementedError(self, interfaces)

        return self.getUser(avatarId).addCallback(gotAvatar)

    def userFactory(self, name):
        return User(name)

    def getUser(self, name):
        print "getting ", name
        assert isinstance(name, unicode)
        if self.createUserOnRequest:
            def ebUser(err):
                err.trap(ewords.DuplicateUser)
                return self.lookupUser(name)
            return self.createUser(name).addErrback(ebUser)
        return self.lookupUser(name)
    def addUser(self, user):
        if user.name in self.users:
            return defer.fail(failure.Failure(ewords.DuplicateUser()))
        self.users[user.name] = user
        return defer.succeed(user)

    def addGroup(self, group):
        if group.name in self.groups:
            return defer.fail(failure.Failure(ewords.DuplicateGroup()))
        self.groups[group.name] = group
        return defer.succeed(group)

    def lookupUser(self, name):
        assert isinstance(name, unicode)
        name = name.lower()
        try:
            user = self.users[name]
        except KeyError:
            return defer.fail(failure.Failure(ewords.NoSuchUser(name)))
        else:
            return defer.succeed(user)

    def lookupGroup(self, name):
        assert isinstance(name, unicode)
        name = name.lower()
        try:
            group = self.groups[name]
        except KeyError:
            return defer.fail(failure.Failure(ewords.NoSuchGroup(name)))
        else:
            return defer.succeed(group)


class IRCService(irc.IRC):
    implements(iwords.IChatClient)

    # A list of IGroups in which I am participating
    groups = None

    # A no-argument callable I should invoke when I go away
    logout = None

    # An IUser we use to interact with the chat service
    avatar = None

    # To whence I belong
    realm = None

    # How to handle unicode (TODO: Make this customizable on a per-user basis)
    encoding = 'utf-8'

    # Twisted callbacks
    #def connectionMade(self):
    #    self.irc_PRIVMSG = self.irc_USESERV_PRIVMSG

    def connectionLost(self, reason):
        if self.logout is not None:
            self.logout()
            self.avatar = None

    # Make sendMessage a bit more useful to us
    def sendMessage(self, command, *parameter_list, **kw):
        if not kw.has_key('prefix'):
            kw['prefix'] = self.hostname
        if not kw.has_key('to'):
            kw['to'] = self.name.encode(self.encoding)
        arglist = [self, command, kw['to']] + list(parameter_list)
        irc.IRC.sendMessage(*arglist, **kw)

    def userJoined(self, group, user):
        self.join("%s!%s@%s" % (user.name, user.name, self.hostname),'#' + group.name)

    def userLeft(self, group, user, reason=None):
        assert reason is None or isinstance(reason, unicode)
        self.part("%s!%s@%s" % (user.name, user.name, self.hostname),
            '#' + group.name,
            (reason or u"leaving").encode(self.encoding, 'replace'))

    def receive(self, sender, recipient, message):
        #>> :glyph!glyph@adsl-64-123-27-108.dsl.austtx.swbell.net PRIVMSG glyph_ :hello

        if iwords.IGroup.providedBy(recipient):
            recipientName = '#' + recipient.name
        else:
            recipientName = recipient.name

        text = message.get('text', '<an unrepresentable message>')
        for L in text.splitlines():
            self.privmsg(
                '%s!%s@%s' % (sender.name, sender.name, self.hostname),
                recipientName,
                L)

    def groupMetaUpdate(self, group, meta):
        if 'topic' in meta:
            topic = meta['topic']
            author = meta.get('topic_author', '')
            self.topic(
                self.name,
                '#' + group.name,
                topic,
                '%s!%s@%s' % (author, author, self.hostname)
                )
    # irc.IRC callbacks - starting with login related stuff.
    nickname = None
    password = None

    def irc_PASS(self, prefix, params):
        """Password message -- Register a password.

        Parameters: <password>

        [REQUIRED]

        Note that IRC requires the client send this *before* NICK
        and USER.
        """
        self.password = params[-1]

    def irc_NICK(self, prefix, params):
        """Nick message -- Set your nickname.

        Parameters: <nickname>

        [REQUIRED]
        """
        try:
            nickname = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.privmsg(
                USESERV,
                nickname,
                'Your nickname is cannot be decoded.  Please use ASCII or UTF-8.')
            self.transport.loseConnection()
            return

        password = self.password
        self.password = None
        self.logInAs(nickname, password)

    def irc_USER(self, prefix, params):
        """User message -- Set your realname.

        Parameters: <user> <mode> <unused> <realname>
        """
        # Note: who gives a crap about this?  The IUser has the real
        # information we care about.  Save it anyway, I guess, just
        # for fun.
        self.realname = params[-1]


    def irc_USESERV_PRIVMSG(self, prefix, params):
        """Send a (private) message.

        Parameters: <msgtarget> <text to be sent>
        """
        target = params[0]
        password = params[-1]

        if self.nickname is None:
            # XXX Send an error response here
            self.transport.loseConnection()
        elif target.lower() != "nickserv":
            self.privmsg(
                USESERV,
                self.nickname,
                "Denied. ")
        else:
            nickname = self.nickname
            self.nickname = None
            self.logInAs(nickname, password)

    def getPrefixMapping(self):
        k = PREFIX.keys()
        return '(%s)%s' % (''.join(k), ''.join([ PREFIX[i] for i in k ]))

    def logInAs(self, nickname, password):
        d = self.factory.portal.login(credentials.UsernamePassword(nickname, password), self, iwords.IUser)
        d.addCallbacks(self._cbLogin, self._ebLogin, errbackArgs=(nickname,))

    _welcomeMessages = [
        (irc.RPL_WELCOME,
         ":connected to Apollo"),
        (irc.RPL_YOURHOST,
         ":Your host is %(serviceName)s, running version %(serviceVersion)s"),
        (irc.RPL_CREATED,
         ":This server was created on %(creationDate)s"),

        (irc.RPL_MYINFO,
         "%(serviceName)s %(serviceVersion)s %(UMODES)s %(PMODES)s"),
        (irc.RPL_MYINFO, 
         "MAP KNOCK SAFELIST HCN WATCH=%(WATCH)s SILENCE=%(SILENCE)s MODES=%(MODES)s " +
         "MAXCHANNELS=%(MAXCHANNELS)s MAXBANS=%(MAXBANS)s NICKLEN=%(NICKLEN)s " + 
         "TOPICLEN=%(TOPICLEN)s KICKLEN=%(KICKLEN)s CHANTYPES=%(CHANTYPES)s" + 
         "PREFIX=%(PREFIX)s CHANMODES=%(CHANMODES)s are supported by this server")
        ]


    def _cbLogin(self, (iface, avatar, logout)):
        assert iface is iwords.IUser, "Realm is buggy, got %r" % (iface,)

        # Let them send messages to the world
        #del self.irc_PRIVMSG  # By deleting the method? Hello?
        print repr(avatar)

        self.avatar = avatar
        self.logout = logout
        self.realm = avatar.realm
        self.hostname = self.realm.name

        info = {
            "serviceName": self.hostname,
            "serviceVersion": "Apollo-0.1",
            "creationDate": ctime(), 
            "UMODES": UMODES,
            "PMODES": PMODES,
            "WATCH": WATCH,
            "SILENCE": SILENCE,
            "MODES": MODES,
            "MAXCHANNELS" : MAXCHANNELS,
            "MAXBANS" : MAXBANS,
            "NICKLEN" : NICKLEN,
            "TOPICLEN" : TOPICLEN,
            "KICKLEN" : KICKLEN,
            "CHANTYPES" : CHANTYPES,
            "PREFIX" : self.getPrefixMapping(),
            "CHANMODES": CHANMODES
            }
        for code, text in self._welcomeMessages:
            self.sendMessage(code, text % info)

    def _ebLogin(self, err, nickname):
        if err.check(ewords.AlreadyLoggedIn):
            self.privmsg(
                USESERV,
                nickname,
                "Already logged in.  No pod people allowed!")
        elif err.check(ecred.UnauthorizedLogin):
            self.privmsg(
                USESERV,
                nickname,
                "Login failed.  Goodbye.")
        else:
            log.msg("Unhandled error during login:")
            log.err(err)
            self.privmsg(
                USESERV,
                nickname,
                "Server error during login.  Sorry.")
        self.transport.loseConnection()

    # Great, now that's out of the way, here's some of the interesting
    # bits
    def irc_PING(self, prefix, params):
        """Ping message

        Parameters: <server1> [ <server2> ]
        """
        if self.realm is not None:
            self.sendMessage('PONG', self.hostname)


    def irc_QUIT(self, prefix, params):
        """Quit

        Parameters: [ <Quit Message> ]
        """
        self.transport.loseConnection()

    def channelMode(self, user, channel, mode, *args):
        print "passing channel modes"
        self.sendLine(":%s %s %s %s %s %s" % (
            self.hostname, irc.RPL_CHANNELMODEIS, user, channel, mode, ' '.join(args)))
            
    def setChannelMode(self, user, channel, mode, *args):
        print "setting channel mode"
        self.sendLine(":%s MODE %s %s %s" % (user, channel, mode, ' '.join(args)))

    def _channelMode(self, group, modes=None, *targets):
        print "%s/%s by %s " % ('#'+group.name, modes, self.avatar.name) # some debug
        # TODO - Implement ban lists
        #        invite lists (UnrealIRCd feature)

        def applyMode(m, *rest):
            print m, rest
            if m in CHANMODES:
                if not rest: # no user target, must be a channel mode
                    group.meta['modes'].append(mode)
                elif m in PREFIX.keys(): # Is a user prefix mode
                    group.modeUser(self.avatar.name, m)
                elif m == 'b':
                    self.channelBans(group.name)
                self.setChannelMode(self.avatar.name+"!@userCloud", "#" + group.name, "+%s" % m, *rest)

        # Set a mode
        if modes:
            if modes[0]=='+' or modes[0]=='-':
                modeList = modes[1:]
                if targets:
                    for mode, target in zip(modeList, targets):
                        applyMode(mode, target)
                else:
                    for mode in modeList:
                        applyMode(mode)
        # List modes    
        else:
            self.channelMode(self.name, '#' + group.name, group.getModes())


    def _userMode(self, user, modes=None):
        self.notice(USESERV, user.name, "This server doesn't care about umodes, don't bother setting them")
        modes = ""
        if modes:
            self.sendMessage(
                irc.ERR_UNKNOWNMODE,
                ":Unknown MODE flag.")
        elif user is self.avatar:
            self.sendMessage(
                irc.RPL_UMODEIS,
                "+")
        else:
            self.sendMessage(
                irc.ERR_USERSDONTMATCH,
                ":You can't look at someone else's modes.")


    def irc_MODE(self, prefix, params):
        print params
        try:
            channelOrUser = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOSUCHNICK, params[0],
                ":No such nickname (could not decode your unicode!)")
            return

        if channelOrUser.startswith('#'):
            # Try channel mode
            def ebGroup(err):
                err.trap(ewords.NoSuchGroup)
                self.sendMessage(irc.ERR_NOSUCHCHANNEL, params[0], ":That channel doesn't exist.")
            d = self.realm.lookupGroup(channelOrUser[1:])
            d.addCallbacks(self._channelMode, ebGroup, callbackArgs=tuple(params[1:]))

        else:
            def ebUser(err):
                self.sendMessage(irc.ERR_NOSUCHNICK,":No such nickname.") 

            d = self.realm.lookupUser(channelOrUser)
            d.addCallbacks(self._userMode, ebUser, callbackArgs=tuple(params[1:]))


    def irc_USERHOST(self, prefix, params):
        """Userhost message

        Parameters: <nickname> *( SPACE <nickname> )

        [Optional]
        """
        pass

    def aresCommand(self, command):
        if "o rly" in command:
            self.notice(USESERV, self.avatar.name, "YA RLY")
        
        splitCmd = command.lower().split()
        print splitCmd
        if splitCmd[0] == "identify":
            if splitCmd[1] == "yarly":
                self.avatar.authoriseUser()
                self.notice(USESERV, self.avatar.name, "Login accepted")
            else:
                self.notice(USESERV, self.avatar.name, "Login rejected")

    def irc_PRIVMSG(self, prefix, params):
        """Send a (private) message.

        Parameters: <msgtarget> <text to be sent>
        """
            
        try:
            targetName = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOSUCHNICK, targetName,
                ":No such nick/channel (could not decode your unicode!)")
            return

        messageText = params[-1]
        if targetName.startswith('#'):
            target = self.realm.lookupGroup(targetName[1:])
        elif targetName.lower() == "ares":
            self.aresCommand(messageText.lower())
        else:
            target = self.realm.lookupUser(targetName).addCallback(lambda user: user.mind)

        def cbTarget(targ):
            if targ is not None:
                return self.avatar.send(targ, {"text": messageText})

        def ebTarget(err):
            self.sendMessage(
                irc.ERR_NOSUCHNICK, targetName,
                ":No such nick/channel.")

        if targetName.lower()=="ares":
            pass
        #  Part of "shun user untill identified" concept, to deter spammers.
        #elif not self.avatar.shunned:
        #    target.addCallbacks(cbTarget, ebTarget)
        #else:
        #    self.notice(USESERV, self.avatar.name, "You are shunned and cannot send messages. ")
        else:
            target.addCallbacks(cbTarget, ebTarget)
            

    def irc_JOIN(self, prefix, params):
        """Join message

        Parameters: ( <channel> *( "," <channel> ) [ <key> *( "," <key> ) ] )
        """
        print self.avatar
        try:
            groupName = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.IRC_NOSUCHCHANNEL, params[0],
                ":No such channel (could not decode your unicode!)")
            return

        if groupName.startswith('#'):
            groupName = groupName[1:]

        def cbGroup(group):
            def cbJoin(ign):
                self.userJoined(group, self)
                self.names(
                    self.name,
                    '#' + group.name,
                    group.getPrefixedNames())
                self._sendTopic(group)
            if group.isBanned(self.avatar.name):
                # user is banned from channel
                self.notice(USESERV, self.avatar.name, "Sorry, you have been banned from #" + group.name)
                return None
            return self.avatar.join(group).addCallback(cbJoin)

        def ebGroup(err):
            # Try to add channel on empty join.
            def reallyFail(groupName):
                self.sendMessage(irc.ERR_NOSUCHCHANNEL, '#' + groupName, ": Cannot join that channel")

            def joinChannel(_):
                self.realm.getGroup(groupName).addCallbacks(cbGroup, reallyFail)
                # Make the user +o
                
            self.realm.addGroup(Group(groupName)).addCallbacks(joinChannel, reallyFail)

        self.realm.getGroup(groupName).addCallbacks(cbGroup, ebGroup)

    def irc_PART(self, prefix, params):
        """Part message

        Parameters: <channel> *( "," <channel> ) [ <Part Message> ]
        """
        try:
            groupName = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOTONCHANNEL, params[0],
                ":Could not decode your unicode!")
            return

        if groupName.startswith('#'):
            groupName = groupName[1:]

        if len(params) > 1:
            reason = params[1].decode('utf-8')
        else:
            reason = None

        def cbGroup(group):
            def cbLeave(result):
                self.userLeft(group, self, reason)
            return self.avatar.leave(group, reason).addCallback(cbLeave)

        def ebGroup(err):
            err.trap(ewords.NoSuchGroup)
            self.sendMessage(
                irc.ERR_NOTONCHANNEL,
                '#' + groupName,
                ":" + err.getErrorMessage())

        self.realm.lookupGroup(groupName).addCallbacks(cbGroup, ebGroup)

    def irc_NAMES(self, prefix, params):
        """Names message

        Parameters: [ <channel> *( "," <channel> ) [ <target> ] ]
        """
        #<< NAMES #python
        #>> :benford.openprojects.net 353 glyph = #python :Orban ... @glyph ... Zymurgy skreech
        #>> :benford.openprojects.net 366 glyph #python :End of /NAMES list.
        try:
            channel = params[-1].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOSUCHCHANNEL, params[-1],
                ":No such channel (could not decode your unicode!)")
            return

        if channel.startswith('#'):
            channel = channel[1:]

        def cbGroup(group):
            self.names(
                self.name,
                '#' + group.name,
                group.getPrefixedNames())

        def ebGroup(err):
            err.trap(ewords.NoSuchGroup)
            # No group?  Fine, no names! 
            self.names(
                self.name,
                '#' + group.name,
                [])

        self.realm.lookupGroup(channel).addCallbacks(cbGroup, ebGroup)

    def irc_TOPIC(self, prefix, params):
        """Topic message

        Parameters: <channel> [ <topic> ]
        """
        try:
            channel = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOSUCHCHANNEL,
                ":That channel doesn't exist (could not decode your unicode!)")
            return

        if channel.startswith('#'):
            channel = channel[1:]

        if len(params) > 1:
            self._setTopic(channel, params[1])
        else:
            self._getTopic(channel)


    def _sendTopic(self, group):
        topic = group.meta.get("topic")
        author = group.meta.get("topic_author") or "<noone>"
        date = group.meta.get("topic_date", 0)
        self.topic(self.name, '#' + group.name, topic)
        self.topicAuthor(self.name, '#' + group.name, author, date)

    def _getTopic(self, channel):
        #<< TOPIC #python
        #>> :benford.openprojects.net 332 glyph #python :<churchr> I really did. I sprained all my toes.
        #>> :benford.openprojects.net 333 glyph #python itamar|nyc 994713482
        def ebGroup(err):
            err.trap(ewords.NoSuchGroup)
            self.sendMessage(
                irc.ERR_NOSUCHCHANNEL, '=', channel,
                ":That channel doesn't exist.")

        self.realm.lookupGroup(channel).addCallbacks(self._sendTopic, ebGroup)


    def _setTopic(self, channel, topic):
        def cbGroup(group):
            newMeta = group.meta.copy()
            newMeta['topic'] = topic
            newMeta['topic_author'] = self.name
            newMeta['topic_date'] = int(time())

            def ebSet(err):
                self.sendMessage(
                    irc.ERR_CHANOPRIVSNEEDED,
                    "#" + group.name,
                    ":You need to be a channel operator to do that.")
            if 't' in newMeta['modes']:
                if newMeta['prefixes'].get(self.name, None):
                    if PREFIXPRIO[newMeta['prefixes'][self.name]] < 3:
                        return group.setMetadata(newMeta).addErrback(ebSet)
                return ebSet(None)
            else:
                return group.setMetadata(newMeta).addErrback(ebSet)

        def ebGroup(err):
            err.trap(ewords.NoSuchGroup)
            self.sendMessage(
                irc.ERR_NOSUCHCHANNEL, '=', channel,
                ":That channel doesn't exist.")

        self.realm.lookupGroup(channel).addCallbacks(cbGroup, ebGroup)


    def list(self, channels):
        """Send a group of LIST response lines

        @type channel: C{list} of C{(str, int, str)}
        @param channel: Information about the channels being sent:
        their name, the number of participants, and their topic.
        """
        for (name, size, topic) in channels:
            self.sendMessage(irc.RPL_LIST, name, str(size), ":" + topic)
        self.sendMessage(irc.RPL_LISTEND, ":End of /LIST")


    def irc_LIST(self, prefix, params):
        """List query

        Return information about the indicated channels, or about all
        channels if none are specified.

        Parameters: [ <channel> *( "," <channel> ) [ <target> ] ]
        """
        #<< list #python
        #>> :orwell.freenode.net 321 exarkun Channel :Users  Name
        #>> :orwell.freenode.net 322 exarkun #python 358 :The Python programming language
        #>> :orwell.freenode.net 323 exarkun :End of /LIST
        if params:
            # Return information about indicated channels
            try:
                channels = params[0].decode(self.encoding).split(',')
            except UnicodeDecodeError:
                self.sendMessage(
                    irc.ERR_NOSUCHCHANNEL, params[0],
                    ":No such channel (could not decode your unicode!)")
                return

            groups = []
            for ch in channels:
                if ch.startswith('#'):
                    ch = ch[1:]
                groups.append(self.realm.lookupGroup(ch))

            groups = defer.DeferredList(groups, consumeErrors=True)
            groups.addCallback(lambda gs: [r for (s, r) in gs if s])
        else:
            # Return information about all channels
            groups = self.realm.itergroups()

        def cbGroups(groups):
            def gotSize(size, group):
                return group.name, size, group.meta.get('topic')
            d = defer.DeferredList([
                group.size().addCallback(gotSize, group) for group in groups])
            d.addCallback(lambda results: self.list([r for (s, r) in results if s]))
            return d
        groups.addCallback(cbGroups)


    def _channelWho(self, group):
        self.who(self.name, '#' + group.name,
            [(m.name, self.hostname, self.realm.name, m.name, "H", 0, m.name) for m in group.iterusers()])


    def _userWho(self, user):
        self.sendMessage(irc.RPL_ENDOFWHO,
                         ":User /WHO not implemented")
    def irc_WHO(self, prefix, params):
        """Who query

        Parameters: [ <mask> [ "o" ] ]
        """
        #<< who #python
        #>> :x.opn 352 glyph #python aquarius pc-62-31-193-114-du.blueyonder.co.uk y.opn Aquarius H :3 Aquarius
        # ...
        #>> :x.opn 352 glyph #python foobar europa.tranquility.net z.opn skreech H :0 skreech
        #>> :x.opn 315 glyph #python :End of /WHO list.
        ### also
        #<< who glyph
        #>> :x.opn 352 glyph #python glyph adsl-64-123-27-108.dsl.austtx.swbell.net x.opn glyph H :0 glyph
        #>> :x.opn 315 glyph glyph :End of /WHO list.
        if not params:
            self.sendMessage(irc.RPL_ENDOFWHO, ":/WHO not supported.")
            return

        try:
            channelOrUser = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.RPL_ENDOFWHO, params[0],
                ":End of /WHO list (could not decode your unicode!)")
            return

        if channelOrUser.startswith('#'):
            def ebGroup(err):
                err.trap(ewords.NoSuchGroup)
                self.sendMessage(
                    irc.RPL_ENDOFWHO, channelOrUser,
                    ":End of /WHO list.")
            d = self.realm.lookupGroup(channelOrUser[1:])
            d.addCallbacks(self._channelWho, ebGroup)
        else:
            def ebUser(err):
                err.trap(ewords.NoSuchUser)
                self.sendMessage(
                    irc.RPL_ENDOFWHO, channelOrUser,
                    ":End of /WHO list.")
            d = self.realm.lookupUser(channelOrUser)
            d.addCallbacks(self._userWho, ebUser)

    def irc_WHOIS(self, prefix, params):
        """Whois query

        Parameters: [ <target> ] <mask> *( "," <mask> )
        """
        def cbUser(user):
            self.whois(
                self.name,
                user.name, user.name, "userCloud",
                user.name, self.realm.name, 'For Honour!', False,
                int(time() - user.lastMessage), user.signOn,
                ['#' + group.name for group in user.itergroups()])

        def ebUser(err):
            err.trap(ewords.NoSuchUser)
            self.sendMessage(
                irc.ERR_NOSUCHNICK,
                params[0],
                ":No such nick/channel")

        try:
            user = params[0].decode(self.encoding)
        except UnicodeDecodeError:
            self.sendMessage(
                irc.ERR_NOSUCHNICK,
                params[0],
                ":No such nick/channel")
            return

        self.realm.lookupUser(user).addCallbacks(cbUser, ebUser)

    def irc_OPER(self, prefix, params):
        """Oper message

        Parameters: <name> <password>
        """
        self.sendMessage(irc.ERR_NOOPERHOST, ":O-lines not applicable")

