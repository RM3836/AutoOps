// 日志分析 JS
async function loadLogs() {
    const data = await api("/api/logs");
    if (!data) return;
    const el = document.getElementById("log-viewer");
    el.innerHTML = data.map(line => {
        let cls = "log-line";
        if (line.includes("ERROR") || line.includes("CRITICAL")) cls += " error";
        else if (line.includes("WARNING")) cls += " warning";
        else if (line.includes("INFO")) cls += " info";
        return `<div class="${cls}">${escapeHtml(line)}</div>`;
    }).join("") || '<div class="text-muted">暂无日志</div>';
    el.scrollTop = el.scrollHeight;
}

async function analyzeLogs() {
    document.getElementById("security-result").innerHTML = '<div class="text-info">分析中...</div>';
    const data = await api("/api/logs/analyze");
    if (!data) return;
    let html = "";
    html += `<div class="mb-2"><strong>可疑事件: ${data.total_suspicious} 条</strong></div>`;
    if (data.auth_alerts && data.auth_alerts.length) {
        html += data.auth_alerts.map(a =>
            `<div class="mb-1"><span class="badge badge-${a.level==="CRITICAL"?"critical":"warning"}">${escapeHtml(a.level)}</span> ${escapeHtml(a.message)}</div>`
        ).join("");
    } else {
        html += '<div class="text-success">✅ 未发现安全问题</div>';
    }
    document.getElementById("security-result").innerHTML = html;
}

document.getElementById("analyze-btn").addEventListener("click", analyzeLogs);

// 日志统计图 - 初始为空，等数据加载后更新
const logCtx = document.getElementById("logChart").getContext("2d");
const logChart = new Chart(logCtx, {
    type: "doughnut",
    data: {
        labels: ["INFO", "WARNING", "ERROR", "CRITICAL"],
        datasets: [{ data: [0, 0, 0, 0], backgroundColor: ["#1f6feb","#d29922","#da3633","#8b949e"] }]
    },
    options: { 
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#c9d1d9" } } } 
    }
});

// 加载真实日志统计数据
async function loadLogStats() {
    const data = await api("/api/logs");
    if (!data) return;
    // 统计各级别数量
    let counts = {INFO: 0, WARNING: 0, ERROR: 0, CRITICAL: 0};
    if (Array.isArray(data)) {
        data.forEach(line => {
            if (line.includes("CRITICAL")) counts.CRITICAL++;
            else if (line.includes("ERROR")) counts.ERROR++;
            else if (line.includes("WARNING")) counts.WARNING++;
            else counts.INFO++;
        });
    }
    logChart.data.datasets[0].data = [counts.INFO, counts.WARNING, counts.ERROR, counts.CRITICAL];
    logChart.update("none");
}

loadLogs();
loadLogStats();
setInterval(loadLogs, 10000);
