from twisted.python.filepath import FilePath

a = FilePath('clean.txt')
b = FilePath('garbage.txt')

f = a.open('w')
f.write('\n')
f.close()

print repr(file('clean.txt', 'rb').read())

b.requireCreate()
f = b.open('w')
f.write('\n')
f.close()

print repr(file('garbage.txt', 'rb').read())


a.remove()
b.remove()
