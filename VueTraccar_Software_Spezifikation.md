# VueTraccar - Software Spezifikation

## 🎯 Projekt-Übersicht

**VueTraccar** ist eine Webapplikation zur Dokumentation und Visualisierung von Wohnmobilreisen. Sie holt GPS-Daten von einem Traccar-Server, analysiert diese und leitet daraus Reisen und Stillstandsorte ab, die dann auf einer interaktiven Google Map visualisiert werden.

### Hauptfunktionen
- GPS-Datenimport von Traccar Server
- Automatische Erkennung von Reisen und Stillstandsorten
- Interaktive Kartendarstellung mit Google Maps
- Dokumentation von Reiseorten (Tagebuch-Funktion)
- KML-Export für externe Verwendung

---

## 🏗️ Technologie-Stack

### Backend
- **Framework**: Quart (async Python Web Framework)
- **Web Server**: Uvicorn
- **Python Version**: 3.x
- **Hauptabhängigkeiten**:
  - `quart==0.19.4` - Async Web Framework
  - `quart-cors==0.7.0` - CORS Support
  - `requests==2.31.0` - HTTP Client für Traccar API
  - `googlemaps==4.10.0` - Reverse Geocoding
  - `pandas==2.2.1` - Datenverarbeitung
  - `tables==3.9.2` - HDF5 Storage
  - `arrow==1.3.0` - Datum/Zeit-Handling
  - `PyYAML==6.0.2` - YAML-Konfiguration
  - `simplekml==1.3.6` - KML-Generierung

### Frontend
- **Framework**: Vue 3
- **UI Library**: Vuetify 3
- **Build Tool**: Vite
- **Hauptabhängigkeiten**:
  - `vue@^3.3.0`
  - `vuetify@^3.0.0`
  - `vue3-google-map@^0.19.0` - Google Maps Integration
  - `axios@^1.6.7` - HTTP Client
  - `md-editor-v3@^4.11.3` - Markdown Editor
  - `vue-loading-overlay@^6.0.4` - Loading States

### Datenbank/Storage
- **HDF5** (via pytables) - Caching von GPS-Routen
- **Lokale `.rst` Dateien** - Standort-Dokumentation
- **YAML** - Reisekonfiguration

---

## 📐 Architektur

### Systemarchitektur

```
┌─────────────────────────────────────────────────────────────┐
│                      Browser (Client)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │         Vue 3 + Vuetify Frontend                       │ │
│  │  • App.vue (Main Component)                            │ │
│  │  • GMap.vue (Google Maps Integration)                  │ │
│  │  • MDDialog.vue (Dokumenten-Anzeige)                   │ │
│  │  • MDEditorDialog.vue (Dokumenten-Bearbeitung)         │ │
│  │  • AppBar.vue, DateDialog.vue, etc.                    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/JSON
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Quart Backend (app.py)                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  API Endpoints:                                        │ │
│  │  • /devices - Geräte auflisten                         │ │
│  │  • /route - GPS-Route abrufen                          │ │
│  │  • /events - Events abrufen                            │ │
│  │  • /travels - Reisen auflisten                         │ │
│  │  • /plotmaps - Kartendaten für Visualisierung          │ │
│  │  • /download.kml - KML Export                          │ │
│  │  • /document/<key> - Dokumenten CRUD                   │ │
│  │  • /prefetchroute - Daten vorladen                     │ │
│  │  • /delprefetch - Cache löschen                        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│         Business Logic (dtraccar/traccar.py)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Traccar Klasse:                                       │ │
│  │  • getDevices() - Traccar API Integration              │ │
│  │  • getRouteData() - GPS-Daten mit Caching              │ │
│  │  • _analyzeroute() - Reise/Stillstand-Erkennung        │ │
│  │  • plot() - Kartendaten aufbereiten                    │ │
│  │  • getTravels() - Reisen aus travels.yml               │ │
│  │  • getDocument/saveDocument - Dokumenten-Verwaltung    │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
    ┌──────────────────┐    ┌──────────────────────┐
    │  Traccar Server  │    │  Google Maps API     │
    │  GPS Data Source │    │  Reverse Geocoding   │
    └──────────────────┘    └──────────────────────┘
                │
                ▼
    ┌──────────────────┐    ┌──────────────────────┐
    │  HDF5 Cache      │    │  documents/*.rst     │
    │  Route Data      │    │  Standort-Docs       │
    └──────────────────┘    └──────────────────────┘
```

