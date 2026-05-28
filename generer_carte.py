import csv
import json

with open("tournois.csv", "r", encoding="utf-8") as f:
    tournois = list(csv.DictReader(f))

tournois_geo = [t for t in tournois if t["latitude"] and t["longitude"]]
print(f"{len(tournois_geo)} tournois geolocalises sur {len(tournois)}")

def date_iso(d):
    if not d or "/" not in d:
        return ""
    parts = d.split("/")
    if len(parts) != 3:
        return ""
    return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"

points = []
for t in tournois_geo:
    cats_list = [c.strip() for c in (t["categories_p"] or "").split("/") if c.strip()]
    points.append({
        "lat": float(t["latitude"]),
        "lon": float(t["longitude"]),
        "club": t["club"],
        "nom": t["nom_tournoi"],
        "dates": t["date_debut"] + " -> " + t["date_fin"],
        "date_debut_iso": date_iso(t["date_debut"]),
        "date_fin_iso": date_iso(t["date_fin"]),
        "categories": cats_list,
        "categories_str": t["categories_p"] or "Non precisee",
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
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f5f6fa; }

.cat-P25   { background: #e5f5ff; color: #0066a1; }
.cat-P50   { background: #d4ecff; color: #00528a; }
.cat-P100  { background: #c6f6d5; color: #1d6f3a; }
.cat-P250  { background: #fef3c7; color: #92400e; }
.cat-P500  { background: #fed7aa; color: #9a3412; }
.cat-P1000 { background: #fbcfe8; color: #9d174d; }
.cat-P1500 { background: #ddd6fe; color: #5b21b6; }
.cat-P2000 { background: #fecaca; color: #991b1b; }

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

#view-toggle {
    background: #2a3568;
    padding: 8px 20px;
    display: flex;
    gap: 8px;
}
.view-btn {
    padding: 8px 16px;
    border: 1px solid transparent;
    background: transparent;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    color: rgba(255,255,255,0.7);
    font-weight: 500;
}
.view-btn.active {
    background: white;
    color: #1a2554;
}

#filters {
    background: white;
    padding: 12px 20px;
    border-bottom: 1px solid #e5e5e5;
}
.filter-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 8px;
}
.filter-row:last-child { margin-bottom: 0; }
.filter-label {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    font-weight: 600;
    margin-right: 4px;
    min-width: 80px;
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
.filter-btn[data-value^="P"]::before {
    content: "";
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}
.filter-btn[data-value="P25"]::before   { background: #0066a1; }
.filter-btn[data-value="P50"]::before   { background: #00528a; }
.filter-btn[data-value="P100"]::before  { background: #1d6f3a; }
.filter-btn[data-value="P250"]::before  { background: #92400e; }
.filter-btn[data-value="P500"]::before  { background: #9a3412; }
.filter-btn[data-value="P1000"]::before { background: #9d174d; }

.date-input {
    padding: 6px 10px;
    border: 1px solid #d0d0d0;
    border-radius: 8px;
    font-size: 13px;
    font-family: inherit;
    color: #333;
    cursor: pointer;
}
.date-input:focus { outline: none; border-color: #1a2554; }
.date-separator { color: #888; font-size: 13px; }
.reset-btn {
    padding: 6px 12px;
    border: none;
    background: transparent;
    color: #1a2554;
    cursor: pointer;
    font-size: 12px;
    text-decoration: underline;
}

#map { height: calc(100vh - 245px); }

#calendar-view {
    display: none;
    height: calc(100vh - 245px);
    grid-template-columns: 1fr 380px;
    gap: 16px;
    padding: 16px;
}
#calendar {
    background: white;
    border-radius: 8px;
    padding: 20px;
    overflow-y: auto;
}
#calendar-nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
}
#calendar-nav h2 { margin: 0; color: #1a2554; font-size: 20px; text-transform: capitalize; }
.nav-btn {
    background: #1a2554;
    color: white;
    border: none;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 18px;
}
.calendar-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 4px;
}
.calendar-header {
    text-align: center;
    font-weight: 600;
    color: #888;
    font-size: 12px;
    padding: 8px 0;
    text-transform: uppercase;
}
.calendar-day {
    aspect-ratio: 1;
    padding: 6px;
    border-radius: 6px;
    background: #f5f6fa;
    cursor: pointer;
    display: flex;
    flex-direction: column;
    transition: all 0.15s;
    min-height: 60px;
    border: 2px solid transparent;
}
.calendar-day:hover { background: #e5eafd; }
.calendar-day.empty {
    background: transparent;
    cursor: default;
}
.calendar-day.has-tournois {
    background: #fafafa;
    font-weight: 500;
}
.calendar-day.in-range {
    background: #fffbe5;
    border-color: #d4ff00;
}
.calendar-day.today {
    border-color: #d4ff00;
    box-shadow: 0 0 0 1px #1a2554 inset;
}
.calendar-day.today .day-number {
    background: #1a2554;
    color: #d4ff00;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}
.calendar-day.selected {
    background: #1a2554;
    color: white;
}
.calendar-day.out-of-range {
    opacity: 0.3;
}
.day-number {
    font-size: 14px;
    margin-bottom: 4px;
}
.day-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 2px;
}
.day-badge {
    font-size: 9px;
    padding: 1px 5px;
    border-radius: 3px;
    font-weight: 700;
}

#day-details {
    background: white;
    border-radius: 8px;
    padding: 20px;
    overflow-y: auto;
}
#day-details h3 { margin: 0 0 12px; color: #1a2554; }
.day-empty {
    color: #888;
    font-style: italic;
    padding: 20px 0;
    text-align: center;
}
.day-tournoi {
    border: 1px solid #e5e5e5;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
}
.day-tournoi-titre {
    font-weight: 600;
    color: #1a2554;
    margin-bottom: 6px;
    font-size: 14px;
}
.day-tournoi-info {
    font-size: 12px;
    color: #666;
    margin: 2px 0;
}
.day-tournoi .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-weight: bold;
    font-size: 10px;
    margin-right: 4px;
}

#legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e5e5e5;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 11px;
    color: #666;
}
.legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}

.popup-tournoi { font-size: 13px; line-height: 1.5; }
.popup-tournoi h3 { margin: 0 0 8px; color: #1a2554; }
.popup-tournoi .badge {
    display: inline-block;
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

<div id="view-toggle">
    <button class="view-btn active" data-view="map">🗺️ Carte</button>
    <button class="view-btn" data-view="calendar">📅 Calendrier</button>
</div>

<div id="filters">
    <div class="filter-row">
        <span class="filter-label">Categorie :</span>
        <button class="filter-btn active" data-type="cat" data-value="all">Toutes</button>
        <button class="filter-btn" data-type="cat" data-value="P25">P25</button>
        <button class="filter-btn" data-type="cat" data-value="P50">P50</button>
        <button class="filter-btn" data-type="cat" data-value="P100">P100</button>
        <button class="filter-btn" data-type="cat" data-value="P250">P250</button>
        <button class="filter-btn" data-type="cat" data-value="P500">P500</button>
        <button class="filter-btn" data-type="cat" data-value="P1000">P1000</button>
    </div>
    <div class="filter-row">
        <span class="filter-label">Genre :</span>
        <button class="filter-btn active" data-type="genre" data-value="all">Tous</button>
        <button class="filter-btn" data-type="genre" data-value="Messieurs">Messieurs</button>
        <button class="filter-btn" data-type="genre" data-value="Dames">Dames</button>
        <button class="filter-btn" data-type="genre" data-value="Mixte">Mixte</button>
    </div>
    <div class="filter-row">
        <span class="filter-label">Periode :</span>
        <span style="font-size:13px;color:#555;">Du</span>
        <input type="date" id="date-from" class="date-input">
        <span class="date-separator">au</span>
        <input type="date" id="date-to" class="date-input">
        <button class="reset-btn" id="reset-dates">Reinitialiser</button>
    </div>
</div>

<div id="map"></div>

<div id="calendar-view">
    <div id="calendar">
        <div id="calendar-nav">
            <button class="nav-btn" id="prev-month">‹</button>
            <h2 id="month-title">Juin 2026</h2>
            <button class="nav-btn" id="next-month">›</button>
        </div>
        <div class="calendar-grid" id="calendar-headers">
            <div class="calendar-header">Lun</div>
            <div class="calendar-header">Mar</div>
            <div class="calendar-header">Mer</div>
            <div class="calendar-header">Jeu</div>
            <div class="calendar-header">Ven</div>
            <div class="calendar-header">Sam</div>
            <div class="calendar-header">Dim</div>
        </div>
        <div class="calendar-grid" id="calendar-days"></div>
        <div id="legend">
            <div class="legend-item"><span class="legend-dot" style="background:#0066a1"></span>P25</div>
            <div class="legend-item"><span class="legend-dot" style="background:#00528a"></span>P50</div>
            <div class="legend-item"><span class="legend-dot" style="background:#1d6f3a"></span>P100</div>
            <div class="legend-item"><span class="legend-dot" style="background:#92400e"></span>P250</div>
            <div class="legend-item"><span class="legend-dot" style="background:#9a3412"></span>P500</div>
            <div class="legend-item"><span class="legend-dot" style="background:#9d174d"></span>P1000</div>
        </div>
    </div>
    <div id="day-details">
        <h3 id="day-title">Selectionne un jour</h3>
        <div id="day-list">
            <div class="day-empty">Clique sur une date du calendrier pour voir les tournois.</div>
        </div>
    </div>
</div>

<script>
const tournois = __DATA__;
let filtres = { cat: "all", genre: "all", dateFrom: "", dateTo: "" };
let markers = [];
let currentView = "map";
const today = new Date();
const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
let selectedDay = null;

// ----- CARTE -----
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
        '<div class="info"><span class="badge cat-' + (t.categories[0] || 'P25') + '">' + t.categories_str + '</span></div>' +
        '<div class="info"><span class="label">Club</span><br>' + t.club + '</div>' +
        '<div class="info"><span class="label">Lieu</span><br>' + t.ville + '</div>' +
        '<div class="info"><span class="label">Dates</span><br>' + t.dates + '</div>' +
        '<div class="info"><span class="label">Epreuves</span><br>' + (t.epreuves || "Non precisee") + '</div>' +
        '<div class="info"><span class="label">Juge-arbitre</span><br>' + t.juge + '</div>' +
        (t.tel ? '<div class="info"><span class="label">Telephone</span><br>' + t.tel + '</div>' : '') +
        (t.email ? '<div class="info"><span class="label">Email</span><br><a href="mailto:' + t.email + '">' + t.email + '</a></div>' : '') +
        '</div>';
}

function filtrer() {
    return tournois.filter(t => {
        if (filtres.cat !== "all" && !t.categories.includes(filtres.cat)) return false;
        if (filtres.genre !== "all" && !t.epreuves.includes(filtres.genre)) return false;
        // Filtre par plage : on garde si le tournoi chevauche la plage
        if (filtres.dateFrom && t.date_fin_iso < filtres.dateFrom) return false;
        if (filtres.dateTo && t.date_debut_iso > filtres.dateTo) return false;
        return true;
    });
}

function refreshMap() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    const visibles = filtrer();
    visibles.forEach(t => {
        const marker = L.marker([t.lat, t.lon], { icon: padelIcon })
            .addTo(map)
            .bindPopup(popupHtml(t));
        markers.push(marker);
    });
    document.getElementById("count").textContent = visibles.length + " tournois";
}

// ----- CALENDRIER -----
function refreshCalendar() {
    const visibles = filtrer();
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();
    
    const monthNames = ["Janvier","Fevrier","Mars","Avril","Mai","Juin","Juillet","Aout","Septembre","Octobre","Novembre","Decembre"];
    document.getElementById("month-title").textContent = monthNames[month] + " " + year;
    
    const grid = document.getElementById("calendar-days");
    grid.innerHTML = "";
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    let startWeekday = firstDay.getDay() - 1;
    if (startWeekday < 0) startWeekday = 6;
    
    for (let i = 0; i < startWeekday; i++) {
        const empty = document.createElement("div");
        empty.className = "calendar-day empty";
        grid.appendChild(empty);
    }
    
    for (let d = 1; d <= lastDay.getDate(); d++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
        const tournoisDuJour = visibles.filter(t => {
            return t.date_debut_iso <= dateStr && dateStr <= t.date_fin_iso;
        });
        
        const div = document.createElement("div");
        div.className = "calendar-day";
        if (tournoisDuJour.length > 0) div.classList.add("has-tournois");
        if (selectedDay === dateStr) div.classList.add("selected");
        if (dateStr === todayStr) div.classList.add("today");
        
        // Plage active : on highlight les jours dans la plage
        if (filtres.dateFrom && filtres.dateTo) {
            if (dateStr >= filtres.dateFrom && dateStr <= filtres.dateTo) {
                div.classList.add("in-range");
            } else {
                div.classList.add("out-of-range");
            }
        }
        
        const cats = new Set();
        tournoisDuJour.forEach(t => t.categories.forEach(c => cats.add(c)));
        const catsFiltrees = filtres.cat === "all" ? Array.from(cats) : Array.from(cats).filter(c => c === filtres.cat);
        const catsArr = catsFiltrees.sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1))).slice(0, 3);
        
        let badgesHtml = catsArr.map(c => `<span class="day-badge cat-${c}">${c}</span>`).join("");
        if (catsFiltrees.length > 3) badgesHtml += `<span class="day-badge" style="background:#ddd;color:#444;">+${catsFiltrees.length - 3}</span>`;
        
        div.innerHTML = `<span class="day-number">${d}</span><div class="day-badges">${badgesHtml}</div>`;
        
        div.addEventListener("click", () => {
            selectedDay = dateStr;
            showDayDetails(dateStr, tournoisDuJour);
            refreshCalendar();
        });
        
        grid.appendChild(div);
    }
}

function showDayDetails(dateStr, tournoisDuJour) {
    const [y, m, d] = dateStr.split("-");
    document.getElementById("day-title").textContent = `${d}/${m}/${y} — ${tournoisDuJour.length} tournoi${tournoisDuJour.length > 1 ? "s" : ""}`;
    
    const list = document.getElementById("day-list");
    if (tournoisDuJour.length === 0) {
        list.innerHTML = '<div class="day-empty">Aucun tournoi ce jour</div>';
        return;
    }
    
    list.innerHTML = tournoisDuJour.map(t => `
        <div class="day-tournoi">
            <div class="day-tournoi-titre">${t.nom}</div>
            <div class="day-tournoi-info"><span class="badge cat-${t.categories[0] || 'P25'}">${t.categories_str}</span> ${t.epreuves || ""}</div>
            <div class="day-tournoi-info">📍 ${t.ville} — ${t.club}</div>
            <div class="day-tournoi-info">⚖️ ${t.juge}</div>
            ${t.tel ? `<div class="day-tournoi-info">📞 ${t.tel}</div>` : ""}
            ${t.email ? `<div class="day-tournoi-info">✉️ <a href="mailto:${t.email}">${t.email}</a></div>` : ""}
        </div>
    `).join("");
}

document.getElementById("prev-month").addEventListener("click", () => {
    currentMonth.setMonth(currentMonth.getMonth() - 1);
    refreshCalendar();
});
document.getElementById("next-month").addEventListener("click", () => {
    currentMonth.setMonth(currentMonth.getMonth() + 1);
    refreshCalendar();
});

document.querySelectorAll(".view-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentView = btn.dataset.view;
        if (currentView === "map") {
            document.getElementById("map").style.display = "block";
            document.getElementById("calendar-view").style.display = "none";
            map.invalidateSize();
        } else {
            document.getElementById("map").style.display = "none";
            document.getElementById("calendar-view").style.display = "grid";
            refreshCalendar();
        }
    });
});

document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        const type = btn.dataset.type;
        document.querySelectorAll(`.filter-btn[data-type="${type}"]`).forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        filtres[type] = btn.dataset.value;
        refreshMap();
        if (currentView === "calendar") refreshCalendar();
    });
});

// Filtres dates
const dateFromInput = document.getElementById("date-from");
const dateToInput = document.getElementById("date-to");

function appliquerDates() {
    filtres.dateFrom = dateFromInput.value;
    filtres.dateTo = dateToInput.value;
    
    // Si une date "Du" est choisie, on saute au mois correspondant
    if (filtres.dateFrom) {
        const d = new Date(filtres.dateFrom);
        currentMonth = new Date(d.getFullYear(), d.getMonth(), 1);
    }
    
    refreshMap();
    if (currentView === "calendar") refreshCalendar();
}

dateFromInput.addEventListener("change", appliquerDates);
dateToInput.addEventListener("change", appliquerDates);

document.getElementById("reset-dates").addEventListener("click", () => {
    dateFromInput.value = "";
    dateToInput.value = "";
    filtres.dateFrom = "";
    filtres.dateTo = "";
    refreshMap();
    if (currentView === "calendar") refreshCalendar();
});

refreshMap();
</script>
</body>
</html>'''

html = html_template.replace("__COUNT__", str(len(tournois_geo)))
html = html.replace("__DATA__", points_json)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Carte generee : index.html")
