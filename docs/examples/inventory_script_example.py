#!/usr/bin/env python

import json

inv = {
    '_meta': {
        'hostvars': {}
    },
    'hosts': []
}

for num in range(0, 3):
    host = u"host-%0.2d" % num
    inv['hosts'].append(host)
    inv['_meta']['hostvars'][host] = dict(ansible_ssh_host='127.0.0.1', ansible_connection='local')

print(json.dumps(inv, indent=2))
