<script setup>
import { ref, mergeProps } from 'vue';
import { startdate, stopdate, travel, travels, openSettingsDialog,
    distance, getTravels, renderMap, downloadkml, delprefetch} from '@/app';
import { setCookie, deleteCookie } from '@/tools';

function setStartDate(params) {
    startdate.value = params;
}
function setStopDate(params) {
    stopdate.value = params;
}

async function update_travel(item) {
    var index = travels.value.map(function(e) { return e.title; }).indexOf(item);
    console.log(item, index, travels.value[index]);
    travel.value = travels.value[index]
    setCookie('travelindex', index, 30)
    startdate.value = new Date(travels.value[index].from.datetime);
    stopdate.value = new Date(travels.value[index].to.datetime);
    renderMap()


}

const menuitems = ref(['Debug', 'Export als KML', 'Log Out', 'Prefetch again']) //, 'Export als GPX', 'Export als CSV', 'Export als PDF'])
async function domenu(item) {
    switch (item) {
        case 'Debug':
            openSettingsDialog()
            break;
        case 'Export als KML':
            downloadkml()
            break;
        case 'Log Out':
            deleteCookie('authenticated')
            break;
        case 'Prefetch again':
            delprefetch()
            break;
        case 'Export als GPX':
            //downloadgpx()
            break;
        case 'Export als CSV':
            //downloadcsv()
            break;
        case 'Export als PDF':
            //downloadpdf()
            break;
    }
}

getTravels()
</script>

<template>
    <v-app-bar
        name="menu-bar"
        density="compact"
        color="grey-darken-3"
        :elevation="5"
        >
        <template v-slot:prepend>
            <v-menu location="bottom">
                <template v-slot:activator="{ props: menu }">
                    <v-tooltip open-delay="500">
                        <template v-slot:activator="{ props: tooltip }">
                            <v-app-bar-nav-icon
                            v-bind="mergeProps(menu, tooltip)"
                            nosize="small"
                            >
                            </v-app-bar-nav-icon>
                        </template>
                        <span>Tooltip</span>
                    </v-tooltip>
                </template>
                <v-list density="compact">
                    <v-list-item
                        v-for="(item, index) in menuitems"
                        :key="index"
                        :value="item"
                    >
                        <v-list-item-title @click="domenu(item)">{{ item }}</v-list-item-title>
                    </v-list-item>
                </v-list>
            </v-menu>
            <!--v-app-bar-title class="ml-2">Traccar Viewer</v-app-bar-title-->
        </template>

        <template v-slot:default>
            <v-select
                :label="`${travels.length} Reisen`"
                flat
                density="compact"
                prepend-icon="mdi-dots-vertical"
                v-model="travel"
                :items="travels"
                @update:model-value="update_travel"
                class="mt-5 ml-6 mb-0 pb-0"
            ></v-select>
            <v-chip
                variant="flat"
                color="transparent"
                class="ml-2">
                {{ distance }}
            </v-chip>
            <DateDialog :key="startdate" :datum="startdate" @getDate="setStartDate"/>
            <DateDialog :key="startdate" :datum="stopdate" @getDate="setStopDate"/>
        </template>
        <template v-slot:append>
            <v-btn
                icon="mdi-reload"
                class="ml-2"
                nosize="small"
                @click="renderMap"
            ></v-btn>
            <!--v-btn
                icon="mdi-set-all"
                class="ml-0"
                nosize="small"
                @click="renderMap"
            ></v-btn -->
            <v-btn icon= "mdi-rv-truck" href="https://tagebuch.smallfamilybusiness.net/" size="small"></v-btn>
            <!-- v-menu
                location="bottom"
                >
                <template v-slot:activator="{ props }">
                    <v-btn
                        icon="mdi-palette-swatch"
                        @click="toggleTheme"
                        v-bind="props"
                        size="small"
                    ></v-btn>
                </template>
                <v-list
                    density="compact"
                >
                        <v-list-item
                            v-for="[key, value] of Object.entries(theme.themes.value).filter(filterTheme)"
                            v-bind="props"
                            :key="key"
                            :value="key"
                            :color="isHovering ? 'primary' : 'transparent'"
                            >
                            <v-list-item-title
                                @click="setTheme(key)"
                            >{{ key }}</v-list-item-title>
                        </v-list-item>
                </v-list>
            </v-menu-->
        </template>
    </v-app-bar>
</template>
