<script setup>
import { ref } from 'vue'
import { downloadkml, distance } from '@/app';

</script>

<template>
    <v-navigation-drawer color="grey-darken-2" :width="80" permanent>
        <template v-slot:prepend>
            <v-sheet 
                class="d-flex flex-column justify-left align-center ga-4 mt-4"
                color="transparent"
                >
                <v-btn
                    color="grey-darken-3"
                    icon="mdi-google-earth"
                    @click="downloadkml"
                    class="d-flex">
                </v-btn>
                <v-btn
                    color="grey-darken-3"
                    icon="mdi-google-earth"
                    @click="downloadkml"
                    class="d-flex">
                </v-btn>
                <v-btn
                    color="grey-darken-3"
                    icon="mdi-google-earth"
                    @click="downloadkml"
                    class="d-flex">
                </v-btn>
            </v-sheet>
        </template>
        <template v-slot:append>
            <v-sheet 
                class="d-flex flex-column justify-left align-center"
                color="transparent"
                >
                <div class="d-flex mb-2">
                    <v-chip variant="flat" color="transparent">
                        {{ distance }}
                    </v-chip>
                </div>
            </v-sheet>
        </template>
    </v-navigation-drawer>
</template>
