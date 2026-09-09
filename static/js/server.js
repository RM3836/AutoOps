// 服务器详情页 JS
let memChart = null;

function esc(s) {
    return escapeHtml(String(s ?? "--"));
}

function fmtNum(n, unit) {
    if (n === null || n === undefined) return "--";
    return n.toLocaleString("zh-CN") + (unit || "");
}

// ===== CPU =====
function renderCPU(cpu) {
    if (!cpu) return;
    setText("cpu-model", cpu.model);
    setText("cpu-physical", cpu.physical_cores + " 核");
    setText("cpu-logical", cpu.logical_cores + " 核");
    setText("cpu-freq-cur", cpu.freq_current + " MHz");
    setText("cpu-freq-max", cpu.freq_max > 0 ? cpu.freq_max + " MHz" : "--");

    const badge = document.getElementById("cpu-usage-badge");
    if (badge) badge.textContent = "总使用率 " + cpu.usage_total + "%";

    // 各核心使用率 — grid 小方块
    const container = document.getElementById("cpu-cores");
    if (container && cpu.usage_per_core) {
        let html = "";
        cpu.usage_per_core.forEach((val, i) => {
            const color = val > 90 ? "#dc3545" : val > 70 ? "#ffc107" : val > 30 ? "#0d6efd" : "#198754";
            html += `<div style="text-align:center;font-size:12px;border-radius:4px;padding:4px 2px;background:${color}18;border:1px solid ${color}40" title="核心${i}: ${val}%">
                <div style="color:${color};font-weight:700;font-variant-numeric:tabular-nums">${val}%</div>
                <div style="color:#889;font-size:10px">#${i}</div>
            </div>`;
        });
        container.innerHTML = html;
    }
}

// ===== 内存 =====
function renderMemory(mem) {
    if (!mem) return;
    setText("mem-total", mem.total_gb + " GB");
    setText("mem-used", mem.used_gb + " GB");
    setText("mem-avail", mem.available_gb + " GB");
    setText("mem-percent", mem.percent + "%");
    setText("mem-buffers", mem.buffers_mb + " MB");
    setText("mem-cached", mem.cached_mb + " MB");
    setText("swap-total", mem.swap_total_gb > 0 ? mem.swap_total_gb + " GB" : "无");
    setText("swap-used", mem.swap_total_gb > 0 ? mem.swap_used_gb + " GB (" + mem.swap_percent + "%)" : "--");

    const badge = document.getElementById("mem-usage-badge");
    if (badge) badge.textContent = "使用率 " + mem.percent + "%";

    // 环形图
    const ctx = document.getElementById("memChart");
    if (!ctx) return;
    const used = mem.used_gb;
    const buffers = mem.buffers_mb / 1024;
    const cached = mem.cached_mb / 1024;
    const free = mem.total_gb - used;

    if (!memChart) {
        memChart = new Chart(ctx.getContext("2d"), {
            type: "doughnut",
            data: {
                labels: ["应用占用", "Buffers", "Cached", "空闲"],
                datasets: [{
                    data: [Math.max(used - buffers - cached, 0), buffers, cached, Math.max(free, 0)],
                    backgroundColor: ["#dc3545", "#ffc107", "#0d6efd", "#198754"],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "65%",
                plugins: {
                    legend: { display: false }
                }
            }
        });
    } else {
        memChart.data.datasets[0].data = [
            Math.max(used - buffers - cached, 0), buffers, cached, Math.max(free, 0)
        ];
        memChart.update("none");
    }
}

// ===== 磁盘分区 =====
function renderDisk(partitions) {
    const tb = document.getElementById("disk-table");
    if (!tb || !partitions) return;
    if (partitions.length === 0) {
        tb.innerHTML = '<tr><td colspan="10" class="text-muted">无分区信息</td></tr>';
        return;
    }
    tb.innerHTML = partitions.map(p => {
        const barColor = p.percent > 90 ? "bg-danger" : p.percent > 70 ? "bg-warning" : "bg-success";
        return `<tr>
            <td>${esc(p.mountpoint)}</td>
            <td>${esc(p.device)}</td>
            <td>${esc(p.fstype)}</td>
            <td>${p.total_gb} GB</td>
            <td>${p.used_gb} GB</td>
            <td>${p.free_gb} GB</td>
            <td><div class="progress" style="height:16px;min-width:80px"><div class="progress-bar ${barColor}" style="width:${p.percent}%">${p.percent}%</div></div></td>
            <td>${fmtNum(p.inodes_total)}</td>
            <td>${fmtNum(p.inodes_used)}</td>
            <td>${fmtNum(p.inodes_free)}</td>
        </tr>`;
    }).join("");
}

// ===== 网卡 =====
function renderNetwork(interfaces) {
    const tb = document.getElementById("net-table");
    if (!tb || !interfaces) return;
    if (interfaces.length === 0) {
        tb.innerHTML = '<tr><td colspan="8" class="text-muted">无网卡信息</td></tr>';
        return;
    }
    tb.innerHTML = interfaces.map(nic => `<tr>
        <td><strong>${esc(nic.name)}</strong></td>
        <td>${esc(nic.ipv4)}</td>
        <td>${nic.bytes_sent_mb}</td>
        <td>${nic.bytes_recv_mb}</td>
        <td>${fmtNum(nic.packets_sent)}</td>
        <td>${fmtNum(nic.packets_recv)}</td>
        <td class="${nic.errin > 0 ? 'text-danger' : ''}">${nic.errin}</td>
        <td class="${nic.errout > 0 ? 'text-danger' : ''}">${nic.errout}</td>
    </tr>`).join("");
}

// ===== 磁盘IO =====
function renderIO(ioList) {
    const tb = document.getElementById("io-table");
    if (!tb || !ioList) return;
    if (ioList.length === 0) {
        tb.innerHTML = '<tr><td colspan="7" class="text-muted">无IO信息</td></tr>';
        return;
    }
    tb.innerHTML = ioList.map(io => `<tr>
        <td><strong>${esc(io.device)}</strong></td>
        <td>${fmtNum(io.read_count)}</td>
        <td>${fmtNum(io.write_count)}</td>
        <td>${io.read_mb}</td>
        <td>${io.write_mb}</td>
        <td>${fmtNum(io.read_time_ms)}</td>
        <td>${fmtNum(io.write_time_ms)}</td>
    </tr>`).join("");
}

// ===== 工具函数 =====
function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val ?? "--";
}

// ===== 主加载 =====
async function loadServerInfo() {
    const data = await api("/api/server/info");
    if (!data) return;
    renderCPU(data.cpu_info);
    renderMemory(data.memory_info);
    renderDisk(data.disk_info);
    renderNetwork(data.network_info);
    renderIO(data.io_info);
}

// 首次加载 + 5秒刷新
loadServerInfo();
setInterval(loadServerInfo, 5000);
