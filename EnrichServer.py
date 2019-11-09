#!/usr/bin/python3

import argparse
import importlib,urllib,json,os,threading

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

DEBUG_ENABLED = 0

class EnrichmentHTTPServer(ThreadingHTTPServer):
	def __init__(self, server_address, request_handler, max_cache_len):
		self.cache = EnrichmentCache(max_cache_len)
		return ThreadingHTTPServer.__init__(self, server_address, request_handler)
		
class EnrichmentRequestHandler(BaseHTTPRequestHandler):
	def __init__(self, request, client_address, server):
		self.enricher = EnrichmentHandler(server.cache)
		self.server_version = "EnrichAPI/0.1"
		return BaseHTTPRequestHandler.__init__(self, request, client_address, server)
	
	def send_result(self, result_str: str) -> bool:
		try:
			self.send_response(200)
			self.end_headers()
			self.wfile.write(result_str.encode())
			return True
		except Exception as e:
			print("Failed to send result: %s" % str(e))
			return False

	def send_failed(self, err_str: str("Unspecified server error."), err_code: int(500)) -> bool:
		try:
			self.send_response(err_code)
			self.end_headers()
			self.wfile.write(err_str.encode())
			return True
		except Exception as e:
			print("Failed to send HTTP error: %s" % str(e))
			return False

	def handle_debug(self, action_name: str):
		if( action_name == "list" ):
			try:
				module_list = self.enricher.list_modules()
				self.send_result(module_list)
			except  Exception as e:
				self.send_failed(str(e))
		elif( action_name == "cache" ):
			try:
				self.send_result(str(self.server.cache._cache))
			except Exception as e:
				self.send_failed(str(e))
		return

	def handle_api(self, module_name: str, module_args: dict):
		if( module_args['info'] ):
			self.send_result(self.enricher.get_module_info(module_name))
			return
			
		try:
			self.send_result(self.enricher.do_enrich(module_name, module_args))
		except Exception as e:
			self.send_failed(str(e))
			
		return


	# Proper GET format is http://server/api/<module_name>?<arg>=<val>&<arg2>=<val2>
	def do_GET(self):
		parsed_req = urllib.parse.urlparse(self.path)
		
		req_uri = parsed_req.path.split('/')[1:] # Avoid null first string
		
		if( DEBUG_ENABLED and req_uri[0] == 'debug' ):
			self.handle_debug(req_uri[1])
		elif( req_uri[0] == 'api' ):
			arg_dict = parsed_req.query.split('&')
			for arg in arg_dict:
				arg_dict[arg_dict.index(arg)] = arg.split('=')

			# Handle the case of /api/module?info	
			try:
				arg_dict = dict(arg_dict)
			except:
				arg_dict = {arg_list[0][0]:True}

			self.handle_api(req_uri[1:],arg_dict)
		
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
			self.modules = {}

			for module in self.modules_available:
				try:
					self.modules[module] = importlib.import_module('modules.' + module)
					self.modules[module] = self.modules[module].Enricher()
				except:
					self.modules[module] = None
					continue
		except FileNotFoundError:
			print("ERROR! No modules found!")
			
	def is_valid_module(self, module_name: str) -> bool:
		if( self.modules.get(module_name) == None ):
			return False
		return True
		
	def do_enrich(self, module_name: str, module_args: dict) -> str:
		if( not self.is_valid_module(module_name) ):
			return ("Module %s not found!" % module_name)
			
		if( self.modules[module].shouldCache and self.cache.get(module_name, args) != None ):
			return self.cache.get(module_name,module_args)
		
		ret_val = self.modules[module_name].do_enrich(module_args)
		if( self.modules[module_name].shouldCache ):
			self.cache.set(module_name, args, ret_val)
			
		return ret_val
	
	def get_module_info(self, module_name: str) -> str:
		if( not self.is_valid_module(module_name) ):
			return ("Module %s not found!" % module_name)
			
		return self.modules[module_name].about()
		
	def list_modules(self) -> str:
		return json.dumps(self.modules_available)
	
class EnrichmentCache():
	def __init__(self, max_cache_len):
		self.max_cache_len = max_cache_len
		self._cache = dict()
		self._lock = dict()
		
	def create_cache(self, namespace: str):
		if( self._cache.get(namespace) == None ):
			self._cache.update({namespace:dict()})
			self._lock.update({namespace:threading.Lock()})
		else:
			print("Cache for %s already exists!" % namespace)
	
	#Assumes you already have lock
	def _delete_oldest_entry(self, namespace: str):
		self._cache[namespace].pop(list(self._cache[namespace])[0])

	def set(self, namespace: str, key: str, value: str):
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
			
	def get(self, namespace: str, key: str) -> str:
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

	parser = argparse.ArgumentParser(description="An HTTP API for data enrichment")
	parser.add_argument('--host', dest='host', help='IP address the server will bind to', default='')
	parser.add_argument('-p', '--port', dest='port', help='Port the server will bind to', default=8080, type=int)
	parser.add_argument('-m', '--max-cache', dest='max_cache_len', help='Maximum number of items to be cached per module', default=250, type=int)
	parser.add_argument('-d', '--debug', dest='enable_debug', help='Enable debug APIs', action='store_true')
	args = parser.parse_args()
	
	DEBUG_ENABLED = args.enable_debug

	http_server = EnrichmentHTTPServer((args.host,args.port), EnrichmentRequestHandler, args.max_cache_len)
	print("Starting HTTP server...")
	try:
		http_server.serve_forever()
	except KeyboardInterrupt:
		pass
	
	http_server.server_close()
	