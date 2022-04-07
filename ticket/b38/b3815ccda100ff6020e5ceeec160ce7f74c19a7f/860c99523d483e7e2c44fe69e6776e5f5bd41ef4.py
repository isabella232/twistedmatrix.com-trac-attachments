# -*- coding: utf-8 -*-
import random
import timeit
 
from test.test_iterlen import len

class BaseBuffer(object):
    delimiter = "\r\n"
    MAX_LENGTH = 16384

    def __init__(self):
        self.clearLineBuffer()
    
    def clearLineBuffer(self):
        return ""

    def dataReceived(self, data):
        pass
    
    def lineReceived(self, line):
        pass

class ArrayBuffer(BaseBuffer):
    _buffer = None

    def clearLineBuffer(self):
        self._buffer = []
        return ""

    def dataReceived(self, data):
        self._buffer+=data
        last = "".join(self._buffer[-2:])
        try:
            if len(last.split(self.delimiter, 1)) > 1:
                line = "".join(self._buffer)
                result, newItem = line.split(self.delimiter, 1)
                self.lineReceived(result)
                self._buffer = [newItem]
        except ValueError:
            pass
    
class StringBuffer(BaseBuffer):
    _buffer = None
    
    def clearLineBuffer(self):
        self._buffer = ""
        return ""
    
    def dataReceived(self, data):
        self._buffer = self._buffer+data
        try:
            line, self._buffer = self._buffer.split(self.delimiter, 1)
            self.lineReceived(line)
        except ValueError:
            pass

class CheckBuffer(object):
    buffer = None
    bufClass = None
    
    def __init__(self, buffer):
        self.__prepareChunks(buffer)
    
    def __prepareChunks(self, buffer):
        self.buffer = buffer
        self.dataBuf = []
        while len(self.buffer) > 10:
            chunkLen = int(random.uniform(40, 100))
            self.dataBuf.append(self.buffer[:chunkLen])
            self.buffer = self.buffer[chunkLen:]
        self.dataBuf.append(self.buffer)
        self.buffer = buffer
    
    def workWithData(self):
        bufferClass = self.bufClass
        b = bufferClass()
        for s in self.dataBuf:
            b.dataReceived(s)

if __name__ == "__main__":
    c = CheckBuffer("""Here it is—a shiny new edition of Beginning Python. If you count its predecessor, Practical
        Python, this is actually the third edition, and a book I’ve been involved with for the better part
        of a decade. During this time, Python has seen many interesting changes, and I’ve done my best
        to update my introduction to the language. At the moment, Python is facing perhaps its most
        marked transition in a very long time: the introduction of version 3. As I write this, the final release
        isn’t out yet, but the features are clearly defined and working versions are available. One interesting
        challenge linked to this language revision is that it isn’t backward-compatible. In other words,
        it doesn’t simply add features that I could pick and choose from in my writing. It also changes the
        existing language, so that certain things that are true for Python 2.5 no longer hold.
        Had it been clear that the entire Python community would instantly switch to the new version
        and update all its legacy code, this would hardly be a problem. Simply describe the new
        language! However, a lot of code written for older versions exists, and much will probably still
        be written, until version 3 is universally accepted as The Way To Go™.
        So, how have I gotten myself out of this pickle? First of all, even though there are incompatible
        changes, most of the language remains the same. Therefore, if I wrote entirely about Python
        2.5, it would be mostly correct for Python 3 (and even more so for its companion release, 2.6).
        As for the parts that will no longer be correct, I have been a bit conservative and assumed that
        full adoption of version 3 will take some time. I have based the book primarily on 2.5, and noted
        things that will change throughout the text. In addition, I’ve included Appendix D, which gives
        you an overview of the main changes. I think this will work out for most readers.
        In writing this second edition, I have had a lot of help from several people. Just as with the
        previous two versions (the first edition, and, before it, Practical Python), Jason Gilmore got me
        started and played an important role in getting the project on the road. As it has moved along,
        Richard Dal Porto, Frank Pohlmann, and Dominic Shakeshaft have been instrumental in keeping
        it going. Richard Taylor has certainly played a crucial role in ensuring that the code is
        correct (and if it still isn’t, I’m the one to blame), and Marilyn Smith has done a great job tuning
        my writing. My thanks also go out to other Apress staff, including Liz Berry, Beth Christmas,
        Steve Anglin, and Tina Nielsen, as well as various readers who have provided errata and helpful
        suggestions, including Bob Helmbold and Waclaw Kusnierczyk. I am also, of course, still thankful
        to all those who helped in getting the first two incarnations of this book on the shelves.
    """)

    c.dataBuf *= 6
    c.bufClass = ArrayBuffer
    #c.bufClass = StringBuffer
    
    __builtins__.v_c = c
    c.workWithData()
    t = timeit.Timer("v_c.workWithData()", "")
    print t.timeit(1000)
