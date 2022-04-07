# -*- encoding: utf-8 -*-

"""
平芜泫 DNS 代理服务器的解析类。

作者：平芜泫（airyai@gmail.com）。
时间：2011/8/8。
"""

from twisted.names import dns, client

class UpstreamResolver(client.Resolver):
	def __init__(self, address, port, is_tcp=False, timeout=None):
		"""
		创建一个 UpstreamResolver 的对象。
		
		参数：
		
		address -- 字符串。上游服务器的地址。
		port -- 数值。上游服务器的端口。
		is_tcp -- 布尔值。如果为 True，则使用 TCP 连接上游服务器。
		timeout -- 数值，上游服务器的查询超时时间。
		  如果为 None，则使用默认值 10 秒钟。
		"""
		
		# 记录参数
		self.address = address
		self.port = port
		self.is_tcp = is_tcp
		self.resolv_timeout = timeout
		if timeout is None:
			self.resolv_timeout = 10
		
		# 初始化基类
		client.Resolver.__init__(self, servers=[(address, port)])

		
	def _my_query(self, query, timeout=None):
		# 检查 timeout 设定
		if timeout is None:
			timeout = self.resolv_timeout
		if isinstance(timeout, tuple) or isinstance(timeout, list):
			if len(timeout) > 0:
				timeout = timeout[0]
			else:
				timeout = self.resolv_timeout
				
		# 创建查询
		if self.is_tcp:
			ret = self.queryTCP([query], timeout)
		else:
			ret = self.queryUDP([query], [timeout])
		ret.addCallback(self.filterAnswers)
		return ret
		
	def lookupAddress(self, name, timeout=None):
		return self._my_query(dns.Query(name, dns.A, dns.IN), timeout)
	
	# Fix strange bug when object disposed.
	# bug exists under Twisted 11.0
	def connectionLost(self, p):
		pass
		
if __name__ == '__main__':
	from twisted.internet import reactor, defer
	def printData(d):
		print d
		
	up = UpstreamResolver("8.8.4.4", 53, True)
	d1 = up.lookupAddress("www.google.com")
	d2 = up.lookupAddress("www.twitter.com")
	d1.addCallback(printData)
	d2.addCallback(printData)
	
	reactor.callLater(5, reactor.stop)
	reactor.run()
		

