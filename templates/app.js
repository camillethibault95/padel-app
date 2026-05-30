let tournois = [];
let filtres = { cat: "all", genre: "all", dateFrom: "", dateTo: "" };
let userPosition = null;
let rayonKm = 10;
let userMarker = null;
let markers = [];
let currentView = "map";
const today = new Date();
const todayStr = formatDateISO(today);
let currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
let selectedDay = null;
let map;
let padelIcon;
let suggestionsTimeout = null;

function formatDateISO(d) {
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function distanceKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const toRad = x => x * Math.PI / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat/2) ** 2 +
              Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
              Math.sin(dLon/2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
}

function badgesHtml(t) {
    const paires = t.epreuves_detail || [];
    if (paires.length === 0) {
        if (!t.categories || t.categories.length === 0) {
            return '<span class="badge cat-P25">?</span>';
        }
        return t.categories.map(c => '<span class="badge cat-' + c + '">' + c + '</span>').join(" ");
    }
    const cats = [...new Set(paires.map(p => p.categorie))].sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1)));
    return cats.map(c => '<span class="badge cat-' + c + '">' + c + '</span>').join(" ");
}

fetch("tournois.json")
    .then(r => r.json())
    .then(data => {
        tournois = data;
        initMap();
        refreshMap();
    });

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
    let distanceInfo = "";
    if (userPosition) {
        const d = distanceKm(userPosition.lat, userPosition.lon, t.lat, t.lon);
        distanceInfo = '<div class="info"><span class="label">Distance</span><br>📍 ' + d.toFixed(1) + ' km</div>';
    }
    return '<div class="popup-tournoi">' +
        '<h3>' + t.nom + '</h3>' +
        '<div class="info">' + badgesHtml(t) + '</div>' +
        '<div class="info"><span class="label">Club</span><br>' + t.club + '</div>' +
        '<div class="info"><span class="label">Lieu</span><br>' + t.ville + '</div>' +
        distanceInfo +
        '<div class="info"><span class="label">Dates</span><br>' + t.dates + '</div>' +
        '<div class="info"><span class="label">Epreuves</span><br>' + (t.epreuves || "Non précisée") + '</div>' +
        '<div class="info"><span class="label">Juge-arbitre</span><br>' + t.juge + '</div>' +
        (t.tel ? '<div class="info"><span class="label">Téléphone</span><br>' + t.tel + '</div>' : '') +
        (t.email ? '<div class="info"><span class="label">Email</span><br><a href="mailto:' + t.email + '">' + t.email + '</a></div>' : '') +
        '</div>';
}

function filtrer() {
    return tournois.filter(t => {
        if (filtres.dateFrom && t.date_fin_iso < filtres.dateFrom) return false;
        if (filtres.dateTo && t.date_debut_iso > filtres.dateTo) return false;
        
        if (userPosition) {
            const d = distanceKm(userPosition.lat, userPosition.lon, t.lat, t.lon);
            if (d > rayonKm) return false;
        }
        
        if (filtres.cat === "all" && filtres.genre === "all") return true;
        
        const paires = t.epreuves_detail || [];
        if (paires.length === 0) return false;
        
        return paires.some(p => {
            if (filtres.cat !== "all" && p.categorie !== filtres.cat) return false;
            if (filtres.genre !== "all" && p.genre !== filtres.genre) return false;
            return true;
        });
    });
}

