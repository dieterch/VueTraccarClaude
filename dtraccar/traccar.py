import arrow
import json
import math
import os
import time
import requests
import itertools
import functools
from statistics import mean
import pprint
from pprint import pprint as pp, pformat as pf
import  dtraccar
import tomli as tml, tomli_w as tmlw
import googlemaps
import pandas as pd
import uuid
import warnings
import os
import re
import yaml
from pathlib import Path
from datetime import datetime
warnings.filterwarnings("ignore")

############################## Class Interface ##############################
   
class Traccar:
    def __init__(self, cfgfile='config.toml'):
        with open(cfgfile, mode="rb") as fp:
            self._cfg = tml.load(fp)
        self.gmaps = googlemaps.Client(key=self._cfg['mapsapikey'])
        self._newprefetch = False
            
    @property
    def cfg(self):
        return self._cfg
    
    @property
    def hash(self):
        return self._cfg['vuetraccarhash']
        
# -------------------
# api calls & caching
# -------------------            
    def getDevices(self):
        try:
            cfg = self._cfg
            r = requests.get(cfg['url'] + '/api/devices', auth=(
            cfg['user'], cfg['password']),
            timeout=100.000)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

    # Events
    def getEvents(self, **kwargs):
        try:
            parameters = self._par(['deviceId', 'from', 'to'], **kwargs)
            print(f"getEvent: {parameters}")
            cfg = self._cfg
            r = requests.get(
                cfg['url'] + '/api/reports/events', 
                auth=(cfg['user'], cfg['password']),
                headers={"Accept": "application/json; charset=utf-8"},
                params=parameters,
                timeout=100.000)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err) 

    # Positions
    def getPosition(self, cfg=None, id=None):
        try:
            cfg = self._cfghelp(cfg)
            r = requests.get(
                cfg['url'] + '/api/positions', 
                auth=(cfg['user'], cfg['password']), 
                headers={"Accept": "application/json; charset=utf-8"},
                params={'id': id },
                timeout=100.000)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err) 

    def _pfname(self, deviceId): # return the filename for the prefetch data
        name = self._cfg['prefetch_route'][:-4]
        extension = self._cfg['prefetch_route'][-4:]
        return f"{name}_deviceId{deviceId}{extension}"

    # prefetch route data
    def prefetchRouteData(self, deviceId=4):
        print(f"prefetching file {self._pfname(deviceId)} from {self._cfg['url']}")
        t0 = time.time()
        if hasattr(self, '_route'):
            del self._route
            
        # fetch all data since startdate, need a dict because 'from' and 'to' are reserved words
        args={
            'deviceId': deviceId,
            'from': self._formatdate(self._cfg['startdate']), 
            'to': self._formatdate(arrow.now())
        }        
        self._route = self._getRouteData(**args)
        t1 = time.time()
        _, self._standstill_periods = self._analyzeroute(self._route) # prefetch the standstill periods
        t2 = time.time()
        pd.DataFrame(self._route).to_hdf(self._pfname(deviceId), "data", complevel=6)
        pd.DataFrame(self._standstill_periods).to_hdf(self._pfname(deviceId), "standstill", complevel=6)        
        t3 = time.time()
        print(f"route prefetch : {len(self._route)} recs, store {t1-t0:.2f} sec, analyze {t2-t1:.2f}, total {t3-t0:.2f} sec.")
        return {"records" : len(self._route), "time": t1-t0}
    
    def del_prefetch(self, deviceId=4):
        if os.path.isfile(self._pfname(deviceId)):
            os.remove(self._pfname(deviceId))
            return f"file {self._pfname(deviceId)} deleted."
        else:
            return f"file {self._pfname(deviceId)} not found."
    
    def getRouteData(self, **kwargs):
        if hasattr(self, '_route'):
            if not os.path.isfile(self._pfname(kwargs['deviceId'])):
                print(f"prefetching  ... deleting 'self._route'")
                del self._route            
        if not hasattr(self, '_route'): # no else here, as the route may be deleted in the if clause
            # handle caching of route data
            if not os.path.isfile(self._pfname(kwargs['deviceId'])):
                self.prefetchRouteData() # self._route is created here as a side effect
            else:
                self._route = pd.read_hdf(self._pfname(kwargs['deviceId']), "data").to_dict(orient='records')
                self._standstill_periods = pd.read_hdf(self._pfname(kwargs['deviceId']), "standstill").to_dict(orient='records')
        # now we have a valid self._route 
        lastid = self._route[-1]['id']; lastdate = self._formatdate(self._route[-1]['fixTime'])

        # fetch only missing data, need a dict because 'from' and 'to' are reserved words
        args={
            'deviceId': kwargs['deviceId'],
            'from': lastdate, 
            #'to': self._formatdate(arrow.now().date()) # limit to today to enable caching => lead to 1 day delay while on trip
            'to': self._formatdate(arrow.now()) # immediate update ?
        }
        _newroute = self._getRouteData(**args)
        
        # filter out the records that are already in self._route
        newroute, newstandstill_periods = self._analyzeextendedroute([r for r in _newroute if r['id'] > lastid])
        # add the new records to the self._route
        self._route.extend(newroute)
        # add the new standstill periods to the self._standstill_periods
        self._standstill_periods.extend(newstandstill_periods)
        print(f"getRouteData: {len(newroute)} new records added to route, {len(self._route)} total records.")
        print(f"getRouteData: {len(newstandstill_periods)} new standstill periods added to standstill_periods, {len(self._standstill_periods)} total records.")
        # filter route for the requested time period
        route = [p for p in self._route if p['fixTime'] >= kwargs['from'] and p['fixTime'] <= kwargs['to']]
        return route
 
    # Routes
    @functools.cache
    def _getRouteData(self, **kwargs):
        t0 = time.time()
        parameters = self._par(['deviceId', 'from', 'to'], **kwargs)
        try:
            r = requests.get(
                self._cfg['url'] + '/api/reports/route', 
                auth=(self._cfg['user'], self._cfg['password']), 
                headers={"Accept": "application/json; charset=utf-8"},
                params=parameters,
                timeout=100.000)
            r.raise_for_status()
            # filter out very long distances
            route = [p for p in r.json() if p['attributes']['distance'] < 1000000.0]
            t1 = time.time()
            print(f"load route, device: {kwargs['deviceId']} from: {kwargs['from']}, to: {kwargs['to']}, {len(r.json()) - len(route)} records filtered. {t1-t0:.2f} seconds.")
            return route
        except requests.exceptions.HTTPError as err:
            raise SystemExit(err)

