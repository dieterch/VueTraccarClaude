function DECtoDMS(dd)
{
    let vars  = dd.split('.');
    let deg   = vars[0];
    let tempma = "0."+vars[1];
    tempma = tempma * 3600;
    let min = Math.floor(tempma / 60);
    let sec = tempma - (min * 60);
    return deg+"°"+min+"'"+sec+'"';
}

function GoogleMapsLink(lat, lon) {
    return `https://www.google.com/maps/place/${DECtoDMS(String(lat))}N+${DECtoDMS(String(lon))}E`
}

console.log(DECtoDMS(String(43.88))) 
console.log(DECtoDMS(String(12.9574197)))

text = `https://www.google.com/maps/place/${DECtoDMS(String(43.88))}N+${DECtoDMS(String(12.9574197))}E`
console.log(text)

console.log(GoogleMapsLink(43.88, 12.9574197))