function refreshMap() {
    markers.forEach(m => map.removeLayer(m));
    markers = [];
    const visibles = filtrer();
    
    if (userPosition) {
        visibles.sort((a, b) => {
            const dA = distanceKm(userPosition.lat, userPosition.lon, a.lat, a.lon);
            const dB = distanceKm(userPosition.lat, userPosition.lon, b.lat, b.lon);
            return dA - dB;
        });
    }
    
    visibles.forEach(t => {
        const marker = L.marker([t.lat, t.lon], { icon: padelIcon })
            .addTo(map)
            .bindPopup(popupHtml(t));
        markers.push(marker);
    });
    document.getElementById("count").textContent = visibles.length + " tournois";
}

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
        const tournoisDuJour = visibles.filter(t => t.date_debut_iso <= dateStr && dateStr <= t.date_fin_iso);

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

        const catsTrouvees = new Set();
        tournoisDuJour.forEach(t => {
            const paires = t.epreuves_detail || [];
            paires.forEach(p => {
                if (filtres.cat !== "all" && p.categorie !== filtres.cat) return;
                if (filtres.genre !== "all" && p.genre !== filtres.genre) return;
                catsTrouvees.add(p.categorie);
            });
        });
        
        const catsArr = Array.from(catsTrouvees).sort((a, b) => parseInt(a.slice(1)) - parseInt(b.slice(1))).slice(0, 3);
        let html = catsArr.map(c => '<span class="day-badge cat-' + c + '">' + c + '</span>').join("");
        if (catsTrouvees.size > 3) html += '<span class="day-badge" style="background:#ddd;color:#444;">+' + (catsTrouvees.size - 3) + '</span>';

        div.innerHTML = '<span class="day-number">' + d + '</span><div class="day-badges">' + html + '</div>';

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
    document.getElementById("day-title").textContent = d + "/" + m + "/" + y + " — " + tournoisDuJour.length + " tournoi" + (tournoisDuJour.length > 1 ? "s" : "");

    const list = document.getElementById("day-list");
    if (tournoisDuJour.length === 0) {
        list.innerHTML = '<div class="day-empty">Aucun tournoi ce jour</div>';
        return;
    }

    list.innerHTML = tournoisDuJour.map(t => {
        let distanceInfo = "";
        if (userPosition) {
            const d2 = distanceKm(userPosition.lat, userPosition.lon, t.lat, t.lon);
            distanceInfo = ' • 📍 ' + d2.toFixed(1) + ' km';
        }
        return '<div class="day-tournoi">' +
            '<div class="day-tournoi-titre">' + t.nom + '</div>' +
            '<div class="day-tournoi-info">' + badgesHtml(t) + ' ' + (t.epreuves || "") + '</div>' +
            '<div class="day-tournoi-info">📍 ' + t.ville + ' — ' + t.club + distanceInfo + '</div>' +
            '<div class="day-tournoi-info">⚖️ ' + t.juge + '</div>' +
            (t.tel ? '<div class="day-tournoi-info">📞 ' + t.tel + '</div>' : "") +
            (t.email ? '<div class="day-tournoi-info">✉️ <a href="mailto:' + t.email + '">' + t.email + '</a></div>' : "") +
        '</div>';
    }).join("");
}

// ----- POSITION (geoloc OU adresse avec autocomplete) -----
const geolocBtn = document.getElementById("geoloc-btn");
const addressInput = document.getElementById("address-input");
const addressSuggestions = document.getElementById("address-suggestions");
const resetGeolocBtn = document.getElementById("reset-geoloc");
const geolocStatus = document.getElementById("geoloc-status");
const rayonSelect = document.getElementById("rayon-select");

function setUserPosition(lat, lon, label) {
    userPosition = { lat: lat, lon: lon };
    
    if (userMarker) map.removeLayer(userMarker);
    const userIcon = L.divIcon({
        html: '<div class="user-location-marker"></div>',
        className: "",
        iconSize: [18, 18],
        iconAnchor: [9, 9]
    });
    userMarker = L.marker([lat, lon], { icon: userIcon })
        .addTo(map)
        .bindPopup(label || "Ta position");
    
    map.setView([lat, lon], 12);
    resetGeolocBtn.style.display = "inline-block";
    refreshMap();
    if (currentView === "calendar") refreshCalendar();
}

// Géolocalisation navigateur
geolocBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
        geolocStatus.textContent = "Géolocalisation non supportée";
        return;
    }
    geolocStatus.textContent = "Recherche de ta position...";
    
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            geolocBtn.classList.add("active");
            geolocStatus.textContent = "📍 Position trouvée";
            setUserPosition(pos.coords.latitude, pos.coords.longitude, "Ta position");
        },
        (err) => {
            if (err.code === 1) {
                geolocStatus.textContent = "⚠️ Tu as refusé la géoloc — utilise plutôt ton adresse";
            } else {
                geolocStatus.textContent = "⚠️ Erreur géoloc — utilise plutôt ton adresse";
            }
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
});

