// 运维工具箱 JS

// ===== 主机Ping =====
document.getElementById("ping-mode").addEventListener("change", function() {
    document.getElementById("ping-list-input").style.display = this.value === "list" ? "" : "none";
    document.getElementById("ping-subnet-input").style.display = this.value === "subnet" ? "" : "none";
});

document.getElementById("ping-btn").addEventListener("click", async function() {
    this.disabled = true; this.textContent = "扫描中...";
    const mode = document.getElementById("ping-mode").value;
    let body;
    if (mode === "subnet") {
        body = { mode: "subnet", subnet: document.getElementById("ping-subnet").value,
                 start: parseInt(document.getElementById("ping-start").value),
                 end: parseInt(document.getElementById("ping-end").value) };
    } else {
        const hosts = document.getElementById("ping-hosts").value.trim().split("\n").filter(h => h.trim());
        body = { mode: "list", hosts: hosts };
    }
    const data = await api("/api/tools/ping", {method:"POST", body:JSON.stringify(body)});
    const tb = document.getElementById("ping-result");
    if (data && data.length) {
        const alive = data.filter(d => d.alive).length;
        tb.innerHTML = `<tr><td colspan="2" class="text-info">共 ${data.length} 台，存活 ${alive} 台</td></tr>` +
            data.map(d => `<tr><td>${escapeHtml(d.host)}</td><td>${d.alive ? '<span class="text-success">✅ 在线</span>' : '<span class="text-danger">❌ 离线</span>'}</td></tr>`).join("");
    }
    this.disabled = false; this.textContent = "🔍 开始扫描";
});

// ===== 端口扫描 =====
document.getElementById("port-btn").addEventListener("click", async function() {
    this.disabled = true;
    const host = document.getElementById("port-host").value;
    const ports = document.getElementById("port-list").value.split(",").map(Number);
    const data = await api("/api/tools/portscan", {method:"POST", body:JSON.stringify({host, ports})});
    const tb = document.getElementById("port-result");
    if (data && data.ports) {
        tb.innerHTML = data.ports.map(p =>
            `<tr><td>${escapeHtml(p.port)}</td><td>${escapeHtml(p.service)}</td><td>${p.status === "open" ? '<span class="text-success">开放</span>' : '<span class="text-danger">关闭</span>'}</td></tr>`
        ).join("");
    }
    this.disabled = false;
});

// ===== DNS解析 =====
document.getElementById("dns-btn").addEventListener("click", async function() {
    const domain = document.getElementById("dns-domain").value.trim();
    if (!domain) return;
    const data = await api("/api/tools/dns", {method:"POST", body:JSON.stringify({domain})});
    const el = document.getElementById("dns-result");
    if (data) {
        let html = `<h5 class="text-info mb-3">${escapeHtml(domain)}</h5>`;
        if (data.A && data.A.length) {
            html += "<p><strong>A 记录 (IP地址):</strong></p><ul>" + data.A.map(ip => `<li>${escapeHtml(ip)}</li>`).join("") + "</ul>";
        }
        if (data.NS && data.NS.length) {
            html += "<p><strong>NS 记录 (域名服务器):</strong></p><ul>" + data.NS.map(ns => `<li>${escapeHtml(ns)}</li>`).join("") + "</ul>";
        }
        if (data.MX && data.MX.length) {
            html += "<p><strong>MX 记录 (邮件服务器):</strong></p><ul>" + data.MX.map(mx => `<li>${escapeHtml(mx)}</li>`).join("") + "</ul>";
        }
        if (data.CNAME && data.CNAME.length) {
            html += "<p><strong>CNAME 记录 (别名):</strong></p><ul>" + data.CNAME.map(c => `<li>${escapeHtml(c)}</li>`).join("") + "</ul>";
        }
        if (data.error) html += `<p class="text-danger">错误: ${escapeHtml(data.error)}</p>`;
        if (!data.A?.length && !data.NS?.length && !data.MX?.length && !data.CNAME?.length) {
            html += '<p class="text-muted">未找到解析记录</p>';
        }
        el.innerHTML = html;
    }
});

// ===== 进程管理 =====
async function loadProcList(sort) {
    sort = sort || "cpu";
    const data = await api(`/api/tools/processes?sort=${sort}&limit=30`);
    const tb = document.getElementById("proc-list");
    if (!data) return;
    tb.innerHTML = data.map(p => `
        <tr>
            <td>${escapeHtml(p.pid)}</td><td>${escapeHtml(p.name||"--")}</td><td>${escapeHtml(p.username||"--")}</td>
            <td>${escapeHtml((p.cpu_percent||0).toFixed(1))}</td><td>${escapeHtml((p.memory_percent||0).toFixed(1))}</td>
            <td>${escapeHtml(p.status||"--")}</td>
            <td><button class="btn btn-sm btn-danger" onclick="killProc(${p.pid},'${escapeHtml(p.name||"")}')">终止</button></td>
        </tr>
    `).join("");
}

async function killProc(pid, name) {
    if (!confirm(`确认终止进程 ${name} (PID: ${pid})?`)) return;
    const data = await api("/api/tools/kill", {method:"POST", body:JSON.stringify({pid})});
    if (data) {
        alert(data.message);
        loadProcList();
    }
}

// ===== 报告导出（直接下载文件） =====
document.getElementById("gen-report-btn").addEventListener("click", function() {
    document.getElementById("export-status").textContent = "正在生成报告...";
    window.location.href = "/api/tools/report";
    setTimeout(() => {
        document.getElementById("export-status").textContent = "✅ HTML报告已开始下载";
    }, 1000);
});

document.getElementById("export-csv-btn").addEventListener("click", function() {
    document.getElementById("export-status").textContent = "正在导出数据...";
    window.location.href = "/api/tools/export/csv";
    setTimeout(() => {
        document.getElementById("export-status").textContent = "✅ CSV文件已开始下载";
    }, 1000);
});

// 初始化
loadProcList();
