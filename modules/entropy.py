#!/usr/bin/python3

import BaseEnricher
import json,math

class Enricher(BaseEnricher.BaseEnricher):
	METADATA = {
		'AUTHOR':'Michael R. Torres',
		'NAME':'Entropy',
		'DESCRIPTION':'Returns the Shannon entropy of the provided string. Defaults to using DNS charset.',
		'VERSION':'1.0',
		'PARAMETERS':'data: The string to be analyzed; charset: Optional; Character set of the string'
	}
	shouldCache = True
	
	def do_enrich(self, args):
		if( args.get('data') == None ):
			return "0"
		
		target = args['data'].upper()
		charset = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-" if args.get('charset') == None else args['charset']
		
		entropy = 0
		for char in charset:
			p_x = float(target.count(char))/len(target)
			if( p_x > 0 ):
				entropy += - p_x*math.log(p_x, 2)
				
		return str(entropy)