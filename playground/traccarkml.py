#!/usr/bin/env python
# coding: utf-8

'''
This Script loads GPS Data from a traccar server and stores this Data as KML and CSV file
it condenses the amount of data by
	- taking only point with a minimum distance (parameter)
	- talking a point independent from distance if a certain time intervall has passed (parameter)
'''

import json
import requests
import pprint
import os
import re
import simplekml
from simplekml import Kml, ListItemType, Color, Style
from playground.difference import delta
#import console
import pickle
from optparse import OptionParser
import sys

# Input Parameter

cfg = {
    'CommonColor': Color.blue,
    # User credentials, traccar server
    'user': 'dieter.chvatal@gmail.com',
    'password': '81aNUlLY',
    # File Name
}


def getData(par):
    print("1. Traccar Device {0:s} von {1:s} bis {2:s} von {3:s} laden ...".format(
        par.device, par.startdate, par.enddate, par.url))
    payload = {'deviceId': par.device,
               'from': par.startdate, 'to': par.enddate}
    response = requests.get(par.url + '/api/reports/route', auth=(
        cfg['user'], cfg['password']), params=payload, timeout=100.000)
    # print(response.url)
    return json.loads(response.content)


def dofilter(par, data):
    print("2. Filter > {0:2.1f} km Abstand. Mindestens alle {1:1.0f} h ein Wegpunkt ... ".format(
        float(par.distfilter), float(par.secfilter) / 3600))
    first = 0
    last = len(data)
    kml = []
    i = 0
    for i in range(last):
        # berechne Zeit und Distanz Differenzen der beiden Datensaetze
        d = delta(data[first], data[i])
        if (((i + 1) % 1000) == 0):
            print('|', end="")

        # das Fahrzeug ist mehr als distfilter km  gefahren oder mehr als secfilter gestanden
        if ((d['distance'] > float(par.distfilter)) or (d['deltatime'] > float(par.secfilter))):
            p = {
                "latitude": data[i]['latitude'],
                "longitude": data[i]['longitude'],
                "altitude": data[i]['altitude'],
            }
            kml.append(p)
            first = i  # merke diesen Datenpunkt als neuen Anfangspunkt

    print(' ', i + 1, 'Datensätze verarbeitet ...')
    return kml


def writeKML(par, kml):
    print("3. Export to KML File {0:s} ... ".format(par.name + '.kml'))
    kmlxml = Kml(name=par.name, open=1)  # Simple KML object
    fol = kmlxml.newfolder(name="LineStrings")  # Folder
    lkml = len(kml)
    lchunk = int(par.maxpoints)
    nol = (lkml // lchunk) + 1  # in chunks schreiben
    points = lkml
    for li in range(nol):
        lcoords = []
        lpoints = min(points, lchunk)
        for i in range(lpoints):
            index = i + li*lchunk
            co = (kml[index]['longitude'], kml[index]
                  ['latitude'], kml[index]['altitude'])
            lcoords.append(co)
        # Waypoints Linestring item

        linestring = fol.newlinestring(name="Route_"+str(li))
        #linestring = kmlxml.newlinestring(name="Route"+str(li))
        linestring.altitudemode = simplekml.AltitudeMode.clamptoground
        linestring.tessellate = 1
        linestring.linestyle.color = cfg['CommonColor']
        linestring.linestyle.width = 4
        linestring.coords = lcoords
        points = points - int(par.maxpoints)

    sharedstyle = Style()
    sharedstyle.labelstyle.color = cfg['CommonColor']
    sharedstyle.labelstyle.scale = 1  # Text size
    sharedstyle.iconstyle.color = cfg['CommonColor']
    sharedstyle.iconstyle.scale = 1  # Icon size
    sharedstyle.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/pink-stars.png'
    # Save the KML
    filename = os.path.split(__file__)[0] + '/' + par.name + '.kml'
    kmlxml.save(filename)


def main():
    parser = OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("-n", "--name", action="store", dest="name",
                      default="2020_Ledrosee_Dieter_Susi", help="KML File Name")
    parser.add_option("-u", "--url", action="store", dest="url",
                      default="https://tracking.seriousfamilybusiness.net", help="Traccar Server URL")
    parser.add_option("-d", "--device", action="store",
                      dest="device", default="2", help="Tracker ID")
    parser.add_option("-b", "--start_date", action="store", dest="startdate",
                      default="2020-07-25T00:00:00Z", help="Beginn Zeitpunkt ISO z.b. 2019-06-16T00:00:00Z")
    parser.add_option("-e", "--end_date", action="store", dest="enddate",
                      default="2020-07-31T23:59:00Z", help="End Zeitpunkt ISO z.b. 2019-06-17T00:00:00Z")
    parser.add_option("-f", "--filter_dist", action="store", dest="distfilter",
                      default="0.05", help="Filtere Punkte < xx.x km Abstand")
    parser.add_option("-z", "--filter_sec", action="store", dest="secfilter",
                      default="14400", help="Schreibe Punkte mindestens alle xx sec")
    parser.add_option("-m", "--maxpoints", action="store", dest="maxpoints",
                      default="2500", help="maximale Anzahl von Punkten pro KML Linestring")
    (options, args) = parser.parse_args()

    # print(options)
    # print(args)

    # sys.exit(0)

    data = getData(options)  # lese Daten über Traccar API
    kmldata = dofilter(options, data)  # Daten filtern
    writeKML(options, kmldata)  # als KML ausgeben
    # if len(args) != 1:
    #    parser.error("wrong number of arguments")


if __name__ == '__main__':
    main()