# -----------------
# complex functions
# -----------------

    # check if the geofence exit event is valid and makes sense
    def _exit_valid(self, dres, ev, i):
        if ((i > 1) and (arrow.get(ev['serverTime']) - arrow.get(dres[i-1]['serverTime'])).seconds < self._cfg['event_min_gap']):
                print(f"getTravels: skip   exit {i} ({ev['type']}),  {self._formatdate(arrow.get(dres[i]['serverTime']))}, too close to  {self._formatdate(arrow.get(dres[i-1]['serverTime']))}")
                return False
        return True
    
    def _return_valid(self, dres, ev, i):
        if ((i < len(dres)-1) and (arrow.get(dres[i+1]['serverTime']) - arrow.get(ev['serverTime'])).seconds < self._cfg['event_min_gap']):
                print(f"getTravels: skip return {i} ({ev['type']}),  {self._formatdate(arrow.get(dres[i]['serverTime']))}, too close to  {self._formatdate(arrow.get(dres[i+1]['serverTime']))}")
                return False
        return True
    
    
    def _translate(self, country):
        tl = {
            'Austria': 'Österreich',
            'Albania': 'Albanien',
            'Croatia': 'Kroatien',
            'France': 'Frankreich',
            'Germany': 'Deutschland',
            'Greece': 'Griechenland',
            'Italy': 'Italien',
            'Slovenia': 'Slowenien',
            'Switzerland': 'Schweiz'
        }
        if country in tl:
            return tl[country] 
        else: 
            return country
        
    # def _farestStandstill(self, stand_periods):
    #     home = self._cfg['home']
    #     # calculate the distance from home to each element of stand_periods and return the farest one
    #     for p in stand_periods:
    #         p['distance'] = self._distance(home, {'latitude': p['lat'], 'longitude': p['lng']})
    #         if p['address'].find('+') > 0:
    #             p['placeID'] = p['address'].split(' ')[0]
    #             p['address'] = ' '.join(p['address'].split(' ')[1:])
    #         else:
    #             p['placeID'] = ''

    #     stand_periods.sort(key=lambda x: x['distance'], reverse=True)
    #     pfar = stand_periods[0]
    #     return pfar
    
    def _farestStandstill(self, stand_periods):
        home = self._cfg['home']
        # handle empty list
        if not stand_periods:
            return {'distance': 0.0, 'address': '', 'lat': home.get('latitude'), 'lng': home.get('longitude'), 'placeID': ''}
        # calculate the distance from home to each element of stand_periods and return the farthest one
        for p in stand_periods:
            plat = p.get('lat', home.get('latitude'))
            plng = p.get('lng', home.get('longitude'))
            p['distance'] = self._distance(home, {'latitude': plat, 'longitude': plng})
            address = p.get('address', '')
            if '+' in address:
                p['placeID'] = address.split(' ')[0]
                p['address'] = ' '.join(address.split(' ')[1:])
            else:
                p['placeID'] = ''
        stand_periods.sort(key=lambda x: x['distance'], reverse=True)
        pfar = stand_periods[0]
        return pfar

    
    # def _store_travel(self, lto, lfrom, travels, **kwargs):
    #     # store travel if it is longer than cfg['mindays'] and shorter than cfg['maxdays']
    #     if ((lto - lfrom).days > self._cfg['mindays']) & ((lto - lfrom).days < self._cfg['maxdays']):
    #         args = {
    #             'from' : lfrom,
    #             'to' : lto
    #         }
    #         #print(f"store travel: {lfrom.format('YYYY-MM-DD')} ({(lto - lfrom).days} Tage)")
    #         stand_periods = self._filter_standstill_periods(self._standstill_periods, **args)
    #         far_sts = self._farestStandstill(stand_periods)
    #         if far_sts['distance'] > 1: # store only if the farest standstill is more than 1 km away from home
    #             travel_name = far_sts['address']
    #             #  print(f"Travel: '{travel_name}' detected.") 
    #             travels.append({
    #                 'title': f"{lfrom.date()} bis {lto.date()} {travel_name}",
    #                 'from': { 
    #                     'datetime': self._formatdate(lfrom),
    #                     #'event': lfrom_ev, # for debug
    #                     #'position': self.getPosition(cfg, lfrom_ev['positionId'])
    #                 },
    #                 'to': {
    #                     'datetime': self._formatdate(lto),
    #                     #'event': lto_ev, # for debug
    #                     #'position': self.getPosition(cfg, lto_ev['positionId']),
    #                     #'debug_events': [  # for debug
    #                     #    e for e in dres \
    #                     #    if ((arrow.get(e['serverTime']) > lfrom.shift(days=-2)) and 
    #                     #        (arrow.get(e['serverTime']) < lto.shift(days=2)) and 
    #                     #        (e['geofenceId'] == 1))
    #                     #]
    #                 },
    #                 'tage': (lto - lfrom).days, # duration in days
    #                 'device': kwargs['deviceId'] if 'deviceId' in kwargs else self._cfg['devid']
    #             })
    #     return travels

    #####################################################
    ## patch functions von ChatGTP. Start ###############
    #####################################################

    def _parse_date(self, value):
        """
        Accepts ISO strings like '2024-07-10' or '2024-07-10T12:00:00+02:00'
        Always returns an arrow object (timezone aware).
        """
        if isinstance(value, str):
            try:
                return arrow.get(value)
            except Exception as e:
                print(f"[parse_date] ERROR parsing '{value}': {e}")
                raise

        if isinstance(value, arrow.Arrow):
            return value

        raise TypeError(f"[parse_date] Unsupported type: {type(value)}")



    def _write_travel_patches(self):
        patch_file = Path("travels.yml")
        with patch_file.open("w") as f:
            yaml.dump(
                self._travel_patches,
                f,
                sort_keys=False,     # Reihenfolge beibehalten
                allow_unicode=True
            )

    def _register_travel_key(self, key: str):
        if key in self._travel_patches:
            return

        print(f"new travel key detected: '{key}' → adding empty patch entry")

        self._travel_patches[key] = {
            "title": None,
            "from": None,
            "to": None,
            "exclude": None,
        }

        self._write_travel_patches()


    def _clean_patches(self, data: dict):
        cleaned = {}

        for key, entry in data.items():
            if entry is None:
                continue
            
            # Entry sollte ein dict sein
            if isinstance(entry, dict):
                # nur Felder behalten, die einen tatsächlichen Wert besitzen
                filtered = {k: v for k, v in entry.items() if v not in (None, "", {})}

                cleaned[key] = filtered
            else:
                cleaned[key] = entry

        return cleaned

    def _load_travel_patches(self):
        patch_file = Path("travels.yml")

        if not patch_file.exists():
            print("travels.yml not found → starting with empty patches")
            return {}

        with patch_file.open() as f:
            data = yaml.safe_load(f) or {}

        print(f"loaded patches: {len(data)} entries from travels.yml")

        cleaned = self._clean_patches(data)
        if cleaned != data:
            print(f"cleaned patches: removed empty/null fields")

        return cleaned


    def _store_travel(self, lto, lfrom, travels, **kwargs):

        print(f"evaluating travel: {lfrom.format('YYYY-MM-DD HH:mm')} → {lto.format('YYYY-MM-DD HH:mm')}")

        if ((lto - lfrom).days > self._cfg['mindays']) & ((lto - lfrom).days < self._cfg['maxdays']):

            args = {'from': lfrom, 'to': lto}
            stand_periods = self._filter_standstill_periods(self._standstill_periods, **args)
            far_sts = self._farestStandstill(stand_periods)

            if not far_sts or far_sts.get('distance', 0) <= 1:
                return travels

            travel_key = far_sts['address']
            print(f"farthest standstill: {travel_key} (distance {far_sts.get('distance'):.1f} km)")

            self._register_travel_key(travel_key)           # stellt sicher, dass Key existiert
            patches = self._travel_patches.get(travel_key, {})
            print(f"patches found for '{travel_key}': {patches}")

            # Exclude?
            if patches.get("exclude", False):
                print(f"travel '{travel_key}' excluded by patch")
                return travels

            # Defaults
            from_dt = lfrom
            to_dt = lto

            # Apply overrides
            if "from" in patches:
                if patches["from"]:
                    print(f"patching FROM: {from_dt} → {patches['from']}")
                    from_dt = self._parse_date(patches["from"])

            if "to" in patches:
                if patches["to"]:
                    print(f"patching TO:   {to_dt} → {patches['to']}")
                    to_dt = self._parse_date(patches["to"])


            # Duration
            tage = max(0, (to_dt - from_dt).days)

            # Titel-Patching
            title = patches.get("title")
            if not title:
                print(f"auto-title generated for '{travel_key}'")
                title = f"{travel_key}"

            travel = {
                'title': title,
                'from': {'datetime': self._formatdate(from_dt)},
                'to':   {'datetime': self._formatdate(to_dt)},
                'tage': tage,
                'device': kwargs.get('deviceId', self._cfg['devid'])
            }

            travels.append(travel)

        return travels

    #####################################################
    ## patch functions von ChatGTP. Ende ###############
    #####################################################

    # def _store_travel(self, lto, lfrom, travels, **kwargs):
    #     # store travel if it is longer than cfg['mindays'] and shorter than cfg['maxdays']
    #     if ((lto - lfrom).days > self._cfg['mindays']) & ((lto - lfrom).days < self._cfg['maxdays']):
    #         args = {
    #             'from' : lfrom,
    #             'to' : lto
    #         }
    #         stand_periods = self._filter_standstill_periods(self._standstill_periods, **args)
    #         far_sts = self._farestStandstill(stand_periods)
    #         # if no standstill or too close to home, skip storing the travel
    #         if not far_sts or far_sts.get('distance', 0) <= 1:
    #             return travels
    #         travel_name = far_sts['address']
    #         travels.append({
    #             'title': f"{lfrom.date()} bis {lto.date()} {travel_name}",
    #             'from': { 
    #                 'datetime': self._formatdate(lfrom),
    #             },
    #             'to': {
    #                 'datetime': self._formatdate(lto),
    #             },
    #             'tage': (lto - lfrom).days, # duration in days
    #             'device': kwargs['deviceId'] if 'deviceId' in kwargs else self._cfg['devid']
    #         })
    #     return travels

    # Travels
    def getTravels(self, **kwargs):
        if not hasattr(self, '_route'):
            self.getRouteData(**kwargs)                 # get the route & standstill data
        dres = [rec for rec in self.getEvents(**kwargs) if (   # only geofence #1 (Stellplatz Fiecht), Enter und Exit Events
            (rec['type'] == "geofenceEnter" or rec['type'] == "geofenceExit") and rec['geofenceId'] == 1)]  # filter for geofence events
        self._travel_patches = self._load_travel_patches()
        travels = []
        intravel = False                                # state variable intravel

        for i, ev in enumerate(dres):                   # loop over events
            if ev['type'] == 'geofenceExit':            # Go for a trip
                if not self._exit_valid(dres, ev, i):
                    continue                            # skip events that are too close to the previous one
                lfrom = arrow.get(ev['serverTime'])     # exit from greofence for a trip detected, store in lfrom
                # lfrom_ev = ev                           # for debug
                intravel = True
            if intravel:
                if ev['type'] == 'geofenceEnter':       # come back from a trip
                    if not self._return_valid(dres, ev, i):
                            continue                    # skip events that are too close to the next one
                    lto = arrow.get(ev['serverTime'])   # return to gefence from a trip detected, store in lto
                    # lto_ev = ev                       # for debug
                    travels =  self._store_travel(lto, lfrom, travels, **kwargs) # evaluate and store the travel
                    intravel = False                    # back from travel
        # store the last travel if we are still in a travel
        if intravel:
            # lto = arrow.get(self._route[-1]['fixTime']) # if we are still in a travel, set the end to last GPS point of previous day.
            lto = arrow.now() # if we are still in a travel, set the end to now.
            print(f"getTravels: still in travel, exit: {lfrom.format('YYYY-MM-DD HH:mm:ss')}, last update: {lto.format('YYYY-MM-DD HH:mm:ss')}") # for debug
            travels =  self._store_travel(lto, lfrom, travels, **kwargs)
        return travels

    # return data to plot the route
    def plot(self, **kwargs):
        data = self.getRouteData(**kwargs)              # get the portion of the route for the requested period
        center, bounds = self._center_and_bounds(data)  # calculate the center and bounds of the route
        stand_periods = self._filter_standstill_periods(self._standstill_periods, **kwargs) # filter for the requested period
        total_dist = data[-1]['attributes']['totalDistance'] - data[0]['attributes']['totalDistance'] # total distance
        print(f"total distance: {total_dist:.0f} km = {data[-1]['attributes']['totalDistance']} - {data[0]['attributes']['totalDistance']}")                            # for debug
        markers = self._clean_stand_periods(stand_periods)                      # clean the standstill periods
        print(f"centerlat: {center['lat']:.1f}, centerlng: {center['lng']:.1f}") # for debug
        plotdata = [{"lat": d['latitude'], "lng": d['longitude']} for d in data] # prepare the data for the plot
        #pp(markers)        
        #pp(stand_periods[:5])
        return {
            "bounds": bounds,
            "center": center,
            "zoom": self._zoom(bounds),
            "distance": f"{total_dist:.0f} km",
            "markers": markers,
            "plotdata": plotdata
        }

    # return data to plot the route              
    def kml(self, **kwargs):
        cfg = self._cfg
        parameters = self._par(['name','maxpoints'], **kwargs)
        data = self.getRouteData(**kwargs)
        kmldata = dtraccar.tokml(data)
        file_name = kwargs['name'] + '.kml' if 'name' in kwargs else 'route.kml'
        file_path = os.getcwd() + "/dist/static/"
        full_path = file_path + file_name
        dtraccar.writeKML(cfg, parameters, full_path, kmldata)
        return file_name, full_path
    
    def getDocument(self, key, **kwargs):
        file_path = f"documents/{key}.rst"
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                content = file.read()
                return {'md': content}
        else:
            return {'md': f"Bitte 'Bearbeiten' verwenden um Inhalt zu erstellen. "}


    def saveDocument(self, key, **kwargs):
        file_path = f"documents/{key}.rst"
        doc = kwargs['md']
        regex = r"^.*\[(.*)\]\((.*)\)"
        subst = "<a href=\"\\2\" target=\"_blank\">\\1</a>"
        newdoc = re.sub(regex, subst, doc, 0, re.MULTILINE)
        print(newdoc)
        with open(file_path, 'w') as file:
            file.write(newdoc)
            return {'md': newdoc}  
        