### Datenfluss

1. **Initiale Datenabfrage**:
   ```
   Frontend → /travels → Backend lädt travels.yml
   Frontend wählt Reise → /plotmaps
   Backend → Traccar API (mit Caching) → GPS-Daten
   Backend analysiert Route → Stillstände
   Backend → Google Maps API → Adressen
   Backend → Frontend (Polygone, Marker, Bounds)
   ```

2. **Dokumenten-Workflow**:
   ```
   User klickt Marker → /document/<key> GET
   Backend lädt documents/<key>.rst
   Frontend zeigt Markdown
   User editiert → /document/<key> POST
   Backend speichert .rst Datei
   ```

---

## 📊 Datenmodelle

### GPS Route Position
```python
{
    "id": int,                    # Traccar Position ID
    "deviceId": int,              # Gerät ID
    "fixTime": "2023-05-15T10:30:00Z",
    "latitude": 47.2692,
    "longitude": 11.4041,
    "altitude": 574.5,
    "speed": 45.2,                # km/h
    "course": 180,                # Grad
    "attributes": {
        "totalDistance": 1234.5,  # Akkumulierte Distanz in km
        "batteryLevel": 85,
        ...
    }
}
```

### Stillstandsperiode (Standstill Period)
```python
{
    "von": "2023-05-15 10:00",    # Start-Zeitpunkt
    "bis": "2023-05-17 14:00",    # End-Zeitpunkt
    "period": 52,                 # Dauer in Stunden
    "country": "Austria",
    "address": "Fiecht 1, 6235 Reith im Alpbachtal, Austria",
    "lat": 47.2692,
    "lng": 11.4041,
    "key": "marker472692114041",  # Eindeutiger Schlüssel für Dokumente
    "infowindow": false           # UI State
}
```

### Reise (Travel)
```python
{
    "title": "2024 Spanien und Portugal Rundreise",
    "from": {
        "datetime": "2024-03-01T00:00:00Z",
        "address": "Start-Adresse"
    },
    "to": {
        "datetime": "2024-04-15T23:59:59Z",
        "address": "End-Adresse"
    },
    "distance": 3456.7,           # Gesamtdistanz in km
    "exclude": false
}
```

### Plot/Map Daten
```python
{
    "bounds": {
        "nw": {"latitude": 48.5, "longitude": 10.2},
        "ne": {"latitude": 48.5, "longitude": 12.8},
        "se": {"latitude": 46.8, "longitude": 12.8},
        "sw": {"latitude": 46.8, "longitude": 10.2}
    },
    "center": {"lat": 47.65, "lng": 11.5},
    "zoom": 8.5,
    "distance": "1234 km",
    "markers": [                  # Standstill Periods als Marker
        {...},                    # siehe Stillstandsperiode
    ],
    "plotdata": [                 # Polygone für Route
        {"lat": 47.2692, "lng": 11.4041},
        {"lat": 47.2693, "lng": 11.4042},
        ...
    ]
}
```

---

## 🔧 Kernalgorithmen

### 1. Stillstands-Erkennung (`_analyzeroute()`)

**Zweck**: GPS-Route analysieren und Stillstände identifizieren

