const API_URL = "";
let token = localStorage.getItem("token");
let chartInstance = null;

// Init
document.addEventListener("DOMContentLoaded", () => {
    if (token) {
        showApp();
    } else {
        document.getElementById("login-modal").style.display = "flex";
    }
});

// Auth
async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    // Using FormData for OAuth2 standard
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
        const res = await fetch("/auth/token", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });

        if (!res.ok) throw new Error("Invalid credentials");

        const data = await res.json();
        token = data.access_token;
        localStorage.setItem("token", token);
        showApp();
    } catch (e) {
        document.getElementById("auth-error").innerText = e.message;
    }
}

async function register() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const res = await fetch("/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });
        if (res.ok) {
            alert("Registered! Please login.");
        } else {
            const d = await res.json();
            alert(d.detail);
        }
    } catch (e) {
        alert("Error registering");
    }
}

function logout() {
    localStorage.removeItem("token");
    location.reload();
}

function showApp() {
    document.getElementById("login-modal").style.display = "none";
    document.getElementById("app").classList.remove("hidden");
    updateDashboard();
    updateWatchlist();
}

// Dashboard
async function updateDashboard() {
    const country = document.getElementById("country-selector").value;
    const res = await fetch(`/market/indexes?country=${country}`);
    const data = await res.json();

    const grid = document.getElementById("indexes-grid");
    grid.innerHTML = "";

    // Update Chart Selector based on available indexes
    const chartSelect = document.getElementById("chart-symbol");
    chartSelect.innerHTML = "";

    data.forEach((idx, i) => {
        // Add card
        const card = document.createElement("div");
        card.className = "card index-card";
        const isUp = idx.change >= 0;
        card.innerHTML = `
            <h4>${idx.name}</h4>
            <div class="price">${idx.price.toLocaleString()}</div>
            <div class="change ${isUp ? 'up' : 'down'}">
                ${isUp ? '▲' : '▼'} ${idx.change} (${idx.percent}%)
            </div>
        `;
        grid.appendChild(card);

        // Add to chart selector
        const opt = document.createElement("option");
        opt.value = idx.symbol;
        opt.innerText = idx.name;
        chartSelect.appendChild(opt);

        // Load chart for first item by default
        if (i === 0) updateChart(idx.symbol);
    });
}

// Chart
async function updateChart(symbolOverride) {
    const symbol = symbolOverride || document.getElementById("chart-symbol").value;
    if (!symbol) return;

    const res = await fetch(`/market/chart/${symbol}`);
    const data = await res.json();

    const ctx = document.getElementById("marketChart").getContext("2d");
    const labels = data.map(d => d.date);
    const prices = data.map(d => d.price);

    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: symbol,
                data: prices,
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.1)',
                tension: 0.1,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { display: false },
                y: { grid: { color: '#30363d' } }
            }
        }
    });
}

// Watchlist
async function updateWatchlist() {
    const res = await fetch("/watchlist", {
        headers: { "Authorization": `Bearer ${token}` }
    });
    const list = await res.json();
    const ul = document.getElementById("watchlist-list");
    ul.innerHTML = "";

    list.forEach(symbol => {
        const li = document.createElement("li");
        li.innerText = symbol;
        ul.appendChild(li);
    });
}

async function addToWatchlist() {
    const symbol = document.getElementById("new-stock").value.toUpperCase();
    if (!symbol) return;

    await fetch(`/watchlist?symbol=${symbol}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` }
    });
    document.getElementById("new-stock").value = "";
    updateWatchlist();
}

// Chat
async function sendMessage() {
    const input = document.getElementById("chat-input");
    const text = input.value;
    if (!text) return;

    addMessage(text, "user");
    input.value = "";

    // Initial loading state
    const loadingId = addMessage("Thinking...", "bot");

    try {
        const res = await fetch("/agent/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ message: text })
        });
        const data = await res.json();

        // Remove loading
        document.getElementById(loadingId).remove();

        // Convert markdown to text (simple replacement for demo)
        const cleanText = data.response.replace(/\*\*/g, "").replace(/##/g, "").replace(/\n/g, "<br>");
        addMessage(cleanText, "bot", true);
    } catch (e) {
        document.getElementById(loadingId).innerText = "Error contacting agent.";
    }
}

function addMessage(text, role, isHtml = false) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    div.id = "msg-" + Date.now();
    if (isHtml) div.innerHTML = text;
    else div.innerText = text;

    const history = document.getElementById("chat-history");
    history.appendChild(div);
    history.scrollTo(0, history.scrollHeight);
    return div.id;
}

function handleChat(e) {
    if (e.key === "Enter") sendMessage();
}
