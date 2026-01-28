import datetime
from math import sin, cos, sqrt, atan2, radians

# approximate radius of earth in km
R = 6373.0
false = False
true = True
null = None

def delta(pt1, pt2):
    lat1r = radians(pt1['latitude'])
    lon1r = radians(pt1['longitude'])
    lat2r = radians(pt2['latitude'])
    lon2r = radians(pt2['longitude'])

    dlon = lon2r - lon1r
    dlat = lat2r - lat1r

    a = sin(dlat / 2)**2 + cos(lat1r) * cos(lat2r) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    a = datetime.datetime.strptime(pt1['fixTime'][0:-9] + 'Z', "%Y-%m-%dT%H:%M:%SZ")
    b = datetime.datetime.strptime(pt2['fixTime'][0:-9] + 'Z', "%Y-%m-%dT%H:%M:%SZ")
    c = b - a #Zeitunterschied
    if (c.seconds > 0):
        dtime = c.seconds
    else:
        dtime = 1 #um Divisio durch 0 zu vermeiden

    result = {
        'distance': distance, # km
        'deltatime': c.seconds, # sec
        'avgspeed': distance / dtime * 3600 # km/h
    }

    return result


# pt1 = {
#     "id": 91720,
#     "attributes": {
#         "batteryLevel": 100,
#         "distance": 374.54,
#         "totalDistance": 976089.31,
#         "motion": true
#     },
#     "deviceId": 1,
#     "type": null,
#     "protocol": "osmand",
#     "serverTime": "2019-06-16T12:00:03.000+0000",
#     "deviceTime": "2019-06-16T12:00:02.000+0000",
#     "fixTime": "2019-06-16T12:00:02.000+0000",
#     "outdated": false,
#     "valid": true,
#     "latitude": 46.830593,
#     "longitude": 12.788402,
#     "altitude": 673.303,
#     "speed": 25.6976,
#     "course": 82.2656,
#     "address": null,
#     "accuracy": 10,
#     "network": null
# }
# pt2 = {
#     "id": 91803,
#     "attributes": {
#         "batteryLevel": 100,
#         "distance": 465.32,
#         "totalDistance": 1005416.3,
#         "motion": true
#     },
#     "deviceId": 1,
#     "type": null,
#     "protocol": "osmand",
#     "serverTime": "2019-06-16T12:24:29.000+0000",
#     "deviceTime": "2019-06-16T12:24:27.000+0000",
#     "fixTime": "2019-06-16T12:24:27.000+0000",
#     "outdated": false,
#     "valid": true,
#     "latitude": 46.744052,
#     "longitude": 13.117022,
#     "altitude": 608.233,
#     "speed": 36.8163,
#     "course": 53.0859,
#     "address": null,
#     "accuracy": 10,
#     "network": null
# }


# print("delta:", delta(pt1,pt2))