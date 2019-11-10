#!/usr/bin/python3

import BaseEnricher
import json


class Enricher(BaseEnricher.BaseEnricher):
	METADATA = {
		'AUTHOR':'Michael R. Torres',
		'NAME':'StrRev',
		'DESCRIPTION':'Reverses the provided string',
		'VERSION':'1.0',
		'PARAMETERS':'data: The string to be reversed'
	}
	shouldCache = True
	
	def do_enrich(self, args: dict) -> str:
		return args['data'][::-1]