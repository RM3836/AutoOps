// 告警中心 JS
async function loadAlerts() {
    const data = await api("/api/alerts");
    if (!data) return;
    let critical = 0, warning = 0, info = 0;
    data.forEach(a => {
        if (a.level === "CRITICAL") critical++;
        else if (a.level === "WARNING") warning++;
        else info++;
    });
    document.getElementById("critical-count").textContent = critical;
    document.getElementById("warning-count").textContent = warning;
    document.getElementById("info-count").textContent = info;
    document.getElementById("resolved-count").textContent = data.filter(a => a.resolved).length;

    const tb = document.getElementById("alert-list");
    tb.innerHTML = data.map(a => {
        const badge = a.level === "CRITICAL" ? "badge-critical" : (a.level === "WARNING" ? "badge-warning" : "badge-info");
        const stateText = a.resolved ? '<span class="badge bg-success">已处理</span>' : '<span class="badge bg-secondary">未处理</span>';
        const action = a.resolved
            ? '<span class="text-muted">-</span>'
            : `<button class="btn btn-sm btn-outline-light" onclick="resolveAlert(${a.id})">处理</button>`;
        return `<tr>
            <td><span class="badge ${badge}">${escapeHtml(a.level)}</span></td>
            <td>${escapeHtml(a.module)}</td>
            <td>${escapeHtml(a.message)}</td>
            <td>${stateText}</td>
            <td>${escapeHtml(a.time)}</td>
            <td>${action}</td>
        </tr>`;
    }).join("") || '<tr><td colspan="6" class="text-center text-muted">暂无告警</td></tr>';
}

async function resolveAlert(id) {
    const data = await api(`/api/alerts/resolve/${id}`, { method: "POST" });
    if (data && data.ok) {
        loadAlerts();
    } else {
        alert((data && data.message) || "处理失败");
    }
}

// 加载可疑事件分析
async function loadSuspiciousEvents() {
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
    document.getElementById("suspicious-events").innerHTML = html;
}

loadAlerts();
loadSuspiciousEvents();
setInterval(loadAlerts, 10000);
setInterval(loadSuspiciousEvents, 30000);
