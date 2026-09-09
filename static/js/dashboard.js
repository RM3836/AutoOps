// 仪表盘 JS - 防抖动优化版
const chartLabels = [];
const cpuData = [];
const memData = [];
const diskData = [];

const ctx = document.getElementById("trendChart").getContext("2d");
const trendChart = new Chart(ctx, {
    type: "line",
    data: {
        labels: chartLabels,
        datasets: [
            { label: "CPU%", data: cpuData, borderColor: "#00d4aa", backgroundColor: "rgba(0,212,170,0.1)", fill: true, tension: 0.3 },
            { label: "内存%", data: memData, borderColor: "#58a6ff", backgroundColor: "rgba(88,166,255,0.1)", fill: true, tension: 0.3 },
            { label: "磁盘%", data: diskData, borderColor: "#d29922", backgroundColor: "rgba(210,153,34,0.1)", fill: true, tension: 0.3 },
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 500,
            easing: 'easeInOutQuart'
        },
        scales: {
            y: { min: 0, max: 100, grid: { color: "#1a2740" }, ticks: { color: "#8899aa" } },
            x: { grid: { color: "#1a2740" }, ticks: { color: "#8899aa", maxTicksLimit: 10 } }
        },
        plugins: { legend: { labels: { color: "#c9d1d9" } } }
    }
});

function updateCard(id, val) {
    const el = document.getElementById(id);
    if (!el) return;
    const newText = typeof val === "number" ? val + "%" : val;
    if (el.textContent !== newText) {
        el.textContent = newText;
    }
}

function updateElement(id, val) {
    const el = document.getElementById(id);
    if (el && el.textContent !== val) {
        el.textContent = val;
    }
}

async function loadStatus() {
    const d = await api("/api/status");
    if (!d) return;

    // 只在值变化时更新，减少 DOM 操作
    updateCard("cpu-val", d.cpu);
    updateCard("mem-val", d.memory);
    updateCard("disk-val", d.disk);
    updateElement("proc-val", String(d.process_count));

    // 进度条 - CSS transition 会自动平滑
    const cpuBar = document.getElementById("cpu-bar");
    const memBar = document.getElementById("mem-bar");
    const diskBar = document.getElementById("disk-bar");

    if (cpuBar) cpuBar.style.width = d.cpu + "%";
    if (memBar) memBar.style.width = d.memory + "%";
    if (diskBar) diskBar.style.width = d.disk + "%";

    // 只在 class 变化时更新
    const cpuClass = "progress-bar " + getBarColor(d.cpu);
    const memClass = "progress-bar " + getBarColor(d.memory);
    const diskClass = "progress-bar " + getBarColor(d.disk);

    if (cpuBar && cpuBar.className !== cpuClass) cpuBar.className = cpuClass;
    if (memBar && memBar.className !== memClass) memBar.className = memClass;
    if (diskBar && diskBar.className !== diskClass) diskBar.className = diskClass;

    // 静态信息 - 只更新一次或值变化时
    updateElement("cpu-count", String(d.cpu_count));
    updateElement("mem-total", d.memory_total + " GB");
    updateElement("disk-total", d.disk_total + " GB");
    updateElement("net-sent", d.network_sent + " MB");
    updateElement("net-recv", d.network_recv + " MB");
    updateElement("sys-platform", d.platform);
    updateElement("platform-info", d.platform);

    // 图表数据
    const now = new Date().toLocaleTimeString("zh-CN", {hour:"2-digit",minute:"2-digit",second:"2-digit"});
    chartLabels.push(now);
    cpuData.push(d.cpu);
    memData.push(d.memory);
    diskData.push(d.disk);
    if (chartLabels.length > 30) { chartLabels.shift(); cpuData.shift(); memData.shift(); diskData.shift(); }
    trendChart.update('none'); // 'none' 模式减少动画
}

// 智能表格更新 - 只更新变化的单元格，避免 innerHTML 整体重排
async function loadProcesses() {
    const data = await api("/api/processes");
    if (!data) return;

    const tb = document.getElementById("proc-table");
    if (!tb) return;

    // 先调整行数：删多余 / 补不足
    while (tb.children.length > data.length) {
        tb.removeChild(tb.lastChild);
    }
    while (tb.children.length < data.length) {
        const row = document.createElement("tr");
        row.innerHTML = "<td></td><td></td><td></td><td></td>";
        tb.appendChild(row);
    }

    // 重新获取行引用（DOM 已变化），逐格对比更新
    const rows = tb.children;
    for (let i = 0; i < data.length; i++) {
        const p = data[i];
        const cells = rows[i].children;
        const pid = String(p.pid);
        const name = p.name || "--";
        const cpu = (p.cpu_percent || 0).toFixed(1);
        const mem = (p.memory_percent || 0).toFixed(1);

        if (cells[0].textContent !== pid) cells[0].textContent = pid;
        if (cells[1].textContent !== name) cells[1].textContent = name;
        if (cells[2].textContent !== cpu) cells[2].textContent = cpu;
        if (cells[3].textContent !== mem) cells[3].textContent = mem;
    }
}

async function loadAlerts() {
    const data = await api("/api/alerts");
    if (!data) return;

    const tb = document.getElementById("alert-table");
    if (!tb) return;

    const newHtml = data.slice(0, 10).map(a =>
        `<tr><td><span class="badge badge-${a.level==="CRITICAL"?"critical":"warning"}">${a.level}</span></td><td>${a.module}</td><td>${a.message}</td><td>${a.time}</td></tr>`
    ).join("");

    // 只在内容变化时更新
    if (tb.innerHTML !== newHtml) {
        tb.innerHTML = newHtml;
    }
}

// 初始化 - 先加载历史数据，再启动实时刷新
async function init() {
    // 加载历史数据填充图表
    const history = await api("/api/history");
    if (history && history.length) {
        history.forEach(h => {
            const t = h.time ? h.time.split(" ")[1] || h.time : "";
            chartLabels.push(t);
            cpuData.push(h.cpu);
            memData.push(h.memory);
            diskData.push(h.disk);
        });
        trendChart.update("none");
    }
    loadStatus();
    loadProcesses();
    loadAlerts();
    setInterval(loadStatus, 2000);
    setInterval(loadProcesses, 5000);
    setInterval(loadAlerts, 10000);
}
init();
