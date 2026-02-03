<script setup>
import { ref, nextTick } from "vue";
import {
  GoogleMap,
  MarkerCluster,
  Marker,
  Polyline,
  InfoWindow,
} from "vue3-google-map";
import { GoogleMapsLink } from "@/tools";
import {
  polygone,
  center,
  zoom,
  locations,
  togglemarkers,
  togglepath,
  getMDDocument,
} from "@/app";
import { maps_api_key } from "@/secret";
import MDDialog from "./MDDialog.vue";
import axios from "axios";

const flightPath = ref({
  path: polygone.value,
  geodesic: true,
  strokeColor: "#FF0000",
  strokeOpacity: 1.0,
  strokeWeight: 2,
});

const mapRef = ref(null);

function closeInfoWindows() {
  console.log("closeInfoWindows()");
  locations.value.forEach((location) => {
    location.infowindow = false;
  });
}

const mddialog = ref(false);
const mode = ref("light");
const content = ref("");
const file = ref("");
const wordpressPosts = ref({});
const copiedKey = ref(null);

async function openmddialog(key) {
  console.log("openmddialog", key);
  content.value = await getMDDocument(key);
  file.value = key;
  mddialog.value = true;
}

async function loadWordPressPosts(locationKey) {
  console.log("🔍 Loading posts for:", locationKey);
  
  try {
    const response = await axios.get(`/wordpress/posts/${locationKey}`);
    const posts = response.data;
    
    wordpressPosts.value = {
      ...wordpressPosts.value,
      [locationKey]: posts,
      [locationKey.toLowerCase()]: posts
    };
    
    console.log("✅ Loaded", posts.length, "posts");
    
  } catch (error) {
    console.error("❌ Error:", error);
    wordpressPosts.value = {
      ...wordpressPosts.value,
      [locationKey]: [],
      [locationKey.toLowerCase()]: []
    };
  }
}

async function handleMarkerClick(location) {
  closeInfoWindows();
  location.infowindow = true;

  // Posts parallel laden
  loadWordPressPosts(location.key);

  if (mapRef.value?.map) {
    const map = mapRef.value.map;

    // Schritt 1: Zentriere auf Marker
    map.panTo({
      lat: location.lat,
      lng: location.lng
    });

    // Schritt 2: Warte bis InfoWindow gerendert ist
    await new Promise(resolve => setTimeout(resolve, 350));

    // Schritt 3: Verschiebe Marker nach unten (InfoWindow bleibt sichtbar)
    map.panBy(0, -160);
  }
}

function copyToClipboard(key) {
  console.log("📋 Attempting to copy:", key);

  try {
    // Method 1: Select from input field and copy
    const input = document.getElementById('key-' + key);
    if (input) {
      input.select();
      input.setSelectionRange(0, 99999); // For mobile devices

      const success = document.execCommand('copy');
      if (success) {
        console.log("✅ Copied with execCommand from input");
      } else {
        throw new Error('execCommand failed');
      }
    } else {
      // Method 2: Fallback to textarea
      const textarea = document.createElement('textarea');
      textarea.value = key;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      textarea.setSelectionRange(0, 99999);
      const success = document.execCommand('copy');
      document.body.removeChild(textarea);

      if (!success) {
        throw new Error('execCommand failed');
      }
      console.log("✅ Copied with execCommand fallback");
    }

    // Update UI state
    copiedKey.value = key;

    // Reset after 2 seconds
    setTimeout(() => {
      copiedKey.value = null;
      console.log("🔄 Reset copied state");
    }, 2000);

  } catch (error) {
    console.error("❌ Failed to copy:", error);
    alert(`Konnte Key nicht kopieren: ${key}\nBitte manuell kopieren oder im Textfeld markieren und Strg+C drücken.`);
  }
}
</script>

