import csv
import json

with open("tournois.csv", "r", encoding="utf-8") as f:
    tournois = list(csv.DictReader(f))

tournois_geo = [t for t in tournois if t["latitude"] and t["longitude"]]
print(f"{len(tournois_geo)} tournois geolocalises sur {len(tournois)}")

points = []
for t in tournois_geo:
    points.append({
        "lat": float(t["latitude"]),
        "lon": float(t["longitude"]),
        "club": t["club"],
        "nom": t["nom_tournoi"],
        "dates": t["date_debut"] + " -> " + t["date_fin"],
        "categories": t["categories_p"] or "Non precisee",
        "ville": t["ville"],
        "juge": t["juge_arbitre"] or "Non precise",
        "tel": t["telephone"] or "",
        "email": t["email"] or "",
    })

points_json = json.dumps(points, ensure_ascii=False)

html_template = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Tournois Padel Montpellier</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
#header { background: #1a2554; color: white; padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
#header h1 { margin: 0; font-size: 20px; }
#header .count { background: #d4ff00; color: #1a2554; padding: 4px 12px; border-radius: 20px; font-weight: bold; font-size: 14px; }
#map { height: calc(100vh - 60px); }
.popup-tournoi { font-size: 13px; line-height: 1.5; }
.popup-tournoi h3 { margin: 0 0 8px; color: #1a2554; }
.popup-tournoi .badge { display: inline-block; background: #d4ff00; color: #1a2554; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; margin-right: 4px; }
.popup-tournoi .info { margin: 4px 0; color: #444; }
.popup-tournoi .label { color: #888; font-size: 11px; text-transform: uppercase; }
</style>
</head>
<body>
<div id="header">
<h1>Tournois Padel - Herault</h1>
<span class="count">__COUNT__ tournois</span>
</div>
<div id="map"></div>
<script>
const tournois = __DATA__;
const avgLat = tournois.reduce((s, t) => s + t.lat, 0) / tournois.length;
const avgLon = tournois.reduce((s, t) => s + t.lon, 0) / tournois.length;
const map = L.map("map").setView([avgLat, avgLon], 11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "(c) OpenStreetMap",
    maxZoom: 19
}).addTo(map);
const padelIcon = L.divIcon({
    html: '<div style="background:#d4ff00;border:2px solid #1a2554;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:14px;">P</div>',
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14]
});
tournois.forEach(t => {
    const popup = '<div class="popup-tournoi">' +
        '<h3>' + t.nom + '</h3>' +
        '<div class="info"><span class="badge">' + t.categories + '</span></div>' +
        '<div class="info"><span class="label">Club</span><br>' + t.club + '</div>' +
        '<div class="info"><span class="label">Lieu</span><br>' + t.ville + '</div>' +
        '<div class="info"><span class="label">Dates</span><br>' + t.dates + '</div>' +
        '<div class="info"><span class="label">Juge-arbitre</span><br>' + t.juge + '</div>' +
        (t.tel ? '<div class="info"><span class="label">Telephone</span><br>' + t.tel + '</div>' : '') +
        (t.email ? '<div class="info"><span class="label">Email</span><br><a href="mailto:' + t.email + '">' + t.email + '</a></div>' : '') +
        '</div>';
    L.marker([t.lat, t.lon], { icon: padelIcon }).addTo(map).bindPopup(popup);
});
</script>
</body>
</html>'''

html = html_template.replace("__COUNT__", str(len(tournois_geo)))
html = html.replace("__DATA__", points_json)

with open("carte.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Carte generee : carte.html")
print("Pour l'ouvrir : open carte.html")
