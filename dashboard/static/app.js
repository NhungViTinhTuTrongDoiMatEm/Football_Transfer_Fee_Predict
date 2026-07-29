// API Base URL
const API_URL = "";

// Element Selectors
const searchInput = document.getElementById("player-search-input");
const searchSpinner = document.getElementById("search-spinner");
const searchResults = document.getElementById("search-results");
const welcomePanel = document.getElementById("welcome-panel");
const dashboardPanel = document.getElementById("dashboard-panel");

// Player State
let currentPlayerId = null;
let currentPlayerStats = [];

// Debounce timer
let debounceTimer;

// Handle Input in Search Box
searchInput.addEventListener("input", function() {
    clearTimeout(debounceTimer);
    const query = searchInput.value.trim();
    
    if (query.length < 2) {
        searchResults.style.display = "none";
        return;
    }
    
    searchSpinner.style.display = "block";
    
    debounceTimer = setTimeout(() => {
        fetch(`${API_URL}/api/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                renderSearchResults(data);
            })
            .catch(err => {
                console.error("Lỗi tìm kiếm:", err);
            })
            .finally(() => {
                searchSpinner.style.display = "none";
            });
    }, 300);
});

// Render Dropdown Results
function renderSearchResults(players) {
    if (players.length === 0) {
        searchResults.innerHTML = `<div class="search-result-item" style="cursor: default;"><span class="result-name">Không tìm thấy cầu thủ nào</span></div>`;
        searchResults.style.display = "block";
        return;
    }
    
    let html = "";
    players.forEach(p => {
        const photoUrl = p.photo || "https://media.api-sports.io/football/players/fallback.png";
        html += `
            <div class="search-result-item" onclick="selectPlayer(${p.player_id})">
                <img src="${photoUrl}" alt="${p.name}">
                <div class="result-info">
                    <span class="result-name">${p.name}</span>
                    <span class="result-meta">${p.nationality} • Tuổi: ${p.age}</span>
                </div>
            </div>
        `;
    });
    
    searchResults.innerHTML = html;
    searchResults.style.display = "block";
}

// Hide Dropdown when clicking outside
document.addEventListener("click", function(e) {
    if (!e.target.closest(".search-section")) {
        searchResults.style.display = "none";
    }
});

// Select Player and load details
function selectPlayer(playerId) {
    searchResults.style.display = "none";
    searchInput.value = "";
    
    fetch(`${API_URL}/api/player/${playerId}`)
        .then(res => res.json())
        .then(data => {
            currentPlayerId = playerId;
            currentPlayerStats = data.stats;
            
            // Render Profile Info
            renderProfile(data.profile);
            
            // Build Season Tabs
            renderSeasonTabs(data.stats);
            
            // Show Dashboard, Hide Welcome
            welcomePanel.style.display = "none";
            dashboardPanel.style.display = "grid";
        })
        .catch(err => {
            alert("Lỗi tải thông tin cầu thủ: " + err.message);
        });
}

// Render Profile Panel
function renderProfile(profile) {
    document.getElementById("player-name").textContent = profile.name;
    document.getElementById("player-photo").src = profile.photo || "https://media.api-sports.io/football/players/fallback.png";
    document.getElementById("player-age").textContent = profile.age;
    document.getElementById("player-nation").textContent = profile.nationality;
    
    const clubLogo = document.getElementById("player-club-logo");
    const clubName = document.getElementById("player-club-name");
    
    if (profile.team_name) {
        clubLogo.src = profile.team_logo || "";
        clubLogo.style.display = "block";
        clubName.textContent = profile.team_name;
    } else {
        clubLogo.style.display = "none";
        clubName.textContent = "Không CLB (Tự do)";
    }
}

// Render Season Tabs
function renderSeasonTabs(stats) {
    const container = document.getElementById("season-tabs-container");
    container.innerHTML = "";
    
    if (stats.length === 0) {
        container.innerHTML = `<span style="font-size: 0.9rem; color: var(--text-secondary);">Không có dữ liệu thống kê</span>`;
        return;
    }
    
    // Lấy danh sách season duy nhất
    const seasons = [...new Set(stats.map(s => s.season))].sort((a, b) => b - a);
    
    seasons.forEach((season, idx) => {
        const btn = document.createElement("button");
        btn.className = `season-tab-btn ${idx === 0 ? 'active' : ''}`;
        btn.textContent = `Mùa ${season}`;
        btn.onclick = () => {
            document.querySelectorAll(".season-tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            loadSeasonStats(season);
        };
        container.appendChild(btn);
    });
    
    // Mặc định load mùa mới nhất
    loadSeasonStats(seasons[0]);
}

// Load and Display Stats for Selected Season
function loadSeasonStats(season) {
    // Tìm các dòng stats của season này (có thể có nhiều giải đấu như World Cup và League)
    const seasonRecords = currentPlayerStats.filter(s => s.season === season);
    
    if (seasonRecords.length === 0) return;
    
    // Gộp dữ liệu từ các giải đấu trong mùa để hiển thị tổng quan
    let totalAppearances = 0;
    let totalLineups = 0;
    let totalMinutes = 0;
    let sumRatingMinutes = 0;
    let totalGoals = 0;
    let totalAssists = 0;
    let totalPenalties = 0;
    
    let shotsTotal = 0;
    let shotsOn = 0;
    let passesTotal = 0;
    let passesKey = 0;
    let tacklesTotal = 0;
    let tacklesInterceptions = 0;
    let duelsTotal = 0;
    let duelsWon = 0;
    let dribblesAttempts = 0;
    let dribblesSuccess = 0;
    let foulsCommitted = 0;
    let foulsDrawn = 0;
    let cardsYellow = 0;
    let cardsRed = 0;
    
    seasonRecords.forEach(s => {
        totalAppearances += parseInt(s.games_appearances || 0);
        totalLineups += parseInt(s.games_lineups || 0);
        totalMinutes += parseInt(s.games_minutes || 0);
        sumRatingMinutes += parseFloat(s.games_rating || 0) * parseInt(s.games_minutes || 0);
        
        totalGoals += parseInt(s.goals_total || 0);
        totalAssists += parseInt(s.goals_assists || 0);
        totalPenalties += parseInt(s.penalty_scored || 0);
        
        shotsTotal += parseInt(s.shots_total || 0);
        shotsOn += parseInt(s.shots_on || 0);
        passesTotal += parseInt(s.passes_total || 0);
        passesKey += parseInt(s.passes_key || 0);
        tacklesTotal += parseInt(s.tackles_total || 0);
        tacklesInterceptions += parseInt(s.tackles_interceptions || 0);
        duelsTotal += parseInt(s.duels_total || 0);
        duelsWon += parseInt(s.duels_won || 0);
        dribblesAttempts += parseInt(s.dribbles_attempts || 0);
        dribblesSuccess += parseInt(s.dribbles_success || 0);
        foulsCommitted += parseInt(s.fouls_committed || 0);
        foulsDrawn += parseInt(s.fouls_drawn || 0);
        cardsYellow += parseInt(s.cards_yellow || 0);
        cardsRed += parseInt(s.cards_red || 0);
    });
    
    // Tính rating trung bình có trọng số phút thi đấu
    let avgRating = 0;
    if (totalMinutes > 0) {
        avgRating = (sumRatingMinutes / totalMinutes).toFixed(2);
    } else if (seasonRecords.length > 0) {
        // Fallback trung bình thường nếu phút thi đấu bằng 0
        const validRatings = seasonRecords.map(s => parseFloat(s.games_rating || 0)).filter(r => r > 0);
        if (validRatings.length > 0) {
            avgRating = (validRatings.reduce((a, b) => a + b, 0) / validRatings.length).toFixed(2);
        }
    }
    
    // Cập nhật giao diện Stats Grid
    document.getElementById("val-matches").textContent = `${totalAppearances} trận`;
    document.getElementById("val-lineups").textContent = totalLineups;
    document.getElementById("val-minutes").textContent = totalMinutes.toLocaleString();
    
    const ratingEl = document.getElementById("val-rating");
    ratingEl.textContent = avgRating > 0 ? avgRating : "N/A";
    
    document.getElementById("val-goals").textContent = `${totalGoals} bàn`;
    document.getElementById("val-assists").textContent = totalAssists;
    document.getElementById("val-penalties").textContent = totalPenalties;
    
    document.getElementById("val-shots-total").textContent = shotsTotal;
    document.getElementById("val-shots-on").textContent = shotsOn;
    
    // Tỷ lệ sút trúng mục tiêu (accuracy)
    let shotAccuracy = 0;
    if (shotsTotal > 0) {
        shotAccuracy = Math.round((shotsOn / shotsTotal) * 100);
    }
    document.getElementById("pct-shots-accuracy").textContent = `${shotAccuracy}%`;
    document.getElementById("fill-shots-accuracy").style.width = `${shotAccuracy}%`;
    
    document.getElementById("val-passes-total").textContent = passesTotal.toLocaleString();
    document.getElementById("val-passes-key").textContent = passesKey;
    
    document.getElementById("val-tackles-total").textContent = tacklesTotal;
    document.getElementById("val-tackles-interceptions").textContent = tacklesInterceptions;
    
    document.getElementById("val-duels-won").textContent = `${duelsWon}/${duelsTotal}`;
    document.getElementById("val-dribbles-success").textContent = `${dribblesSuccess}/${dribblesAttempts}`;
    
    document.getElementById("val-fouls").textContent = `${foulsCommitted} / ${foulsDrawn}`;
    document.getElementById("val-cards-yellow").textContent = cardsYellow;
    document.getElementById("val-cards-red").textContent = cardsRed;
    
    // Gọi API dự đoán giá trị chuyển nhượng
    loadPrediction(currentPlayerId, season);
}

// Fetch AI prediction
function loadPrediction(playerId, season) {
    const valueAmount = document.getElementById("predicted-value");
    const loader = document.getElementById("value-loader");
    const wcBadge = document.getElementById("wc-badge");
    
    // Reset và hiển thị loading
    valueAmount.style.display = "none";
    loader.style.display = "block";
    wcBadge.style.display = "none";
    
    fetch(`${API_URL}/api/player/${playerId}/predict?season=${season}`)
        .then(res => {
            if (!res.ok) throw new Error("Thất bại");
            return res.json();
        })
        .then(data => {
            if (data.error) {
                valueAmount.textContent = "N/A";
                valueAmount.style.fontSize = "2rem";
            } else {
                valueAmount.textContent = `€${data.predicted_value_m_eur}M`;
                valueAmount.style.fontSize = "2.8rem";
                
                // Hiển thị cờ thưởng World Cup
                if (data.is_wc && data.wc_boost > 1.0) {
                    wcBadge.textContent = `World Cup Boost ${data.wc_boost}x`;
                    wcBadge.style.display = "block";
                }
            }
        })
        .catch(err => {
            valueAmount.textContent = "Error";
            valueAmount.style.fontSize = "2rem";
        })
        .finally(() => {
            loader.style.display = "none";
            valueAmount.style.display = "block";
        });
}