**Logik**:
```python
def _analyzeroute(route):
    standstill = False
    stop = {}
    sample_period = []
    stand_periods = []
    
    for i in range(len(route)-1):
        distance = haversine_distance(route[i], route[i+1])
        
        if distance < 0.1:  # < 100m → Stillstand
            if not standstill:
                standstill = True
                stop = route[i]
            sample_period.append(route[i].position)
        else:  # Bewegung
            if standstill:
                standstill = False
                start = route[i]
                period_hours = time_diff(stop, start)
                
                if period_hours > CONFIG.standperiod:  # z.B. > 8h
                    avg_position = average(sample_period)
                    address = google_maps.reverse_geocode(avg_position)
                    stand_periods.append({
                        'von': stop.fixTime,
                        'bis': start.fixTime,
                        'period': period_hours,
                        'address': address,
                        'lat': avg_position.lat,
                        'lng': avg_position.lng,
                        'key': generate_key(avg_position)
                    })
                sample_period = []
    
    return route, stand_periods
```

**Konfigurierbarer Parameter**:
- `standperiod` in `config.toml` (Standard: 8 Stunden)

### 2. Reisen-Ableitung (`getTravels()`)

**Zweck**: Aus Stillstandsorten komplette Reisen ableiten

**Logik**:
```python
def getTravels(deviceId, from, to):
    # 1. Hole alle Standstills im Zeitraum
    standstills = get_standstill_periods(deviceId, from, to)
    
    # 2. Lade travels.yml Konfiguration
    travel_config = load_yaml('travels.yml')
    
    # 3. Gruppiere Standstills zu Reisen
    travels = []
    for config_key, config in travel_config.items():
        matching_standstills = [
            s for s in standstills 
            if s.address.contains(config_key)
        ]
        
        if matching_standstills:
            travel = {
                'title': config.title or 'Unbenannte Reise',
                'from': min(s.von for s in matching_standstills),
                'to': max(s.bis for s in matching_standstills),
                'distance': calculate_total_distance(matching_standstills)
            }
            travels.append(travel)
    
    return travels
```

### 3. Route-Caching mit HDF5

**Zweck**: Performance-Optimierung durch intelligentes Caching

**Strategie**:
```python
def getRouteData(deviceId, from, to):
    cache_file = f"prefetch_route_deviceId{deviceId}.h5"
    
    # 1. Lade gecachte Daten falls vorhanden
    if cache_exists(cache_file):
        cached_route = load_from_hdf5(cache_file, "data")
        cached_standstills = load_from_hdf5(cache_file, "standstill")
        last_date = cached_route[-1].fixTime
    else:
        # Initial fetch all data
        cached_route = fetch_from_traccar(deviceId, CONFIG.startdate, now())
        cached_standstills = analyze_route(cached_route)
        save_to_hdf5(cache_file, cached_route, cached_standstills)
        last_date = cached_route[-1].fixTime
    
    # 2. Hole nur neue Daten
    new_data = fetch_from_traccar(deviceId, last_date, now())
    new_standstills = analyze_extended_route(new_data)
    
    # 3. Merge und update Cache
    full_route = cached_route + new_data
    full_standstills = cached_standstills + new_standstills
    
    # 4. Filter für angefragte Zeitspanne
    filtered_route = [p for p in full_route if from <= p.fixTime <= to]
    
    return filtered_route
```

---

## 🎨 Frontend-Komponenten

### App.vue (Hauptkomponente)
**Verantwortlichkeit**: Root-Container, Authentication, Routing

**State**:
- `authenticated`: Boolean für Login-Status (aktuell hardcoded auf `true`)

**Child Components**:
- `AppBar` - Top Navigation
- `GMap` - Kartendarstellung
- `DebugDialog` - Debug-Ansichten

### GMap.vue (Kartenkomponente)
**Verantwortlichkeit**: Google Maps Integration, Marker, Polylines

**Props/State**:
- `polygone`: Array von lat/lng für Route
- `center`: Map-Zentrum
- `zoom`: Zoom-Level
- `locations`: Standstill-Marker
- `togglemarkers`, `togglepath`: Sichtbarkeits-Flags

**Features**:
- MarkerCluster für Performance
- InfoWindow mit Standort-Details
- Click-Handler für Dokumenten-Dialog

### MDDialog.vue (Dokumenten-Anzeige)
**Verantwortlichkeit**: Markdown-Preview von Standort-Dokumenten

