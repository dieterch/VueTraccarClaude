import arrow
from dtraccar import traccar
import pandas as pd
import json
import time
import os
import sys
from pprint import pprint as pp
import warnings
warnings.filterwarnings("ignore")


T = traccar.Traccar()

if __name__ == '__main__':
    print(f'''
\033[H\033[J
*************************************************************
* Prefetch data from {T.cfg['url']} 
*************************************************************
''')

def _formatdate(d):
    return arrow.get(d).format('YYYY-MM-DDTHH:mm:ss') + 'Z'

print(f"read route data from file {T.cfg['url']}:")
t6 = time.time()
nroute = pd.read_hdf(T.cfg['prefetch_route'], "data").to_dict(orient='records')
t7 = time.time()
print(f"route : {len(nroute)} recs loaded from {T.cfg['prefetch_route']} in {t7-t6:.2f} seconds.")
last_id = nroute[-1]['id']; d = _formatdate(nroute[-1]['fixTime'])
print(f"lastid: {last_id}, lastdate: {d}")

print('-------------------------')
print(f"fetch route data, from lastdate until now from {T.cfg['url']}")
t2 = time.time()
route = T.getRouteData(startdate=d)
t3 = time.time()
print(f"route : {len(route)} recs fetched  in {t3-t2:.2f} seconds.")
print('-------------------------')
for r in route:
    print(f"route: {r['id']} {_formatdate(r['fixTime'])}")
print('-------------------------')
print('filter out the records that are already in the prefetch file')
newroute = [r for r in route if r['id'] > last_id]
for r in newroute:
    print(f"route: {r['id']} {_formatdate(r['fixTime'])}")
print('-------------------------')
# add the new records to the prefetch file
nroute.extend(newroute)

