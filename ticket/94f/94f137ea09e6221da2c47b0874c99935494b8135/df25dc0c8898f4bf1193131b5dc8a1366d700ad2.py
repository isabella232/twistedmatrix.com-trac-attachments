import StringIO

from OpenSSL.SSL import SSLv3_METHOD, TLSv1_METHOD

from twisted.mail.smtp import ESMTPSenderFactory
from twisted.python.usage import Options, UsageError
from twisted.internet.ssl import ClientContextFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor


def sendmail(
    authenticationUsername, authenticationSecret,
    fromAddress, toAddress,
    messageFile,
    smtpHost="email-smtp.us-east-1.amazonaws.com", smtpPort=587
    ):
    contextFactory = ClientContextFactory()
    contextFactory.method = TLSv1_METHOD

    resultDeferred = Deferred()

    senderFactory = ESMTPSenderFactory(
        authenticationUsername,
        authenticationSecret,
        fromAddress,
        toAddress,
        messageFile,
        resultDeferred,
        contextFactory=contextFactory,heloFallback=True
        )

    reactor.connectTCP(smtpHost, smtpPort, senderFactory)

    return resultDeferred, senderFactory

def main(reactor):
    d, f = sendmail(
        "user", "password", "alice@example.com", "bob@example.com",
        StringIO.StringIO("monkeys"))
    return d

from twisted.internet.task import react
react(main, [])
