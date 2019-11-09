## EnrichServer
An asynchronous, modular HTTP server for enrichment of arbitrary data.

Written in Python3, supports HTTP GET/POST requests and in-memory caching of results.

### Usage

To start the server, execute _EnrichServer.py_. The server listens on port 8080 by default


API requests roughly follow the format of http://&lt;server>/api/&lt;endpoint>?&lt;param1>=&lt;val1>&&lt;param2>=&lt;val2>...

The following API endpoints are available.
* api/&lt;module>?info - Returns all available metadata on the module
* api/&lt;module>?&lt;params>

If debug is enabled with the --debug flag:
* debug/list - Returns a list of the currently available modules
* debug/cache - Returns the current cache of results
	
POST requests may be made to the same endpoints, with arguments passed in key-value pairs or as JSON. 

JSON body should be in the following format
```
{
	"action":<enrich|info>,
	"module":<module_name>,
	"args": {"data":"val", "data2","val2", ...}
}
```
	
	
All modules must be stored in ./modules/, relative to pwd of EnrichServer.py.

Modules *must* implement a class named _Enricher_ as a subset of the _BaseEnricher.BaseEnricher_ class.

Modules *should* include an override for the _do_enrich_ method, where the arguments to the enricher are passed as a dict.

Modules *may* enable in-memory caching of results by setting the member variable _shouldCache_ to True.

NOTE: Caching is limited to a default of 100 entries per module by default

Currently provided modules are as follows:
* Sleeper - Sleeps for 10 seconds then echos the _data_ parameter; Used to test asynch
* StrRev - Returns the mirror of the _data_ parameter
* Entropy - Returns the Shannon entropy of the _data_ parameter over an optional _charset_ parameter( Default to DNS ASCII charset )

Planned modules:
* UmbrellaTop1M - Return the ranking of the domain provided in _data_
* WHOIS - Return WHOIS data for domain provided in _data_
* ASN - Provide ASN information(including owner) of IP address in _data_
* ES_Query - Return the result of _query_ against _es_server_
	


	
	

	
