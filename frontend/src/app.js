import { ref, shallowRef, computed } from 'vue'
import { rpost, rget, DECtoDMS, tracdate, getCookie } from './tools.js'
import { useLoading } from 'vue-loading-overlay'
const $loading = useLoading({
    // Optional parameters
})
const fullPage = ref(false)

export const device = ref({name:'WMB Tk106', id:4})
export const startdate = ref(new Date('2019-03-01T00:00:00Z'))
export const stopdate = ref(new Date())
// export const order = ref(-1)

export function traccar_payload() {
    return {
        'name': travel.value.title || 'filename',
        'deviceId': device.value.id,
        'from': tracdate(startdate.value),
        'to': tracdate(stopdate.value),
        'maxpoints': '2500'
    }
}

export const travels = ref([])
export const travel = ref({})
export async function getTravels() { 
    travels.value = await rpost('/travels', traccar_payload())
    travels.value.forEach(t => {
        //console.log('t:', t)
        if ('newtitle' in t) {
            t.oldtitle = t.title
            t.title = t.newtitle
        }
    })

    if (getCookie('travelindex') != '') {
        let index = getCookie('travelindex')
        console.log('load cookie travelindex:', index)
        travel.value = travels.value[index]
    } else {
        travel.value = travels.value[travels.value.length - 1]
    }
    //travel.value = travels.value[3]
    startdate.value = new Date(travel.value.from.datetime);
    stopdate.value = new Date(travel.value.to.datetime);
    renderMap()
    }

export const route = ref({})
export async function getRoute() { 
    route.value = await rpost('/route',traccar_payload())
        //console.log('route:',route.value)
    }

export const events = ref({})
export async function getEvents() { 
    events.value = await rpost('/events', traccar_payload())
        //console.log('events:',events.value)
    }

    
export function download(data, filename) {
    let fileURL = window.URL.createObjectURL(new Blob([data]));
    let fURL = document.createElement('a'); 
    fURL.href = fileURL;
    fURL.setAttribute('download', filename);
    document.body.appendChild(fURL);
    fURL.click();
    document.body.removeChild(fURL);
}

export async function downloadkml() {
    let response =  await rpost('/download.kml',
        traccar_payload(),
        {'Accept': 'application/octet-stream'})
        download(response, travel.value.title + '.kml')
}

export async function delprefetch() {
    let response =  await rget('/delprefetch')
    console.log(response)
}

export const polygone = ref([])
export const center = ref({lat: 0, lng: 0})
export const zoom = ref(10)
export const distance = ref('') //ref('_______')
export const locations = ref([])
// export const bounds = computed(() => {
//     let lat = polygone.value.map(p => p.lat)
//     let lng = polygone.value.map(p => p.lng)
//     return {
//         sw: {lat: Math.min(...lat), lng: Math.min(...lng)},
//         ne: {lat: Math.max(...lat), lng: Math.max(...lng)}
//     }
// })
export async function getMDDocument(key) {
    let response =  await rget(`/document/${key}`)
    // console.log(response)
    return response['md']
}

export async function saveMDDocument(key, doc) {
    console.log('saveMDDocument:', key, doc)
    let response =  await rpost(`/document/${key}`, {'md': doc})
    // console.log(response)
    return response['md']
}


export async function renderMap() {
    const loader = $loading.show({
        // Optional parameters
    })
    const data = await rpost('/plotmaps', traccar_payload())
    loader.hide()
    console.log('data:', data)
    polygone.value = data['plotdata']
    zoom.value = data['zoom']
    center.value = data['center']
    distance.value = data['distance']
    locations.value = data['markers']
    // console.log('polygone:', polygone.value, 'zoom', zoom.value, 'center:', center.value)
}

// settings
export const settingsdialog = ref(false)
export async function openSettingsDialog() {
    settingsdialog.value = true
}
//export const markdownviewdialog = ref(false)
//export const markdowneditdialog = ref(false)

export const togglemap = ref(true)
export const togglemarkers = ref(true)
export const togglepath = ref(true)
export const toggletravels = ref(false)
export const toggleroute = ref(false)
export const toggleEvents = ref(false)