**Props**:
- `content`: Markdown-Text
- `dialog`: Sichtbarkeit
- `file`: Dokumenten-Key

**Features**:
- Markdown-Rendering mit `md-editor-v3`
- "Bearbeiten" Button → öffnet `MDEditorDialog`

### MDEditorDialog.vue (Dokumenten-Editor)
**Verantwortlichkeit**: Markdown-Bearbeitung

**Props**:
- `content`: Zu bearbeitender Text
- `dialog`: Sichtbarkeit
- `file`: Dokumenten-Key

**Events**:
- `saveContent`: Emitted beim Speichern

### app.js (State Management)
**Verantwortlichkeit**: Globaler Application State

**Exports**:
```javascript
// Geräte & Datum
device: Ref<{name: string, id: number}>
startdate: Ref<Date>
stopdate: Ref<Date>

// Daten
travels: Ref<Travel[]>
travel: Ref<Travel>
route: Ref<Route>
events: Ref<Event[]>

// Map State
polygone: Ref<LatLng[]>
center: Ref<LatLng>
zoom: Ref<number>
locations: Ref<Standstill[]>

// UI Toggles
togglemap: Ref<boolean>
togglemarkers: Ref<boolean>
togglepath: Ref<boolean>

// API Functions
getTravels(): Promise<void>
getRoute(): Promise<void>
renderMap(): Promise<void>
getMDDocument(key): Promise<string>
saveMDDocument(key, doc): Promise<string>
downloadkml(): Promise<void>
```

---

## 🔌 API-Endpunkte

### GET /devices
**Zweck**: Liste verfügbarer GPS-Geräte

**Response**:
```json
[
  {
    "id": 4,
    "name": "WMB Tk106",
    "uniqueId": "123456789",
    "status": "online",
    ...
  }
]
```

### POST /route
**Zweck**: GPS-Route für Zeitraum abrufen

**Request**:
```json
{
  "deviceId": 4,
  "from": "2024-03-01T00:00:00Z",
  "to": "2024-04-15T23:59:59Z"
}
```

**Response**: Array von Position-Objekten (siehe Datenmodell)

### POST /travels
**Zweck**: Reisen basierend auf Standstills

**Request**:
```json
{
  "deviceId": 4,
  "from": "2019-03-01T00:00:00Z",
  "to": "2025-01-28T23:59:59Z"
}
```

**Response**:
```json
[
  {
    "title": "2024 Spanien und Portugal Rundreise",
    "from": { "datetime": "...", "address": "..." },
    "to": { "datetime": "...", "address": "..." },
    "distance": 3456.7
  }
]
```

### POST /plotmaps
**Zweck**: Aufbereitete Kartendaten für Frontend

**Request**: Wie `/route`

**Response**: Siehe Plot/Map Daten Modell

### GET /document/{key}
**Zweck**: Dokumenten-Inhalt abrufen

**Response**:
```json
{
  "md": "Als wir am Campingplatz [Norina](https://...) ankamen..."
}
```

### POST /document/{key}
**Zweck**: Dokumenten-Inhalt speichern

**Request**:
```json
{
  "md": "Neuer Markdown-Inhalt..."
}
```

**Response**: Wie GET

### POST /download.kml
**Zweck**: KML-Datei generieren und downloaden

**Request**: Wie `/route` + `name` Parameter

**Response**: Binary KML File

### GET /prefetchroute
**Zweck**: Alle Daten vorab laden und cachen

**Query Params**: `deviceId` (optional, default: 4)

**Response**:
```json
{
  "records": 156789,
  "time": 12.45
}
```

### GET /delprefetch
**Zweck**: Cache-Datei löschen

**Response**: Status-String

---

## 📁 Dateistruktur

