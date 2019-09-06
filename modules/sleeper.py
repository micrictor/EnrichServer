#!/usr/bin/python3

import BaseEnricher
import json,time


class Enricher(BaseEnricher.BaseEnricher):
	METADATA = {
		'AUTHOR':'Michael R. Torres',
		'NAME':'Sleeper',
		'DESCRIPTION':'Sleeps for 10 seconds, then echos the data',
		'VERSION':'1.0',
		'PARAMETERS':'data: The string to echoed'
	}
	
	def do_enrich(self, args):
		time.sleep(10)
		return args['data']
	