# -*- encoding: utf-8 -*-
import sys
import logging

from twisted.logger import Logger, STDLibLogObserver, textFileLogObserver, jsonFileLogObserver, globalLogBeginner

log = Logger()

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

observers = {
    'json': jsonFileLogObserver(sys.stdout),
    'text': textFileLogObserver(sys.stdout),
    'stdlib': STDLibLogObserver(),
}

globalLogBeginner.beginLoggingTo([observers[arg] for arg in sys.argv[1:]], redirectStandardIO=False)

# log.info("plain ASCII")
# log.info(u"→ non-ASCII")
# log.info("str message {ascii_field}", ascii_field="ASCII")
# log.info("str message {unicode_field}", unicode_field=u"→ non-ASCII")
log.info("str message {utf8_field}", utf8_field=u"→ non-ASCII".encode("utf-8"))
# log.info(u"unicode message {ascii_field}", ascii_field="ASCII")
# log.info(u"unicode message {unicode_field}", unicode_field=u"→ non-ASCII")
# log.info(u"unicode message {utf8_field}", utf8_field=u"→ non-ASCII".encode("utf-8"))