```
VueTraccar-main/
├── app.py                      # Quart Backend Entry Point
├── requirements.txt            # Python Dependencies
├── config.toml                 # Konfiguration (nicht im Repo)
├── travels.yml                 # Reise-Definitionen
├── prepare.py                  # Setup-Skript
├── start.sh                    # Start-Skript
│
├── dtraccar/                   # Backend Business Logic
│   ├── __init__.py
│   ├── traccar.py              # Hauptklasse: Traccar-API, Analyse
│   └── kml.py                  # KML-Generierung
│
├── documents/                  # Standort-Dokumentation (.rst)
│   ├── marker438833129591.rst
│   ├── marker472692114041.rst
│   └── ...
│
├── playground/                 # Experimentelle Skripte
│   ├── cleanperiods.py
│   ├── difference.py
│   └── ...
│
├── frontend/                   # Vue 3 Frontend
│   ├── package.json
│   ├── vite.config.mjs
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.js             # Vue Entry Point
│   │   ├── App.vue             # Root Component
│   │   ├── app.js              # State Management
│   │   ├── tools.js            # Helper Functions
│   │   │
│   │   ├── components/
│   │   │   ├── AppBar.vue
│   │   │   ├── GMap.vue
│   │   │   ├── MDDialog.vue
│   │   │   ├── MDEditorDialog.vue
│   │   │   ├── DateDialog.vue
│   │   │   ├── DebugDialog.vue
│   │   │   └── SideBar.vue
│   │   │
│   │   ├── plugins/
│   │   │   ├── index.js
│   │   │   └── vuetify.js
│   │   │
│   │   └── assets/
│   │       ├── logo.png
│   │       └── logo.svg
│   │
│   └── public/                 # Statische Assets
│
└── dist/                       # Build Output (generiert)
    ├── index.html
    └── static/
```

---

## ⚙️ Konfiguration

### config.toml (Beispiel)
```toml
[general]
url = "http://traccar-server:8082"
user = "admin"
password = "secure_password"
mapsapikey = "YOUR_GOOGLE_MAPS_API_KEY"
vuetraccarhash = "authentication_hash"
startdate = "2019-03-01"
standperiod = 8.0  # Stunden für Stillstands-Erkennung
prefetch_route = "prefetch_route.h5"
```

### travels.yml
Definiert bekannte Reiseziele und deren Zuordnung:
```yaml
"Sagres, Portugal":
  title: "2024 Spanien und Portugal Rundreise"
  from: null
  to: null
  exclude: null

"332, 6210 Bradl, Austria":
  title: null
  from: null
  to: null
  exclude: true  # Heimatadresse ausschließen
```

**Matching-Logik**: Wenn ein Standstill-Ort die Adresse enthält, wird er dieser Reise zugeordnet.

---

## 🚀 Setup & Deployment

### Installation

1. **Backend Setup**:
   ```bash
   # System-Dependencies
   apt install libopenblas0 libopenblas-dev
   apt install python3-tables python3-tables-lib
   
   # Python Environment
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Konfiguration
   cp config.toml.example config.toml
   # Edit config.toml mit Traccar-Credentials und Google API Key
   ```

2. **Frontend Setup**:
   ```bash
   cd frontend
   npm install
   npm run build
   ```

3. **Secret-Datei erstellen**:
   ```javascript
   // frontend/src/secret.js
   export const maps_api_key = 'YOUR_GOOGLE_MAPS_API_KEY';
   export const vuetraccarhash = 'YOUR_AUTH_HASH';
   ```

### Entwicklung

**Backend**:
```bash
python app.py
# Läuft auf http://0.0.0.0:5999 mit Auto-Reload
```

**Frontend**:
```bash
cd frontend
npm run dev
# Läuft auf http://localhost:3000 mit Hot-Reload
```

### Produktion

```bash
# Frontend bauen
cd frontend
npm run build

# Backend starten
export PRODUCTION=1
python app.py
# Oder mit start.sh:
./start.sh
```

**Docker** (optional):
```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libopenblas0 libopenblas-dev \
    python3-tables python3-tables-lib \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN cd frontend && npm install && npm run build

EXPOSE 5999
CMD ["python", "app.py"]
```

---

## 🐛 Bekannte Probleme & Verbesserungspotenzial

