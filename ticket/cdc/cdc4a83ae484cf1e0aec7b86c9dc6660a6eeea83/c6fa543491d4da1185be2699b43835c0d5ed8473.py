from twisted.trial.unittest import TestCase

class Test(TestCase):
	def testTest(self):
		from twisted.internet.defer import succeed
		def check(result):
			print check
			self.assertEqual(result, 17)
			
		result = succeed(17)
		result.addCallback(check)
		return result
		