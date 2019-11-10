#!/usr/bin/python3

import json

class BaseEnricher:
	METADATA = {
		'AUTHOR':'John Q. Public',
		'NAME':'BaseEnricher',
		'DESCRIPTION':'Base enricher module.',
		'VERSION':'1.0',
		'PARAMETERS':'data: The string to be echoed'
	}
	
	#def __init__(self):
		
		
	def do_enrich(self, args: dict) -> str:
		return args['data']
	
	def about(self) -> str:
		return json.dumps(self.METADATA)
			