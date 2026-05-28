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
        "date_debut": t["date_debut"],
        "categories": t["categories_p"] or "Non precisee",
        "ville": t["ville"],
        "juge": t["juge_arbitre"] or "Non precise",
        "tel": t["telephone"] or "",
        "email": t["email"] or "",
        "epreuves": t["epreuves"] or "",
    })

points_json = json.dumps(points, ensure_ascii=False)

html_template = '''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tournois Padel - Herault</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }

#header {
    background: #1a2554;
    color: white;
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
#header h1 { margin: 0; font-size: 18px; }
#count {
    background: #d4ff00;
    color: #1a2554;
    padding: 4px 12px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 14px;
}

#filters {
    background: white;
    padding: 12px 20px;
    border-bottom: 1px solid #e5e5e5;
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
}
.filter-label {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    font-weight: 600;
    margin-right: 4px;
}
.filter-btn {
    padding: 6px 14px;
    border: 1px solid #d0d0d0;
    background: white;
    border-radius: 20px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    color: #555;
    transition: all 0.15s;
}
.filter-btn:hover { border-color: #1a2554; }
.filter-btn.active {
    background: #1a2554;
    color: white;
    border-color: #1a2554;
}

#map { height: calc(100vh - 110px); }

.popup-tournoi { font-size: 13px; line-height: 1.5; }
.popup-tournoi h3 { margin: 0 0 8px; color: #1a2554; }
.popup-tournoi .badge {
    display: inline-block;
    background: #d4ff00;
    color: #1a2554;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: bold;
    font-size: 11px;
    margin-right: 4px;
}
.popup-tournoi .info { margin: 4px 0; color: #444; }
.popup-tournoi .label { color: #888; font-size: 11px; text-transform: uppercase; }
</style>
</head>
<body>
<div id="header">
    <h1>🎾 Tournois Padel - Herault</h1>
    <span id="count">__COUNT__ tournois</span>
</div>

<div id="filters">
    <span class="filter-label">Categorie :</span>
    <button class="filter-btn active" data-cat="all">Toutes</button>
    <button class="filter-btn" data-cat="P25">P25</button>
    <button class="filter-btn" data-cat="P50">P50</button>
    <button class="filter-btn" data-cat="P100">P100</button>
    <button class="filter-btn" data-cat="P250">P250</button>
    <button class="filter-btn" data-cat="P500">P500</button>
    <button class="filter-btn" data-cat="P1000">P1000</button>
</div>

<div id="map"></div>

<script>
const tournois = __DATA__;
let filtreCategorie = "all";
let markers = [];

const avgLat = tournois.reduce((s, t) => s + t.lat, 0) / tournois.length;
const avgLon = tournois.reduce((s, t) => s + t.lon, 0) / tournois.length;
const map = L.map("map").setView([avgLat, avgLon], 11);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "(c) OpenStreetMap",
    maxZoom: 19
}).addTo(map);

const padelIcon = L.divIcon({
    html: '<div style="background:#d4ff00;border:2px solid #1a2554;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:bold;color:#1a2554;">P</div>',
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14]
});

function popupHtml(t) {
    return '<div class="popup-tournoi">' +
        '<h3>' + t.nom + '</h3>' +
        '<div class="info"><span class="badge">' + t.categories + '</span></div>' +
        '<div class="info"><span class="label">Club</span><br>' + t.club + '</div>' +
        '<div class="info"><span class="label">Lieu</span><br>' + t.ville + '</div>' +
        '<div class="info"><span class="label">Dates</span><br>' + t.dates + '</div>' +
        '<div class="info"><span class="label">Juge-arbitre</span><br>' + t.juge + '</div>' +
        (t.tel ? '<div class="info"><span class="label">Telephone</span><br>' + t.tel + '</div>' : '') +
        (t.email ? '<div class="info"><span class="label">Email</span><br><a href="mailto:' + t.email + '">' + t.email + '</a></div>' : '') +
        '</div>';
}

function afficherMarkers() {
    // Nettoyer les anciens markers
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    
    // Filtrer les tournois selon la categorie
    const filtres = tournois.filter(t => {
        if (filtreCategorie === "all") return true;
        return t.categories.includes(filtreCategorie);
    });
    
    // Ajouter les nouveaux markers
    filtres.forEach(t => {
        const marker = L.marker([t.lat, t.lon], { icon: padelIcon })
            .addTo(map)
            .bindPopup(popupHtml(t));
        markers.push(marker);
    });
    
    // Mettre a jour le compteur
    document.getElementById("count").textContent = filtres.length + " tournois";
}

// Gestion des clics sur les filtres
document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        filtreCategorie = btn.dataset.cat;
        afficherMarkers();
    });
});

// Affichage initial
afficherMarkers();
</script>
</body>
</html>'''

html = html_template.replace("__COUNT__", str(len(tournois_geo)))
html = html.replace("__DATA__", points_json)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Carte generee : index.html")
