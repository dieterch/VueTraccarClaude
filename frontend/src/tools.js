import { ref } from 'vue'
import axios from 'axios';
import CryptoJS from 'crypto-js';
export const host = ref(window.location.host)
export const protocol = ref(window.location.protocol)   


export const dohash = async (password) => {
    return CryptoJS.SHA512(password).toString(CryptoJS.enc.Hex);
}

export const validPassword = async (password, hash) => {
    let testhash = CryptoJS.SHA512(password).toString(CryptoJS.enc.Hex);
    return testhash === hash;
}  

export const setCookie = (name, value, days = 7, path = '/') => {
    const expires = new Date(Date.now() + days * 864e5).toUTCString()
    document.cookie = name + '=' + encodeURIComponent(value) + '; expires=' + expires + '; path=' + path
}

export const getCookie = (name) => {
    return document.cookie.split('; ').reduce((r, v) => {
        const parts = v.split('=')
        return parts[0] === name ? decodeURIComponent(parts[1]) : r
    }, '')
}

export const deleteCookie = (name, path = '/') => {
    setCookie(name, '', -1, path)
}
  
export function tracdate(mydate) { return mydate.toISOString().split('T')[0] + 'T00:00:00Z'}

export function DECtoDMS(dd)
{
    let vars  = dd.split('.');
    let deg   = vars[0];
    let tempma = "0."+vars[1];
    tempma = tempma * 3600;
    let min = Math.floor(tempma / 60);
    let sec = tempma - (min * 60);
    return `${deg}%C2%B0${min}'${sec}%22`;
}

export function GoogleMapsLink(lat, lng) {
    let Latdir = lat > 0 ? 'N' : 'S'; let LngDir = lng > 0 ? 'E' : 'W';
    return `https://www.google.com/maps/place/${DECtoDMS(String(Math.abs(lat)))}${Latdir}+${DECtoDMS(String(Math.abs(lng)))}${LngDir}/@${lat},${lng},12z`
}

export async function rget(api, headers = { 'Content-type': 'application/json', }) {
    const endpoint = `${protocol.value}//${host.value}${api}`
    // console.log('rpost:', endpoint, headers)
    try {
        const response = await axios.get( endpoint, 
            { headers: headers});
        return response.data
    } catch (e) {
        console.log(`${endpoint} \n` + String(e));
        alert(`${endpoint} \n` + String(e));
    }
}

export async function rpost(api, data, headers = { 'Content-type': 'application/json', }) {
    const endpoint = `${protocol.value}//${host.value}${api}`
    // console.log('rpost:', endpoint, data, headers)
    try {
        const response = await axios.post(
            endpoint, data, { headers: headers}
            );
        return response.data
    } catch (e) {
        console.log(`${endpoint} \n` + String(e));
        alert(`${endpoint} \n` + String(e));
    }
}