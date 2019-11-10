#!/usr/bin/python3

import BaseEnricher
import json,csv

class Enricher(BaseEnricher.BaseEnricher):
	METADATA = {
		'AUTHOR':'Michael R. Torres',
		'NAME':'Top1M',
		'DESCRIPTION':'Returns rank of the domain in Cisco OpenDNS Top1m domains or 0',
		'VERSION':'1.0',
		'PARAMETERS':'data: The domain to return the ranking of.'
	}
	shouldCache = True
	
	def do_enrich(self, args: dict) -> str:
		if( args.get('data') == None ):
			return "0"
			
		target = args['data'].lower()
		
		value = 0
		with open('resources/top1m/top-1m.csv', 'r') as top1m_fl:
			csv_obj = csv.reader(top1m_fl)
			for row in csv_obj:
				if( row[1] == target ):
					value = row[0]
					break

		return str(value)