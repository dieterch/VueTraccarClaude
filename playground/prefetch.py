import arrow
import dtraccar
import pandas as pd
import json
import time
import os
from pprint import pprint as pp
import warnings
warnings.filterwarnings("ignore")


T = dtraccar.Traccar()


if __name__ == '__main__':
    print(f'''
\033[H\033[J
*************************************************************
* Prefetch data from {T.cfg['url']} 
*************************************************************
''')

print(f"fetch route data from {T.cfg['url']}")
t0 = time.time()
route = T.getRouteData()
t1 = time.time()
print(f"route : {len(route)} recs fetched  in {t1-t0:.2f} seconds.")
#pp(route[:10])

pd.DataFrame(route).to_hdf(T.cfg['prefetch_route'], "data", complevel=6)
t2 = time.time()
print(f"{T.cfg['prefetch_route']} written in {t2-t1:.2f} seconds.\n")

t3 = time.time()
nroute = pd.read_hdf(T.cfg['prefetch_route'], "data").to_dict(orient='records')
t4 = time.time()
print(f"route : {len(nroute)} recs loaded from {T.cfg['prefetch_route']} in {t4-t3:.2f} seconds.\n")

