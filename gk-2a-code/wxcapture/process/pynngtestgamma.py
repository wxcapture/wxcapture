#!/usr/bin/env python3
"""pynng test code"""

import time
import json
from pynng import Sub0

def process(p_address, p_port):
    """process the data"""
    print('-' * 130)
    print(p_address, p_port)
    try:
        with Sub0(dial=p_address + ':' + p_port, recv_timeout=100, topics="") as sub0:
                time.sleep(0.05)
                op = json.loads(sub0.recv().decode("utf-8"))
                print(op)
                print('>' + op['timestamp'])
                for key, value in op.items():
                    print('   ' + key, ' : ', value)
        sub0.close()
    except:
        print('issue connecting')

address1 = 'tcp://203.86.195.49'
address2 = 'tcp://127.0.0.1'

while True:
    process(address1, '6002')
    process(address2, '6002') 

    time.sleep(2)
