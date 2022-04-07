"""Twisted-aware version of standard RobotFileParser"""
import robotparser
from twisted.web import client, error

class RobotFileParser( robotparser.RobotFileParser ):
	"""Sub-class of RobotFileParser using Twisted for networking

	As with the standard module, you call read, then run a set
	of queries using can_fetch to see if your user-agent is allowed
	to download the given URL.  Since this is twisted, you should
	be doing that in a callback registered with the deferred
	returned from the read method.
	"""
	def read( self, timeout=120 ):
		"""Retrieves robots.txt URL and feeds it to the parser

		timeout -- timeout in seconds before giving up

		returns deferred returning None
		"""
		df = client.getPage(
			url = self.url,
			timeout = timeout,
		)
		df.addCallback( self.onFileData )
		return df
	def onFileData( self, data ):
		"""Called on load of robots.txt file data"""
		lines = [ line.strip() for line in data.split( '\n' )]
		return self.parse(lines)
	def onRetrievalFailure( self, failure ):
		"""Called if load of robots.txt failed"""
		if isinstance( failure.value, error.Error ):
			code, summary, body = failure.value.args[:3]
			self.errcode = int(code)
			# if we are disallowed from reading, nothing is allowed
			if self.errcode == 401 or self.errcode == 403:
				self.disallow_all = 1
			# otherwise everything is assumed allowed
			elif self.errcode >= 400:
				self.allow_all = 1
			return None
		else:
			# unexpected failure case, propagate the failure
			return failure



def _test():
	"""Note: the original code and the twisted version both
	report failures from this suite, looks as though the robots.txt
	files being referenced may have changed since the test was
	written"""
	from twisted.internet import defer
	rp = RobotFileParser()

	# robots.txt that exists, gotten to by redirection
	rp.set_url('http://www.musi-cal.com/robots.txt')
	df = rp.read()

	def after( result ):
		# test for re.escape
		robotparser._check(rp.can_fetch('*', 'http://www.musi-cal.com/'), 1)
		# this should match the first rule, which is a disallow
		robotparser._check(rp.can_fetch('', 'http://www.musi-cal.com/'), 0)
		# various cherry pickers
		robotparser._check(rp.can_fetch('CherryPickerSE',
						   'http://www.musi-cal.com/cgi-bin/event-search'
						   '?city=San+Francisco'), 0)
		robotparser._check(rp.can_fetch('CherryPickerSE/1.0',
						   'http://www.musi-cal.com/cgi-bin/event-search'
						   '?city=San+Francisco'), 0)
		robotparser._check(rp.can_fetch('CherryPickerSE/1.5',
						   'http://www.musi-cal.com/cgi-bin/event-search'
						   '?city=San+Francisco'), 0)
		# case sensitivity
		robotparser._check(rp.can_fetch('ExtractorPro', 'http://www.musi-cal.com/blubba'), 0)
		robotparser._check(rp.can_fetch('extractorpro', 'http://www.musi-cal.com/blubba'), 0)
		# substring test
		robotparser._check(rp.can_fetch('toolpak/1.1', 'http://www.musi-cal.com/blubba'), 0)
		# tests for catch-all * agent
		robotparser._check(rp.can_fetch('spam', 'http://www.musi-cal.com/search'), 0)
		robotparser._check(rp.can_fetch('spam', 'http://www.musi-cal.com/Musician/me'), 1)
		robotparser._check(rp.can_fetch('spam', 'http://www.musi-cal.com/'), 1)
		robotparser._check(rp.can_fetch('spam', 'http://www.musi-cal.com/'), 1)

	df.addCallback( after )
	rp2 = RobotFileParser()
	rp2.set_url('http://www.lycos.com/robots.txt')
	df2 = rp2.read()
	def after2( result ):
		# robots.txt that does not exist
		robotparser._check(rp.can_fetch('Mozilla', 'http://www.lycos.com/search'), 1)
	df2.addCallback( after2 )
	return defer.DeferredList( [df,df2] )

if __name__ == "__main__":
	from twisted.internet import reactor
	def testMain( ):
		robotparser.debug=1
		df = _test()
		def quit( result ):
			reactor.stop()
		df.addCallback( quit )
		return df
	reactor.callWhenRunning( testMain )
	reactor.run()
