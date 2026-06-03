// AutoOps 公共JS
// 时钟
function updateClock() {
    const now = new Date();
    const el = document.getElementById("clock");
    if (el) el.textContent = now.toLocaleString("zh-CN");
}
setInterval(updateClock, 1000);
updateClock();

// 通用 fetch 封装
async function api(url, opts = {}) {
    try {
        const res = await fetch(url, {
            headers: {"Content-Type": "application/json"},
            ...opts
        });
        return await res.json();
    } catch (e) {
        console.error("API Error:", e);
        return null;
    }
}

// 进度条颜色
function getBarColor(val) {
    if (val > 90) return "bg-danger";
    if (val > 70) return "bg-warning";
    return "bg-success";
}

// HTML 转义，避免把后端返回内容直接拼进 innerHTML 时带来注入风险
function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
