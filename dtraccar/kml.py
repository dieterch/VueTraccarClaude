import os
import random
import simplekml
from simplekml import Kml, ListItemType, Color, Style

kml_colors = [
    Color.red,
    Color.lightblue,
    Color.lightpink,
    Color.lightgreen,
    Color.yellow,
    Color.orange,
    Color.magenta
]


def tokml(data):
    kml = [{
        "latitude": d['latitude'],
        "longitude": d['longitude'],
        "altitude": d['altitude'],
    } for d in data]
    return kml


def writeKML(cfg, par, filename, kml):
    CommonColor = kml_colors[random.randint(0, len(kml_colors)-1)]
    kmlxml = Kml(name=par['name'], open=1)  # Simple KML object
    fol = kmlxml.newfolder(name="LineStrings")  # Folder
    lkml = len(kml)
    lchunk = int(par['maxpoints'])
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
        # linestring = kmlxml.newlinestring(name="Route"+str(li))
        linestring.altitudemode = simplekml.AltitudeMode.clamptoground
        linestring.tessellate = 1
        linestring.linestyle.color = CommonColor
        linestring.linestyle.width = 4
        linestring.coords = lcoords
        points = points - int(par['maxpoints'])

    sharedstyle = Style()
    sharedstyle.labelstyle.color = CommonColor
    sharedstyle.labelstyle.scale = 1  # Text size
    sharedstyle.iconstyle.color = CommonColor
    sharedstyle.iconstyle.scale = 1  # Icon size
    sharedstyle.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/paddle/pink-stars.png'
    # Save the KML
    #filename = os.path.split(__file__)[0] + '/' + par['name'] + '.kml'
    kmlxml.save(filename)
