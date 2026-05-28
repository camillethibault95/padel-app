// =============================================================
// CHARGEMENT DES DONNEES
// =============================================================
let tournois = [];
let filtres = { cat: "all", genre: "all", dateFrom: "", dateTo: "" };
let markers = [];
let currentView = "map";
const today = new Date();
const todayStr = formatDateISO(today);
let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
let selectedDay = null;
let map;
let padelIcon;

function formatDateISO(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// Charger les données puis initialiser
fetch("tournois.json")
    .then(r => r.json())
    .then(data => {
        tournois = data;
        initMap();
        refreshMap();
    });

// =============================================================
// CARTE
// =============================================================
function initMap() {
    const avgLat = tournois.reduce((s, t) => s + t.lat, 0) / tournois.length;
    const avgLon = tournois.reduce((s, t) => s + t.lon, 0) / tournois.length;
    map = L.map("map").setView([avgLat, avgLon], 11);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "(c) OpenStreetMap",
        maxZoom: 19
    }).addTo(map);

    padelIcon = L.divIcon({
        html: '<div style="background:#d4ff00;border:2px solid #1a2554;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-weight:bold;color:#1a2554;">P</div>',
        className: "",
        iconSize: [28, 28],
        iconAnchor: [14, 14]
    });
}

function popupHtml(t) {
    return '<div class="popup-tournoi">' +
        '<h3>' + t.nom + '</h3>' +
        '<div class="info"><span class="badge cat-' + (t.categories[0] || 'P25') + '">' + t.categories_str + '</span></div>' +
        '<div class="info"><span class="label">Club</span><br>' + t.club + '</div>' +
        '<div class="info"><span class="label">Lieu</span><br>' + t.ville + '</div>' +
        '<div class="info"><span class="label">Dates</span><br>' + t.dates + '</div>' +
        '<div class="info"><span class="label">Epreuves</span><br>' + (t.epreuves || "Non précisée") + '</div>' +
        '<div class="info"><span class="label">Juge-arbitre</span><br>' + t.juge + '</div>' +
        (t.tel ? '<div class="info"><span class="label">Téléphone</span><br>' + t.tel + '</div>' : '') +
        (t.email ? '<div class="info"><span class="label">Email</span><br><a href="mailto:' + t.email + '">' + t.email + '</a></div>' : '') +
        '</div>';
}

// =============================================================
// FILTRAGE
// =============================================================
function filtrer() {
    return tournois.filter(t => {
        if (filtres.cat !== "all" && !t.categories.includes(filtres.cat)) return false;
        if (filtres.genre !== "all" && !t.epreuves.includes(filtres.genre)) return false;
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

// =============================================================
// CALENDRIER
// =============================================================
function refreshCalendar() {
    const visibles = filtrer();
    const year = currentMonth.getFullYear();
    const month = currentMonth.getMonth();

    const monthNames = ["Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"];
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

// =============================================================
// EVENEMENTS
// =============================================================
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

const dateFromInput = document.getElementById("date-from");
const dateToInput = document.getElementById("date-to");

function appliquerDates() {
    filtres.dateFrom = dateFromInput.value;
    filtres.dateTo = dateToInput.value;
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
