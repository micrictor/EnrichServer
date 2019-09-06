#!/usr/bin/python3

import importlib,urllib,json,os,threading

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import socketserver

class EnrichmentHTTPServer(ThreadingHTTPServer):
	def __init__(self, server_address, request_handler):
		self.cache = EnrichmentCache()
		return ThreadingHTTPServer.__init__(self, server_address, request_handler)
		
class EnrichmentRequestHandler(BaseHTTPRequestHandler):
	def __init__(self, request, client_address, server):
		self.enricher = EnrichmentHandler(server.cache)
		self.server_version = "EnrichAPI/0.1"
		return BaseHTTPRequestHandler.__init__(self, request, client_address, server)
		
	# Proper GET format is http://server/api/<module_name>?<arg>=<val>&<arg2>=<val2>
	def do_GET(self):
		parsed_req = urllib.parse.urlparse(self.path)
		
		req_uri = parsed_req.path.split('/')
		module_name = req_uri[-1]
		
		if( req_uri[-1] == "list" ):
			try:
				module_list = self.enricher.list_modules()
				self.send_response(200)
				self.end_headers()
				self.wfile.write(module_list.encode())
			except:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b'Unspecified server error!')
				
			return
			
		if( req_uri[-1] == "cache" ):
			try:
				self.send_response(200)
				self.end_headers()
				self.wfile.write(str(self.server.cache._cache).encode())
			except:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b'Unspecified server error!')
				
			return
		
		if( req_uri[-1] == "info" ):
			try:
				module_info = self.enricher.get_module_info(req_uri[-2])
				self.send_response(200)
				self.end_headers()
				self.wfile.write(module_info.encode())
			except:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b'Unspecified server error!')
				
			return
			
		arg_list = parsed_req.query.split('&')
		for arg in arg_list:
			arg_list[arg_list.index(arg)] = arg.split('=')
		arg_list = dict(arg_list)
		
		module_name = req_uri[-1]
		
		try:
			module_resp = self.enricher.do_enrich(module_name, arg_list)
			self.send_response(200)
			self.end_headers()
			self.wfile.write(module_resp.encode())
		except:
			self.send_response(500)
			self.end_headers()
			self.wfile.write(b'Unspecified server error!')
		
	# Accepts arguments as JSON-formatted data
	"""
	{
		"action":<enrich|info|list>,
		"module":<module_name>,
		"args": {"data":"val", "data2","val2", ...}
	}
	"""
	def do_POST(self):
		payload_len = int(self.headers['Content-Length'])
		payload = self.rfile.read(payload_len).decode()
		
		
		try:
			payload = json.loads(payload)
		except:
			self.send_response(500)
			self.end_headers()
			self.wfile.write(b'POST data not in JSON format!')
			return
		
		if( payload['action'] == "list" ):
			try:
				module_list = self.enricher.list_modules()
				self.send_response(200)
				self.end_headers()
				self.wfile.write(module_list.encode())
			except:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b'Unspecified server error!')

		elif( payload['action'] == "info" ):
			try:
				module_info = self.enricher.get_module_info(payload['module'])
				self.send_response(200)
				self.end_headers()
				self.wfile.write(module_info.encode())
			except:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b'Unspecified server error!')
				
		elif( payload['action'] == "enrich" ):
			try:
				module_resp = self.enricher.do_enrich(payload['module'], json.loads(payload['args']))
				self.send_response(200)
				self.end_headers()
				self.wfile.write(module_resp.encode())
			except:
				self.send_response(500)
				self.end_headers()
				self.wfile.write(b'Unspecified server error!')
		else:
			self.send_response(404)
			self.end_headers()
			self.wfile.write(b('Action %s not valid!' % payload['action']))
	
class EnrichmentHandler:
	def __init__(self, cache):
		self.cache = cache
		try :
			self.modules_available = list(x.replace('.py', '') for x in os.listdir('./modules/'))
			
			# There's probably a better way to do this
			self.modules_available.remove('__init__')
			self.modules_available.remove('__pycache__')
			self.modules_available.remove('BaseEnricher')
			
			self.modules = {}
			for module in self.modules_available:
				self.modules[module] = importlib.import_module('modules.' + module)
				self.modules[module] = self.modules[module].Enricher()
		except FileNotFoundError:
			print("ERROR! No modules found!")
			
	def is_valid_module(self, module_name):
		if( self.modules.get(module_name) == None ):
			return False
		return True
		
	def do_enrich(self, module, args):
		if( not self.is_valid_module(module) ):
			return ("Module %s not found!" % module)
			
		if( self.modules[module].shouldCache and self.cache.get(module, args) != None ):
			return self.cache.get(module,args)
		
		ret_val = self.modules[module].do_enrich(args)
		if( self.modules[module].shouldCache ):
			self.cache.set(module, args, ret_val)
			
		return ret_val
	
	def get_module_info(self, module):
		if( not self.is_valid_module(module) ):
			return ("Module %s not found!" % module)
			
		return self.modules[module].about()
		
	def list_modules(self):
		return json.dumps(self.modules_available)
	
class EnrichmentCache():
	def __init__(self, max_cache_len=100):
		self.max_cache_len = max_cache_len
		self._cache = dict()
		self._lock = dict()
		
	def create_cache(self, namespace):
		if( self._cache.get(namespace) == None ):
			self._cache.update({namespace:dict()})
			self._lock.update({namespace:threading.Lock()})
		else:
			print("Cache for %s already exists!" % namespace)
	
	#Assumes you already have lock
	def _delete_oldest_entry(self, namespace):
		self._cache[namespace].pop(list(self._cache[namespace])[0])

	def set(self, namespace, key, value):
		if( self._cache.get(namespace) == None ):
			self.create_cache(namespace)
			
		key = str(key) # Avoid issues with hashable types
		
		try:	
			self._lock[namespace].acquire()
			if( len(self._cache[namespace]) == self.max_cache_len ):
				self._delete_oldest_entry(namespace)
				
			self._cache[namespace].update({key:value})
		finally:
			self._lock[namespace].release()
			
	def get(self, namespace, key):
		if( self._cache.get(namespace) == None ):
			return None
		
		key = str(key) # Avoid issues with hashable types
		
		try:
			self._lock[namespace].acquire()
			if( self._cache[namespace].get(key) == None ):
				return None
			return self._cache[namespace][key]
		finally:
			self._lock[namespace].release()	
		
		
if __name__ == '__main__':
	http_server = EnrichmentHTTPServer(('',8080), EnrichmentRequestHandler)
	print("Starting HTTP server...")
	try:
		http_server.serve_forever()
	except KeyboardInterrupt:
		pass
	
	http_server.server_close()
	