### 1. WordPress-Verlinkung (HAUPTPROBLEM)

**Aktueller Zustand**:
- Jeder Standort hat einen "zum Tagebuch" Button
- Öffnet MDDialog mit lokaler `.rst` Datei
- Benutzer muss Markdown manuell bearbeiten
- Links zu WordPress müssen manuell eingefügt werden
- Komplizierter Workflow

**Probleme**:
1. **Keine direkte Integration**: WordPress-Inhalte sind nicht automatisch verknüpft
2. **Doppelte Datenhaltung**: `.rst` Dateien vs. WordPress Datenbank
3. **Umständliches Bearbeiten**: Markdown-Editor statt WYSIWYG
4. **Link-Verwaltung**: Manuelle URL-Pflege fehleranfällig
5. **Kein Reverse-Lookup**: Von WordPress zu Karte nicht möglich

**Verbesserungsvorschläge**:

#### Option A: WordPress REST API Integration
```javascript
// Frontend: Automatisches Laden von WordPress-Posts
async function getWordPressContent(location) {
    const response = await fetch(
        `https://dein-blog.de/wp-json/wp/v2/posts?` +
        `tags=${location.key}&_embed`
    )
    const posts = await response.json()
    return posts[0] // Neuester Post mit diesem Tag
}
```

**Vorteile**:
- Direkte Anzeige von WordPress-Inhalten
- Automatische Synchronisation
- Keine doppelte Datenhaltung

**Implementation**:
1. WordPress-Posts mit GPS-Koordinaten oder Location-Key taggen
2. Frontend holt Posts via REST API
3. InfoWindow zeigt WordPress-Excerpt
4. "Mehr lesen" Link zu vollständigem Artikel

#### Option B: Vereinfachter Editor mit WordPress-Post-Picker
```javascript
// Dialog mit WordPress-Post-Suche
<template>
  <v-dialog>
    <v-autocomplete
      :items="wordpressPosts"
      v-model="selectedPost"
      label="WordPress-Artikel verknüpfen"
      @update:modelValue="linkPost"
    />
  </v-dialog>
</template>
```

**Vorteile**:
- Einfaches Verknüpfen statt manuelles Einfügen
- Validierte Links
- Vorschau des Artikels

#### Option C: Inline WordPress-Embed
```javascript
// WordPress-Inhalte direkt in InfoWindow einbetten
<InfoWindow>
  <div v-if="location.wordpressUrl">
    <iframe 
      :src="`${location.wordpressUrl}?embed=true`"
      width="400" 
      height="300"
    />
  </div>