<template>
  <GoogleMap
    ref="mapRef"
    :api-key="maps_api_key"
    style="width: 100%; height: calc(100vh - 48px)"
    :center="center"
    :zoom="zoom"
    @click="closeInfoWindows"
  >
    <Polyline v-if="togglepath" :options="flightPath" />
    <MarkerCluster v-if="togglemarkers">
      <Marker
        v-for="(location, i) in locations"
        :key="i"
        :options="{ position: location }"
        @click="handleMarkerClick(location)"
      >
        <InfoWindow 
          :options="{ 
            position: location, 
            minWidth: 350,
            maxWidth: 400
          }" 
          v-model="location.infowindow"
        >
          <div id="content">
            <div id="siteNotice"></div>
            <h2>{{ location.address.split(",")[0] }}</h2>
            <div id="bodyContent">
              <h4 v-for="(line, i) in location.address.split(',').slice(1)" :key="i">{{ line }}</h4>
              
              <p><a target="_blank" :href="GoogleMapsLink(location.lat, location.lng)">Link zu Google Maps</a></p>

              <table style="width: 100%; text-align: left; margin-top: 5px">
                <tr>
                  <th>Lat, Lng</th>
                  <td>{{ location.lat.toFixed(2) }}, {{ location.lng.toFixed(2) }}</td>
                </tr>
                <tr>
                  <th>von</th>
                  <td>{{ location.von }}</td>
                </tr>
                <tr>
                  <th>bis</th>
                  <td>{{ location.bis }}</td>
                </tr>
                <tr>
                  <th>Dauer</th>
                  <td>{{ location.period }}h</td>
                </tr>
              </table>

              <div style="margin-top: 15px; border-top: 2px solid #1976d2; padding-top: 15px">
                <h3 style="margin: 0 0 12px 0; font-size: 1.1em; color: #1976d2">📝 Reiseberichte</h3>

                <div v-if="wordpressPosts[location.key] && wordpressPosts[location.key].length > 0">
                  <div v-for="post in wordpressPosts[location.key].slice(0, 3)" :key="post.id" style="margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e0e0e0">
                    <h4 style="margin: 0 0 5px 0; font-size: 1em">
                      <a :href="post.link" target="_blank" style="color: #1976d2; text-decoration: none; font-weight: 500">{{ post.title }}</a>
                    </h4>
                    <div style="font-size: 0.85em; color: #666; margin-bottom: 5px">{{ new Date(post.date).toLocaleDateString("de-DE") }}</div>
                    <div style="font-size: 0.9em; line-height: 1.4; color: #333">{{ post.excerpt.replace(/<[^>]*>/g, '').substring(0, 150) }}...</div>
                  </div>

                  <div v-if="wordpressPosts[location.key].length > 3">
                    <a :href="wordpressPosts[location.key][0].link" target="_blank" style="font-size: 0.9em; color: #1976d2; text-decoration: none">→ Alle {{ wordpressPosts[location.key].length }} Beiträge ansehen</a>
                  </div>
                </div>

                <div v-else-if="wordpressPosts[location.key] && wordpressPosts[location.key].length === 0" style="font-style: italic; color: #999; font-size: 0.9em">Noch keine Reiseberichte für diesen Ort</div>

                <div v-else style="font-style: italic; color: #999; font-size: 0.9em">Lade Reiseberichte...</div>
              </div>

              <div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 4px; border: 1px solid #ddd">
                <div style="font-size: 0.75em; color: #666; margin-bottom: 6px; font-weight: 500">WordPress Tag Key:</div>
                <div style="display: flex; align-items: center; gap: 8px">
                  <input
                    type="text"
                    readonly
                    :value="location.key"
                    :id="'key-' + location.key"
                    style="flex: 1; font-size: 0.85em; color: #333; font-family: monospace; padding: 6px 8px; border: 1px solid #ccc; border-radius: 3px; background: white"
                  />
                  <button
                    @click.stop="copyToClipboard(location.key)"
                    :style="{
                      padding: '6px 12px',
                      fontSize: '0.8em',
                      fontWeight: '500',
                      border: 'none',
                      borderRadius: '3px',
                      cursor: 'pointer',
                      minWidth: '75px',
                      backgroundColor: copiedKey === location.key ? '#4caf50' : '#1976d2',
                      color: 'white',
                      transition: 'background-color 0.3s'
                    }"
                  >
                    {{ copiedKey === location.key ? '✓ Copied!' : 'Copy' }}
                  </button>
                </div>
              </div>

              <p>
                <v-btn color="primary" class="ma-2" size="x-small" @click="openmddialog(location.key)">zum Tagebuch</v-btn>
              </p>
            </div>
          </div>
        </InfoWindow>
      </Marker>
    </MarkerCluster>
    
    <MDDialog :content="content" :file="file" :mode="mode" :key="mddialog" :dialog="mddialog" @dialog="(e) => { mddialog = e; }" />
  </GoogleMap>
</template>

<style>
/* InfoWindow Styling - Größe begrenzen */
:deep(.gm-style-iw) {
  max-width: 400px !important;
  max-height: 60vh !important;
}

:deep(.gm-style-iw-c) {
  max-width: 400px !important;
  max-height: 60vh !important;
  padding: 12px !important;
}

:deep(.gm-style-iw-d) {
  max-height: calc(60vh - 60px) !important;
  overflow-y: auto !important;
}

/* Scrollbar */
:deep(.gm-style-iw-d::-webkit-scrollbar) {
  width: 6px;
}

:deep(.gm-style-iw-d::-webkit-scrollbar-track) {
  background: #f1f1f1;
  border-radius: 3px;
}

:deep(.gm-style-iw-d::-webkit-scrollbar-thumb) {
  background: #1976d2;
  border-radius: 3px;
}

:deep(.gm-style-iw-d::-webkit-scrollbar-thumb:hover) {
  background: #1565c0;
}
</style>