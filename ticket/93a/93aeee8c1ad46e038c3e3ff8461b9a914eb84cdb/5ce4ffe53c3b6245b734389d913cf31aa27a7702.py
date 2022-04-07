import decimal, datetime, re
from twisted.protocols import amp


class _FixedOffsetTZInfo(datetime.tzinfo):
    '''"Timezones? What timezones?" -- Python standard library'''

    def __init__(self, sign, hours, minutes):
        self.name = '%s%02i:%02i' % (sign, hours, minutes)
        if sign == '-':
            hours = -hours
            minutes = -minutes
        elif sign != '+':
            raise ValueError, 'invalid sign for timezone %r' % (sign,)
        self.offset = datetime.timedelta(hours=hours, minutes=minutes)

    def utcoffset(self, dt):
        return self.offset

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return self.name


UTCtzinfo = _FixedOffsetTZInfo('+', 0, 0)


class Decimal(amp.Argument):
    '''Encodes decimal.Decimal.
    
    Encoding on the wire is done with str() and Decimal(), which works great
    for python, but may not be the greatest considering interoperability with
    other decimal types. Someone should look at Decimal.__str__ and see if it
    is specified sufficiently well to be implemented elsewhere.
    '''
    fromString = decimal.Decimal
    def toString(self, inObject):
        return str(decimal.Decimal(inObject))


class DateTime(amp.Argument):
    '''Encodes datetime.DateTime.
    
    Wire format: '%04i-%02i-%02iT%02i:%02i:%02i.%06i%s%02i:%02i'. Fields in
    order are: year, month, day, hour, minute, second, microsecond, timezone
    direction (+ or -), timezone hour, timezone minute. Encoded string is
    always exactly 32 characters long. This format is compatible with ISO 8601,
    but that does not mean all ISO 8601 dates can be accepted.

    Also, note that the datetime module's notion of a "timezone" can be
    complex, but the wire format includes only a fixed offset, so the
    conversion is not lossless. A lossless transmission of a DateTime instance
    is not feasible since the receiving end would require a python interpreter.
    '''
    def fromString(self, s):
        if len(s) != 32:
            raise ValueError, 'invalid date format %r' % (s,)

        # strptime doesn't have any way to parse the microseconds or timezone

        date, timeAndZone = s.split('T', 1)
        time, zoneSign, zone = re.split(r'(\+|-)', timeAndZone, 2)
        year, month, day = map(int, date.split('-'))
        hour, minute, secondAndMicrosecond = time.split(':', 2)
        hour = int(hour)
        minute = int(minute)
        second, microsecond = map(int, secondAndMicrosecond.split('.', 1))
        zoneHour, zoneMinute = map(int, zone.split(':', 2))

        return datetime.datetime(year, month, day, hour, minute, second, microsecond, _FixedOffsetTZInfo(zoneSign, zoneHour, zoneMinute))

    def toString(self, i):
        offset = i.utcoffset()
        if offset is None:
            raise ValueError, 'datetimes going through AMP must have an associated timezone. You may find ampext.UTCtzinfo useful.'

        minutesOffset = (offset.days * 86400 + offset.seconds) // 60

        if minutesOffset > 0:
            sign = '+'
        else:
            sign = '-'

        # strftime has no way to format the microseconds, or put a ':' in the
        # timezone. Suprise!

        return '%04i-%02i-%02iT%02i:%02i:%02i.%06i%s%02i:%02i' % (
            i.year,
            i.month,
            i.day,
            i.hour,
            i.minute,
            i.second,
            i.microsecond,
            sign,
            abs(minutesOffset) // 60,
            abs(minutesOffset) % 60)


def test():
    timezones = [
        _FixedOffsetTZInfo('+', 0, 0),
        _FixedOffsetTZInfo('+', 2, 0),
        _FixedOffsetTZInfo('-', 5, 0),
        _FixedOffsetTZInfo('+', 3, 19),
        _FixedOffsetTZInfo('-', 6, 59),
    ]
    # callables taking a tz parameter and returning a datetime in that tz
    datetimes = [
        datetime.datetime.now,
    ]

    argument = DateTime()

    print 'checking DateTime'
    for tz in timezones:
        for makeDt in datetimes:
            dt = makeDt(tz)
            assert argument.fromString(argument.toString(dt)) == dt

    print 'all tests passed'
