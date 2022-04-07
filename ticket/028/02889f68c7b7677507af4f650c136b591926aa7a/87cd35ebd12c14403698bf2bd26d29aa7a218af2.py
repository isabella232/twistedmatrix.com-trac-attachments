# sorted andsoring in general makes cmp= exitinct 
# http://wiki.python.org/moin/HowTo/Sorting/ 

def by_name(n):
    rest, delim, suffix = n.rpartition('.')
    rest_parts = rest.split('.')
    return tuple( reversed(rest_parts + [-len(rest_parts)] + [suffix]) )

>>> sorted(['a.b.com', 'a.b.c.com', 'com', 'zzz.b.com', 'd.net', 'a.b.net'], key=by_name)
['a.b.c.com', 'a.b.com', 'zzz.b.com', 'com', 'a.b.net', 'd.net']
