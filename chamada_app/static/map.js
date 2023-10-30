// script.js
var mymap = L.map('mapid').setView([51.505, -0.09], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors'
}).addTo(mymap);

if ("geolocation" in navigator) {
    navigator.geolocation.getCurrentPosition(function(position) {
        var lat = position.coords.latitude;
        var lon = position.coords.longitude;
        mymap.setView([lat, lon], 10);
        L.marker([lat, lon]).addTo(mymap)
        .bindPopup("Você está aqui.").openPopup();

        var fixedLocation = L.latLng(-22.9060827429717, -43.1332034197611);
        var currentLocation = L.latLng(lat, lon);
        var distance = fixedLocation.distanceTo(currentLocation);
        var radius = 500; // 500 meters

        if (distance <= radius) {
            console.log("Dentro do raio de 500 metros");
            L.marker([-22.9060827429717, -43.1332034197611]).addTo(mymap)
            .bindPopup("Localização fixa.").openPopup();
        } else {
            console.log("Fora do raio de 500 metros");
        }
    });
} else {
    console.log("Geolocalização não suportada");
}
