import csv
import requests
import xml.etree.ElementTree as ET
import sys
import time
import collectd
import six

INTERVAL = 10
PATH = ''
TIMEOUT = 10
PLUGIN = 'SNOW-XML'

default_dimensions = {}
metricType = 'semaphores'

def parseXML(file):
	semaphores = []
	global default_dimensions
	
	try:
		root = ET.fromstring(file)
		for semaphore in root.findall('./semaphores'):
			semaphores.append(semaphore)
		for instance_id in root.findall('./instance_id'):
			default_dimensions['instanceId'] = instance_id.text
		for instance_name in root.findall('./instance_name'):
			default_dimensions['instanceName'] = instance_name.text	
	except Exception as e:
		collectd.error('Failed to parse XML file %s' % (e))
	
	return semaphores

def format_dimensions(dimensions, more_dimensions=''):
    '''
    Formats dimensions before fed to collectd plugin instance
    '''
    formatted = []
    formatted.extend(("%s=%s" % (k, v)) for k, v in six.iteritems(dimensions))
    return ('[%s%s]' % (str(formatted).replace('\'', '').
            replace(' ', '').replace("\"", '').replace('[', '').
                replace(']', ''),
                '' if len(more_dimensions) == 1 else more_dimensions))


def prepare_plugin_instance(attribute, default_dimensions, more_dimensions=''):
    '''
    Prepares the plugin instance string to be passed to collectd
    '''
    default_dimensions = format_dimensions(default_dimensions,
        (more_dimensions))
    return ("%s%s" % (attribute, default_dimensions))


def config_callback(conf):

	for node in conf.children:
		try:
			if node.key == 'Interval':
				global INTERVAL
				INTERVAL = node.values[0]
			elif node.key == 'Path':
				global PATH
				PATH = node.values[0]
			elif node.key == 'Timeout':
				global TIMEOUT
				TIMEOUT = node.values[0]
		except Exception as e:
			collectd.error('Failed to load the configuration %s due to %s' % (node.key, e))
			raise e

def init_callback():
	collectd.register_read(read_callback,interval=INTERVAL)
	return True	

def read_callback():
	try:
		response = requests.get(PATH,timeout=TIMEOUT)
		
		if response.status_code != 200:
			collectd.info('Failed to reach url: %s , status code: %s' % (PATH,response.status_code))
			return		

		semaphores = parseXML(response.content)

		semaphoresCollected = {}

		for semaphore in semaphores:
			if len(semaphore.keys()) > 0:
				stats = []
				values = []
				name = ''
				for key in semaphore.keys():
					if key == 'name':
						name = semaphore.get(key)
					else:
						stats.append(key) 
						values.append(semaphore.get(key))
				if name != '':
					semaphoresCollected[name] = {}
					semaphoresCollected[name]['stats'] = stats
					semaphoresCollected[name]['values'] = values
				else:
					collectd.info('Found semaphore without a name %s',semaphore.items())

		for key in semaphoresCollected.keys():
			dispatch_values(key,semaphoresCollected[key]['stats'],semaphoresCollected[key]['values'])

	except Exception as e:
		collectd.error('Failed to fetch and transfer data due to %s' % (e))

def dispatch_values(name,stats,values):
	global default_dimensions
	global metricType
	default_dimensions['element']=name

	val = collectd.Values(type='gauge')
	val.plugin_instance = prepare_plugin_instance(metricType,default_dimensions)
	val.plugin = PLUGIN
	
	for iter in range(len(stats)):
		val.type_instance = stats[iter]
		val.values = [values[iter]]
		val.dispatch()

collectd.register_config(config_callback)
collectd.register_init(init_callback)

