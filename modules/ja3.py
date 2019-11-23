#!/usr/bin/python3

import BaseEnricher
import json

class Enricher(BaseEnricher.BaseEnricher):
	METADATA = {
		'AUTHOR':'Michael R. Torres',
		'NAME':'JA3',
		'DESCRIPTION':'Returns the application linked to a JA3 MD5, or "unknown" if it cannot be determined.',
		'VERSION':'1.0',
		'PARAMETERS':'ja3: The JA3 MD5 to search for'
	}
	shouldCache = True
	
	def do_enrich(self, args: dict) -> str:
		if( args.get('ja3') == None ):
			return "unknown"
		
		target = args['ja3'].lower()
		
		app_name = "unknown"
		with open('resources/ja3/ja3fingerprint.json', 'r') as ja3_fl:
			curr_line = ja3_fl.readline()
			while curr_line:
				json_obj = json.loads(curr_line)
				if( json_obj['ja3_hash'] == target ):
					value = json_obj['desc']
					break
				curr_line = ja3_fl.readline()

		return str(value)