// AUTOCOMPLETE adresse
function chercherSuggestions(query) {
    if (!query || query.length < 3) {
        addressSuggestions.style.display = "none";
        return;
    }
    
    const url = "https://api-adresse.data.gouv.fr/search/?q=" + encodeURIComponent(query) + "&limit=5";
    
    fetch(url)
        .then(r => r.json())
        .then(data => {
            if (!data.features || data.features.length === 0) {
                addressSuggestions.style.display = "none";
                return;
            }
            
            addressSuggestions.innerHTML = data.features.map((f, i) => {
                const label = f.properties.label;
                const city = f.properties.city || f.properties.name || "";
                return '<div class="suggestion-item" data-index="' + i + '">' +
                    '<div>' + label + '</div>' +
                    '</div>';
            }).join("");
            
            // Stocker les résultats pour pouvoir les utiliser au clic
            addressSuggestions.dataset.results = JSON.stringify(data.features.map(f => ({
                lat: f.geometry.coordinates[1],
                lon: f.geometry.coordinates[0],
                label: f.properties.label
            })));
            
            addressSuggestions.style.display = "block";
            
            // Ajouter les clics sur les suggestions
            addressSuggestions.querySelectorAll(".suggestion-item").forEach(item => {
                item.addEventListener("click", () => {
                    const idx = parseInt(item.dataset.index);
                    const results = JSON.parse(addressSuggestions.dataset.results);
                    const sel = results[idx];
                    
                    addressInput.value = sel.label;
                    addressSuggestions.style.display = "none";
                    geolocBtn.classList.remove("active");
                    geolocStatus.textContent = "📍 " + sel.label;
                    setUserPosition(sel.lat, sel.lon, sel.label);
                });
            });
        })
        .catch(err => {
            console.error("Erreur autocomplete:", err);
            addressSuggestions.style.display = "none";
        });
}

// Debounce : on attend 300ms après la dernière frappe avant d'appeler l'API
addressInput.addEventListener("input", () => {
    clearTimeout(suggestionsTimeout);
    const query = addressInput.value.trim();
    suggestionsTimeout = setTimeout(() => chercherSuggestions(query), 300);
});

// Cacher les suggestions si on clique ailleurs
document.addEventListener("click", (e) => {
    if (!e.target.closest("#address-wrapper")) {
        addressSuggestions.style.display = "none";
    }
});

// Si on appuie sur Entrée, on prend la première suggestion
addressInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        e.preventDefault();
        const firstSuggestion = addressSuggestions.querySelector(".suggestion-item");
        if (firstSuggestion) firstSuggestion.click();
    } else if (e.key === "Escape") {
        addressSuggestions.style.display = "none";
    }
});

// Désactiver position
resetGeolocBtn.addEventListener("click", () => {
    userPosition = null;
    if (userMarker) {
        map.removeLayer(userMarker);
        userMarker = null;
    }
    geolocBtn.classList.remove("active");
    addressInput.value = "";
    resetGeolocBtn.style.display = "none";
    geolocStatus.textContent = "";
    refreshMap();
    if (currentView === "calendar") refreshCalendar();
});

rayonSelect.addEventListener("change", () => {
    rayonKm = parseInt(rayonSelect.value);
    if (userPosition) {
        refreshMap();
        if (currentView === "calendar") refreshCalendar();
    }
});

// ----- AUTRES EVENEMENTS -----
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

document.querySelectorAll(".filter-btn[data-type]").forEach(btn => {
    btn.addEventListener("click", () => {
        const type = btn.dataset.type;
        document.querySelectorAll(".filter-btn[data-type=\"" + type + "\"]").forEach(b => b.classList.remove("active"));
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

// ----- MOBILE : OUVRIR/FERMER LE PANNEAU FILTRES -----
const mobileFiltersToggle = document.getElementById("mobile-filters-toggle");
const mobileFiltersClose = document.getElementById("mobile-filters-close");
const filtersPanel = document.getElementById("filters");

if (mobileFiltersToggle) {
    mobileFiltersToggle.addEventListener("click", () => {
        filtersPanel.classList.add("mobile-open");
    });
}

if (mobileFiltersClose) {
    mobileFiltersClose.addEventListener("click", () => {
        filtersPanel.classList.remove("mobile-open");
    });
}

// ----- MOBILE : DETAILS DU JOUR EN BOTTOM-SHEET -----
const dayDetailsClose = document.getElementById("day-details-close");
const dayDetailsPanel = document.getElementById("day-details");

if (dayDetailsClose) {
    dayDetailsClose.addEventListener("click", () => {
        dayDetailsPanel.classList.remove("mobile-open");
    });
}

// Quand on clique sur un jour avec tournois, ouvrir le bottom-sheet
const originalShowDayDetails = showDayDetails;
showDayDetails = function(dateStr, tournoisDuJour) {
    originalShowDayDetails(dateStr, tournoisDuJour);
    if (window.innerWidth <= 768 && tournoisDuJour.length > 0) {
        dayDetailsPanel.classList.add("mobile-open");
    }
};
