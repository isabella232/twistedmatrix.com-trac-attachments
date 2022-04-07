from twisted.python import usage

class SomeSubCommand(usage.Options):
	pass

class Options(usage.Options):
	subCommands = [
		['foobar', 'foo', SomeSubCommand, "FIXME"],
		]

if __name__ == '__main__':
	Options().parseOptions()