</InfoWindow>
```

**Empfehlung**: **Option A** für beste UX, kombiniert mit:
- Backend-Endpoint `/wordpress/link` zum Speichern von Verknüpfungen
- Automatisches Tagging neuer WordPress-Posts mit GPS-Daten
- Bi-direktionale Verlinkung (Karte ↔ Blog)

### 2. Weitere Verbesserungsmöglichkeiten

#### Performance
- **Problem**: Bei langen Reisen viele GPS-Punkte
- **Lösung**: Polyline-Simplification (Douglas-Peucker-Algorithmus)
  ```python
  from simplification.cutil import simplify_coords
  simplified = simplify_coords(route_coords, 0.0001)
  ```

#### User Experience
- **Problem**: Kein Mobile-optimiertes Layout
- **Lösung**: Responsive Vuetify-Breakpoints nutzen
  ```vue
  <v-container fluid>
    <v-row>
      <v-col cols="12" md="8">
        <GMap />
      </v-col>
      <v-col cols="12" md="4">
        <TravelList />
      </v-col>
    </v-row>
  </v-container>
  ```

#### Features
- **Fehlend**: Fotos zu Standorten
- **Lösung**: 
  1. Photo-Upload mit Exif-GPS-Daten
  2. Automatische Zuordnung zu nächstem Standstill
  3. Galerie in InfoWindow
  
- **Fehlend**: Reise-Statistiken
- **Lösung**: Dashboard mit Charts (recharts)
  - Gesamtdistanz pro Jahr
  - Lieblingsländer
  - Durchschnittliche Aufenthaltsdauer

#### Datenhaltung
- **Problem**: `.rst` Dateien + HDF5 nicht optimal für Multiuser
- **Lösung**: Migration zu PostgreSQL + PostGIS
  ```sql
  CREATE TABLE standstills (
    id SERIAL PRIMARY KEY,
    location GEOGRAPHY(POINT),
    period INTERVAL,
    address TEXT,
    wordpress_url TEXT,
    photos JSONB
  );
  ```

---

## 🔐 Security & Authentication

### Aktueller Zustand
- **SSO Forward-Auth** implementiert (siehe `App.vue:19`)
- Authentifizierung aktuell deaktiviert (`authenticated = ref(true)`)
- Hash-basiertes Auth-System vorbereitet aber nicht aktiv

### Empfehlungen
1. **Aktiviere SSO**: Nutze existierende Forward-Auth
2. **HTTPS**: Nur über HTTPS betreiben
3. **API-Keys**: Google Maps API Key auf Domain beschränken
4. **CORS**: Quart-CORS auf eigene Domain limitieren
   ```python
   app = cors(app, allow_origin="https://deine-domain.de")
   ```

---

## 📈 Monitoring & Logging

### Aktuelles Logging
```python
# app.py und traccar.py nutzen print() Statements
print(f"getRouteData: {len(newroute)} new records")
print(f"route prefetch: {len(self._route)} recs")
```

### Verbesserungsvorschlag
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('vuetraccar.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"Route fetched: {len(newroute)} records")
logger.error(f"Traccar API failed: {error}")
```

---

## 🧪 Testing

### Aktueller Zustand
- Keine automatisierten Tests
- Manuelle Tests während Entwicklung

### Empfohlene Test-Strategie

#### Backend (pytest)
```python
# tests/test_traccar.py
import pytest
from dtraccar.traccar import Traccar

def test_distance_calculation():
    t = Traccar()
    pt1 = {'latitude': 47.0, 'longitude': 11.0}
    pt2 = {'latitude': 48.0, 'longitude': 12.0}
    dist = t._distance(pt1, pt2)
    assert 130 < dist < 150  # ca. 140 km

def test_standstill_detection():
    route = [
        {'fixTime': '2024-01-01T10:00:00Z', 'latitude': 47.0, 'longitude': 11.0},
        {'fixTime': '2024-01-01T10:05:00Z', 'latitude': 47.0001, 'longitude': 11.0001},
        # ... mehr Punkte
    ]
    analyzed, standstills = Traccar()._analyzeroute(route)
    assert len(standstills) > 0
```

#### Frontend (Vitest + Vue Test Utils)
```javascript
// tests/components/GMap.spec.js
import { mount } from '@vue/test-utils'
import GMap from '@/components/GMap.vue'

describe('GMap', () => {
  it('renders markers correctly', () => {
    const wrapper = mount(GMap, {
      props: {
        locations: [
          { lat: 47.0, lng: 11.0, address: 'Test' }
        ]
      }
    })
    expect(wrapper.find('.marker').exists()).toBe(true)
  })
})
```

---

## 📚 Weiterführende Dokumentation

### Externe APIs
- **Traccar API**: https://www.traccar.org/api-reference/
- **Google Maps JavaScript API**: https://developers.google.com/maps/documentation/javascript
- **Google Geocoding API**: https://developers.google.com/maps/documentation/geocoding
- **WordPress REST API**: https://developer.wordpress.org/rest-api/

### Frameworks
- **Quart**: https://quart.palletsprojects.com/
- **Vue 3**: https://vuejs.org/
- **Vuetify**: https://vuetifyjs.com/
- **Vite**: https://vitejs.dev/

---

## 🎯 Roadmap für Weiterentwicklung mit Claude Code

### Phase 1: WordPress-Integration (Priorität HOCH)
1. **Backend**:
   - Neuer Endpoint `/wordpress/posts` für Post-Suche
   - Endpoint `/wordpress/link` zum Verknüpfen von Standorten mit Posts
   - WordPress REST API Integration in `traccar.py`

