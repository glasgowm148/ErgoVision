#!/usr/bin/env python3

import os
import json
import random
import argparse
import webbrowser
import concurrent.futures

from time import sleep

from core.utils import getNew
from core.utils import ranker
from core.utils import genLocation
from core.exporter import exporter
from core.prepareGraph import prepareGraph
from core.getTransactions import getTransactions
from core.colors import green, white, red, info, run, end

parse = argparse.ArgumentParser()
parse.add_argument('-s', '--seeds', help='target blockchain address(es)', dest='seeds')
parse.add_argument('-o', '--output', help='output file to save raw JSON data', dest='output')
parse.add_argument('-d', '--depth', help='depth of crawling', dest='depth', type=int, default=3)
parse.add_argument('-t', '--top', help='number of addresses to crawl from results', dest='top', type=int, default=20)
parse.add_argument('-l', '--limit', help='maximum number of addresses to fetch from one address', dest='limit', type=int, default=100)
args = parse.parse_args()

top = args.top
seeds = args.seeds
depth = args.depth
limit = args.limit
output = args.output


database = {}
processed = set()

seeds = args.seeds.split(',')

for seed in seeds:
    database[seed] = {}


def crawl(addresses, processed, database, limit):
    threadpool = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    blacklist = set()  # Define your blacklist here
    blacklist.add('9fLYPigGHXkTyyQvU9zzoT3RTAXJ4dfHjbkg6ik2fHKKxjprSrh') # FP
    blacklist.add('9f2h3D4MuAgG5RRYG4VZwXHPa37qQk5Ss82WdcsJvWXKd2edZo3') # pg
    futures = (threadpool.submit(getTransactions, address, processed, database, limit, blacklist) for address in addresses)
    print(f"Processed: {processed}, Database: {database}, Limit: {limit}, Blacklist: {blacklist}")

    for i, _ in enumerate(concurrent.futures.as_completed(futures)):
        print('%s Progress: %i/%i        ' % (info, i + 1, len(addresses)), end='\r')

try:
    for i in range(depth):
        print ('%s Crawling level %i' % (run, i + 1))
        database = ranker(database, top + 1)
        toBeProcessed = getNew(database, processed)
        print('%s %i addresses to crawl' % (info, len(toBeProcessed)))
        crawl(toBeProcessed, processed, database, limit)
except KeyboardInterrupt:
    pass

database = ranker(database, top)

jsoned = {'edges':[],'nodes':[]}
num = 1

num = 0
doneNodes = []
doneEdges = []
for node in database:
    x, y = genLocation()
    size = len(database[node])
    if size > 20:
        size = 20
    if node not in doneNodes:
        doneNodes.append(node)
        jsoned['nodes'].append({'label': node, 'x': x, 'y': y, 'id':'id=' + node, 'size':size})
    for childNode in database[node]:
        uniqueSize = database[node][childNode]
        if uniqueSize > 20:
            uniqueSize = 20
        x, y = genLocation()
        if childNode not in doneNodes:
            doneNodes.append(childNode)
            jsoned['nodes'].append({'label': childNode, 'x': x, 'y': y, 'id':'id=' + childNode, 'size': uniqueSize})
        if (node + ':' + childNode or childNode + ':' + node) not in doneEdges:
            doneEdges.extend([(node + ':' + childNode), (childNode + ':' + node)])
            jsoned['edges'].append({'source':'id=' + childNode, 'target':'id=' + node, 'id':num, "size":uniqueSize/3 if uniqueSize > 3 else uniqueSize})
        num += 1

print('%s Total wallets:%i' % (info, len(jsoned['nodes'])))
print('%s Total connections:%i' % (info, len(jsoned['edges'])))

render = json.dumps(jsoned).replace(' ', '').replace('\'', '"')

prepareGraph('%s.json' % seeds[0], render)
webbrowser.open('ErgoVision.html')

if output:
    data = exporter(output, jsoned)
    new = open(output, 'w+')
    new.write(data)
    new.close()

quit()
