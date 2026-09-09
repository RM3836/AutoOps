// SSH 远程运维 JS
let selectedHostId = null;

async function loadHosts() {
    const data = await api("/api/ssh/hosts");
    if (!data) return;
    const el = document.getElementById("host-list");
    el.innerHTML = data.map(h =>
        `<div class="list-group-item list-group-item-action ${h.id===selectedHostId?"active":""}">
            <div onclick="selectHost(${h.id},'${escapeHtml(h.hostname)}')" style="cursor:pointer">
                <strong>${escapeHtml(h.hostname)}</strong>
                <span class="text-muted float-end">${escapeHtml(h.username)}@${escapeHtml(h.hostname)}:${escapeHtml(h.port)}</span>
                <br><small class="text-muted">${escapeHtml(h.desc||"无描述")}</small>
            </div>
            <button class="btn btn-sm btn-outline-danger mt-1" onclick="event.stopPropagation();deleteHost(${h.id})">删除</button>
        </div>`
    ).join("") || '<div class="text-muted p-3">暂无服务器，请点击"添加"</div>';
}

function selectHost(id, hostname) {
    selectedHostId = id;
    document.getElementById("current-host").textContent = hostname;
    document.getElementById("cmd-input").disabled = false;
    document.getElementById("exec-btn").disabled = false;
    document.getElementById("cmd-input").focus();
    loadHosts();
}

async function deleteHost(id) {
    if (!confirm("确定删除该服务器？")) return;
    await api(`/api/ssh/delete/${id}`, { method: "DELETE" });
    if (selectedHostId === id) {
        selectedHostId = null;
        document.getElementById("current-host").textContent = "未选择";
        document.getElementById("cmd-input").disabled = true;
        document.getElementById("exec-btn").disabled = true;
    }
    loadHosts();
}

async function execCommand() {
    const cmd = document.getElementById("cmd-input").value.trim();
    if (!cmd || !selectedHostId) return;
    const out = document.getElementById("terminal-output");
    out.innerHTML += `<div class="text-success">\n$ ${escapeHtml(cmd)}</div>`;
    out.innerHTML += '<div class="text-warning">执行中...</div>';
    out.scrollTop = out.scrollHeight;
    const data = await api("/api/ssh/exec", {
        method: "POST",
        body: JSON.stringify({host_id: selectedHostId, command: cmd})
    });
    // 移除"执行中"
    out.lastChild.remove();
    if (data && data.result) {
        out.innerHTML += `<div>${escapeHtml(data.result)}</div>`;
    } else {
        out.innerHTML += '<div class="text-danger">执行失败</div>';
    }
    out.scrollTop = out.scrollHeight;
    document.getElementById("cmd-input").value = "";
}

// 事件绑定
document.getElementById("exec-btn").addEventListener("click", execCommand);
document.getElementById("cmd-input").addEventListener("keydown", e => {
    if (e.key === "Enter") execCommand();
});

// 快捷命令
document.querySelectorAll(".quick-cmd").forEach(btn => {
    btn.addEventListener("click", () => {
        document.getElementById("cmd-input").value = btn.dataset.cmd;
        execCommand();
    });
});

// 添加主机
document.getElementById("save-host").addEventListener("click", async () => {
    const d = {
        hostname: document.getElementById("add-host").value,
        port: parseInt(document.getElementById("add-port").value) || 22,
        username: document.getElementById("add-user").value,
        password: document.getElementById("add-pass").value,
        description: document.getElementById("add-desc").value,
    };
    if (!d.hostname || !d.username || !d.password) { alert("请填写完整信息"); return; }
    await api("/api/ssh/add", {method: "POST", body: JSON.stringify(d)});
    bootstrap.Modal.getInstance(document.getElementById("addModal")).hide();
    loadHosts();
});

loadHosts();