2. **Frontend**:
   - `WordPressPicker.vue` Komponente
   - Automatisches Laden von WordPress-Content in InfoWindow
   - "Artikel verknüpfen" Button statt "Bearbeiten"

3. **Datenmodell**:
   - Erweitere Standstill-Modell um `wordpress_post_id`
   - Neue Tabelle/JSON für Location ↔ WordPress Mappings

### Phase 2: UI/UX Verbesserungen
1. Mobile-Responsive Layout
2. Foto-Upload und -Galerie
3. Reise-Statistiken Dashboard
4. Offline-Modus (Service Worker)

### Phase 3: Performance & Skalierung
1. Route-Simplification
2. Migration zu PostgreSQL + PostGIS
3. Redis Caching für Traccar API Calls
4. Lazy Loading für Marker

### Phase 4: Erweiterte Features
1. Mehrbenutzerverwaltung
2. Reise-Teilen (Public Links)
3. Export zu PDF/GPX
4. Kommentar-Funktion

---

## 💡 Schnellstart für Claude Code

### Typische Kommandos

```bash
# Projekt klonen/öffnen
git clone <repo>
cd VueTraccar-main

# Dependencies installieren
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Backend starten
python app.py

# Frontend entwickeln
cd frontend && npm run dev

# Tests ausführen (wenn vorhanden)
pytest
npm run test

# Deployment bauen
cd frontend && npm run build
```

### Wichtige Dateien für Änderungen

**WordPress-Integration**:
- `dtraccar/traccar.py` - Neue WordPress API-Funktionen
- `frontend/src/components/GMap.vue` - InfoWindow anpassen
- `frontend/src/app.js` - State Management erweitern

**UI Anpassungen**:
- `frontend/src/components/*.vue` - Vue-Komponenten
- `frontend/src/plugins/vuetify.js` - Theme

**API Änderungen**:
- `app.py` - Neue Endpoints
- `dtraccar/traccar.py` - Business Logic

### Debugging-Tipps

**Backend**:
```python
# In traccar.py oder app.py
import pdb; pdb.set_trace()  # Breakpoint setzen
```

**Frontend**:
```javascript
// In .vue oder .js Dateien
console.log('Debug:', variable)
debugger;  // Browser-Debugger
```

**API Testen**:
```bash
# Mit curl
curl -X POST http://localhost:5999/plotmaps \
  -H "Content-Type: application/json" \
  -d '{"deviceId":4,"from":"2024-01-01T00:00:00Z","to":"2024-12-31T23:59:59Z"}'
```

---

## 📞 Zusammenfassung für Claude Code

Diese App ist ein **Vue 3 + Quart**-basiertes System zur Wohnmobil-Reisedokumentation:

**Kernfunktionen**:
1. GPS-Daten von Traccar-Server holen
2. Stillstände (>8h) erkennen
3. Auf Google Maps visualisieren
4. Mit Reiseberichten verknüpfen (aktuell umständlich)

**Hauptverbesserung gesucht**:
Vereinfachung der WordPress-Verlinkung - von manuellem Markdown-Editieren zu automatischer Integration.

**Tech-Stack**:
- Backend: Python/Quart/Pandas
- Frontend: Vue 3/Vuetify/Google Maps
- Storage: HDF5 (Cache), .rst Files (Docs)

**Nächste Schritte**:
1. WordPress REST API Integration
2. Automatisches Post-Tagging mit GPS-Daten
3. Vereinfachtes Verknüpfungs-UI
4. Bi-direktionale Links (Karte ↔ Blog)

**Code-Qualität**: Gut strukturiert, aber:
- Wenig Kommentare in kritischen Algorithmen
- Keine Tests
- Print-Logging statt Logging-Framework
- `.rst` Files nicht ideal für Multiuser

Mit dieser Spezifikation kannst du jetzt mit **Claude Code** direkt starten!