# ----------------------
# local helper functions
# ---------------------- 

    def _par(self, parameters, **kwargs): # limit parameters to the api-defined ones (for requests)
        return {a: kwargs[a] for a in kwargs if a in parameters}
    
    def _formatdate(self, d):
        return arrow.get(d).format('YYYY-MM-DDTHH:mm:ss') + 'Z'

    def _center_and_bounds(self, route):
        t0 = time.time()
        south = min([d['latitude'] for d in route])
        north = max([d['latitude'] for d in route])
        east = min([d['longitude'] for d in route])
        west = max([d['longitude'] for d in route])
        center = {
            'lat': (south + north) / 2,
            'lng': (east + west) / 2
        }
        bounds = {
            'nw': {'latitude': north, 'longitude': west},
            'ne': {'latitude': north, 'longitude': east},
            'se': {'latitude': south, 'longitude': east},
            'sw': {'latitude': south, 'longitude': west}
        }
        t1 = time.time()
        print(f"calculate route center and bounds: {t1-t0:.2f} seconds.")
        return center, bounds

    def _zoom(self,bounds):
        extx = self._distance(bounds['nw'], bounds['ne'])
        exty = self._distance(bounds['nw'], bounds['sw'])
        ext = math.sqrt(extx**2 + exty**2)
        #zoom = 46.527*((ext+150)**-0.288)
        zoom = 35.936*((ext+150)**-0.243)
        print(f"zoom: ext:{ext:.1f},(x:{extx:.1f} y:{exty:.1f}) zoom: {zoom}")
        return zoom
        
    def _clean_stand_periods(self, stand_periods): # combine stand periods that are close to each other
        for (i,j) in itertools.combinations(range(len(stand_periods)), 2):
            latdiff = stand_periods[i]['lat'] - stand_periods[j]['lat']
            lngdiff = stand_periods[i]['lng'] - stand_periods[j]['lng']
            diff = math.sqrt(latdiff**2 + lngdiff**2)
            if  diff < 0.005:
                if (stand_periods[i]['period'] > 0 and stand_periods[j]['period'] > 0):
                    #print(f"combine {i}-{j}, distance: {diff:.4f}")
                    stand_periods[i]['period'] += stand_periods[j]['period']
                    stand_periods[j]['period'] = 0
        sp = [d for d in stand_periods if d['period'] > 0]
        return sp

    def _filter_standstill_periods(self, stand_periods, **kwargs):
        return [p for p in stand_periods if
                ((arrow.get(p['von']) >= arrow.get(kwargs['from']).shift(hours=-8)) and
                 (arrow.get(p['bis']) <= arrow.get(kwargs['to']).shift(hours=8)))]
    
    def _timediff(self, pt1, pt2): # return time difference between 2 pts in seconds
        return (arrow.get(pt2['fixTime']) - arrow.get(pt1['fixTime'])).total_seconds()

    def _distance(self, pt1, pt2):
        R = 6373.0 # approximate radius of earth in km
        lat1r = math.radians(pt1['latitude'])  # convert latitude of pt1 to radians
        lon1r = math.radians(pt1['longitude']) # convert longitude pt1 to radians
        lat2r = math.radians(pt2['latitude'])  # convert latitude of pt2 to radians
        lon2r = math.radians(pt2['longitude']) # convert longitude pt2 to radians
        dlon = lon2r - lon1r
        dlat = lat2r - lat1r
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        return distance # in km
    
    def _analyzeextendedroute(self, extendedroute): # analyze extended route
        # take the last distance from the previous route and add it to route[i]['attributes']['totalDistance']
        extended_standStill_periods = []
        if len(extendedroute) > 0:
            last_total_distance = self._route[-1]['attributes']['totalDistance']
            extendedroute, extended_standStill_periods = self._analyzeroute(extendedroute)
            for position in extendedroute:
                position['attributes']['totalDistance'] += last_total_distance
            # calculate the standstill periods
        return extendedroute, extended_standStill_periods
        
    # Berechne die Länger der Reise, die Standzeiten und deren Adressen
    def _analyzeroute(self, route):
        route[0]['attributes']['totalDistance'] = 0.0 # reuse this field, reset the counter.
        total_dist = 0.0 # total distance
        stand_periods = [] # list of standstill periods
        sample_period = [] # list of samples within a standstill periods (a potential stop)
        stop = {} # last stop
        start = {} # last start
        standstill = False # flag for standstill
        for i in range(len(route)-1): # loop over all positions
            d = self._distance(route[i],route[i+1]) # distance between two positions
            total_dist += d # integrate distance
            route[i]['attributes']['totalDistance'] = total_dist # store the accumulated distance
            if d < 0.1: # if distance is less than 100m, we assume the vehicle is standing still
                if not standstill: # if we are not already in a standstill period
                    standstill = True # set the flag
                    stop = route[i] # store the stop position
                sample_period.append( # store the position in the sample period
                    {'lat': route[i]['latitude'],
                     'lng': route[i]['longitude']})
            else: # if the vehicle is moving
                if standstill: # if we are in a standstill period
                    standstill = False # reset the flag
                    start = route[i] # store the start position
                    period = self._timediff(stop, start) # calculate the period
                    if period > (self._cfg['standperiod']*3600.0): # if the period is longer than x hours
                        plat = mean([p['lat'] for p in sample_period]) # calculate the mean latitude
                        plng = mean([p['lng'] for p in sample_period]) # calculate the mean longitude
                        address = self.gmaps.reverse_geocode((plat, plng)) # get the address from google api
                        stand_periods.append( # append the standstill period (This data is used for infowindows in the plot function)
                        {   'von': ' '.join(stop['fixTime'].split('T'))[:16], # 'von': '2021-07-01 12:00',
                            'bis': ' '.join(start['fixTime'].split('T'))[:16], # 'bis': '2021-07-01 12:00',
                            'period': round(period//360.0/10.0),
                            'country': address[0]['address_components'][-2]['long_name'], # 'country': 'Austria',
                            'address': address[0]['formatted_address'], # 'address': 'Fiecht 1, 6235 Reith im Alpbachtal, Austria
                            'lat': plat,
                            'lng': plng,
                            'key': f"marker{str(plat)[:7]}{str(plng)[:7]}".replace('.','').replace('-','M'), # key
                            'infowindow': False # flag used to show/hide infowindow in the plot function
                        })
                    sample_period = [] # empty the sample period indepent if the period was long enough or not
        route[-1]['attributes']['totalDistance'] = total_dist # store the accumulated distance aso for the last position in route
        return route, stand_periods 
        
if __name__ == '__main__':
    print('Please do not call this module directly. Use the app.py instead.')