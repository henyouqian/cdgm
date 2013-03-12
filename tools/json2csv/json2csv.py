import os
import json
import csv
from collections import OrderedDict

def parse(key, value):
    if isinstance(value, list):
        print key
        with open('./output/'+key+'.csv', 'wb') as csvfile:
            writer = csv.writer(csvfile)
            
            #header
            row = value[0]
            writer.writerow([k for k in row])

            #rows
            for row in value:
                writer.writerow([row[k] for k in row])

    elif isinstance(value, dict):
        for k, v in value.iteritems():
            parse(k, v)

dir = os.getcwd()
for a, b, c in os.walk(dir):
    if (a==dir):
        for file in c:
            if file == 'json2csv.py':
                continue
            with open(file) as f:
                root = json.load(f, object_pairs_hook=OrderedDict)
                for k, v in root.iteritems():
                    parse(k, v)
