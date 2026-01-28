<script setup>
import { ref } from "vue";
import { GoogleMap, MarkerCluster, Marker, Polyline, InfoWindow } from "vue3-google-map";
import { GoogleMapsLink } from "@/tools"
import { polygone, center, zoom, locations, togglemarkers, togglepath, getMDDocument } from '@/app';
import { maps_api_key } from '@/secret';
import MDDialog from "./MDDialog.vue";

const flightPath = ref({
    path: polygone.value,
    geodesic: true,
    strokeColor: "#FF0000",
    strokeOpacity: 1.0,
    strokeWeight: 2
  });

function closeInfoWindows() {
    console.log('closeInfoWindows()');
    locations.value.forEach((location) => {
        location.infowindow = false;
    });
}

const mddialog = ref(false)
const mode = ref('light')
const content = ref('');
const file = ref('')

async function openmddialog(key) {
    console.log('openmddialog', key)
    content.value = await getMDDocument(key)
    file.value = key
    mddialog.value = true
}
</script>

<template>
  <GoogleMap
    :api-key="maps_api_key"
    style="width: 100%; height: calc(100vh - 48px);"
    :center="center"
    :zoom="zoom"
    @click="closeInfoWindows">
    <Polyline v-if="togglepath" :options="flightPath" />
    <MarkerCluster
      v-if="togglemarkers"
    >
        <Marker
          v-for="(location, i) in locations"
          :key="i"
          :options="{ position: location }"
          @click="closeInfoWindows"
        >
        <!--InfoWindow :options="{ position: location, content: 'Hello World!' }" /-->
        <InfoWindow
          :options="{ position: location, minWidth: 250}"
          v-model="location.infowindow"
        >
          <div id="content">
              <div id="siteNotice">
              </div>
              <!--h1 id="firstHeading" class="firstHeading">{{ location.country }} ({{ location.period }}h)</h1-->
              <h2>{{ location.address.split(',')[0] }}</h2>
              <div id="bodyContent">
                <h4
                  v-for="(line, i) in location.address.split(',').slice(1)"
                >
                  {{ line }}
                </h4>
                <p>
                  <a
                  target="_blank"
                  :href="GoogleMapsLink(location.lat, location.lng)">
                  Link zu Google Maps</a>
                </p>

                <table
                  style="width: 100%; text-align: left; margin-top: 5px;"
                >
                  <tr>
                    <th>Lat, Lng </th>
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
                <p>
                  <!--v-btn
                    color="primary"
                    class="ma-2"
                    size="x-small"
                    @click="openmddialog(location.key)"
                  >
                    Zusatzinfo
                  </v-btn-->
                  <v-btn
                    color="primary"
                    class="ma-2"
                    size="x-small"
                    @click="openmddialog(location.key)"
                  >
                    zum Tagebuch
                  </v-btn>
                </p>
              </div>
          </div>
        </InfoWindow>
        </Marker>
    </MarkerCluster>
    <MDDialog
      :content="content"
      :file="file"
      :mode="mode"
      :key="mddialog"
      :dialog="mddialog"
      @dialog="(e)=>{mddialog = e}" />
  </GoogleMap>
</template>
