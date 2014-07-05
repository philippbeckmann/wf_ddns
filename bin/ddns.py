#!/usr/bin/python
# Use this script to update a DNS override using the webfaction API
# be sure to set your username, password, dns override, and ethernet interface.
# Then add a crontab entry for the script, I use every 5 minutes
# */5 * * * * /path/to/ddns.py
# This is safe as the script exit(0)'s if the ip is the same as what is recorded in the file.
# Webfaction documentation on DNS overrides
# http://docs.webfaction.com/user-guide/domains.html#overriding-dns-records-with-the-control-panel
 
import xmlrpclib
 
import socket
import fcntl
import struct
import json
from datetime import datetime

current_ip_file = '/etc/ddns/current_ip'

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname.encode('ascii','ignore')[:15])
    )[20:24])

config = json.load(open('/etc/ddns/ddns.json'))

try:
    old_ip_address = open(current_ip_file).read()
    print 'Old IP: %s' % old_ip_address
except:
    old_ip_address = '0.0.0.0'

current_ip_address = get_ip_address(config['ethernet_interface'])
print 'Current IP: %s' % current_ip_address
if old_ip_address == current_ip_address:
    exit(0)

print 'updating to webfaction'
 
# Create an object to represent our server.
server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
session_id, account = server.login(config['web_faction_username'], config['web_faction_password'])
print 'deleting old dns entry'
server.delete_dns_override(session_id, config['web_faction_dns_override'])
print 'creating new dns entry'
server.create_dns_override(session_id, config['web_faction_dns_override'], current_ip_address)
 
if config['web_faction_ip_file']:
    print 'writing current_ip.json'
    data = json.dumps({'IP': current_ip_address, 'Date': datetime.now().isoformat()}, sort_keys=True, indent=4, separators=(',', ': '))
    server.write_file(session_id, config['web_faction_ip_file'], data, 'w')

open(current_ip_file, 'w+').write(current_ip_address)