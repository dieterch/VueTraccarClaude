<script setup>
import { ref } from 'vue'
import { vuetraccarhash } from '@/secret';
import { 
  startdate, stopdate, 
  polygone, 
  togglemap, 
  travel, 
  travels, 
  toggletravels,
  route, 
  toggleroute,
  events,
  toggleEvents
} from '@/app';


// const authenticated = ref(false);
const authenticated = ref(true);     // no authentication needed, sso forward-auth implemented. Dieter 28.1.2025

</script>

<template>
  <v-app 
  class="rounded rounded-md">
    <div
      v-if="!authenticated"
    >
      <Login 
        :hash="vuetraccarhash"
        :authenticated="authenticated"
        @authenticated="(e)=>{
          // console.log('authenticated', e)
          authenticated = e
          }"
      />
    </div>
    <div
      v-else
    >
      <AppBar />
      <!--SideBar /-->
      <!--v-main class="d-flex align-center justify-center" style="min-height: 300px;"-->
      <v-main>
          <DebugDialog />
          <GMap v-if="togglemap" :key=polygone />
          <pre v-if="toggletravels">
  Reise {{ travel }}
          </pre>
          <pre v-if="toggleroute">
  Route {{ route }}
          </pre>
          <pre v-if="toggleEvents">
  Events {{ events }}
          </pre>
        </v-main>
    </div>
  </v-app>
</template>