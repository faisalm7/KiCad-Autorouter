"""One fixed public DNS prerequisite, executed only in the bounded setup job."""
import ipaddress
import json
import socket

rows = socket.getaddrinfo('api.github.com', 443, socket.AF_INET, socket.SOCK_STREAM)
if not rows or len(rows) > 64:
    raise RuntimeError('Unexpected bounded DNS result population')
address = rows[0][4][0]
if not ipaddress.ip_address(address).is_global:
    raise RuntimeError('Expected a public IPv4 endpoint')
print(json.dumps({'hostname': 'api.github.com', 'IPv4': address}))
