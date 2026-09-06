const $ = (selector) => document.querySelector(selector);
const state = { apiUrl: "", runId: "", timer: null, seen: new Set() };

const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (character) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
})[character]);

const serviceClass = (service) => {
  const key = service.toLowerCase();
  if (key.includes("guardrail")) return "guardrail";
  if (key.includes("nova") || key.includes("bedrock")) return "nova";
  if (key.includes("step functions")) return "approval";
  if (key.includes("agentcore")) return "agentcore";
  return "aws";
};

function setStatus(label, kind) {
  const node = $("#status");
  node.textContent = label;
  node.className = `status ${kind}`;
}

function addTrace(step) {
  if (state.seen.has(step.SK)) return;
  state.seen.add(step.SK);
  const trace = $("#trace");
  const wasEmpty = trace.classList.contains("empty");
  trace.classList.remove("empty");
  if (wasEmpty) trace.innerHTML = "";
  const row = document.createElement("article");
  row.className = "trace-row";
  const time = new Date(step.occurred_at).toLocaleTimeString([], { hour12: false });
  row.innerHTML = `<div class="service ${serviceClass(step.service)}">${escapeHtml(step.service)}</div><div><b>${escapeHtml(step.step)}</b><p>${escapeHtml(step.evidence)}</p></div><time>${escapeHtml(time)}</time>`;
  trace.appendChild(row);
  trace.scrollTop = trace.scrollHeight;
}

function renderItems(items) {
  const issues = items.filter((item) => item.entity_type === "ISSUE");
  const tasks = items.filter((item) => item.entity_type === "TASK");
  const approvals = items.filter((item) => item.entity_type === "APPROVAL");
  const pendingApprovals = approvals.filter((item) => item.status === "PENDING");
  const run = items.find((item) => item.entity_type === "RUN");
  const values = [issues.length, tasks.length, approvals.length, 0];
  document.querySelectorAll("#metrics strong").forEach((node, index) => { node.textContent = values[index]; });
  const container = $("#items");
  const cards = [...tasks.map((item) => ({ ...item, route: "INTERNAL TASK", tone: "safe" })), ...approvals.map((item) => ({ ...item, title: item.reason, route: "HUMAN APPROVAL", tone: "hold" }))];
  container.innerHTML = cards.length ? cards.map((item) => {
    const decisions = item.entity_type === "APPROVAL" && item.status === "PENDING"
      ? `<div class="decision-row"><button class="decision approve" data-id="${escapeHtml(item.approval_id)}" data-decision="approve">Approve</button><button class="decision reject" data-id="${escapeHtml(item.approval_id)}" data-decision="reject">Reject</button></div>`
      : "";
    return `<article class="result ${item.tone}"><span>${escapeHtml(item.route)}</span><b>${escapeHtml(item.title)}</b><small>${escapeHtml(item.department || item.status || "Policy enforced")}</small>${decisions}</article>`;
  }).join("") : `<p class="placeholder">Nova is still analyzing the shift…</p>`;
  container.querySelectorAll("button.decision").forEach((button) => {
    button.addEventListener("click", () => decideApproval(button));
  });
  if (pendingApprovals.length) setStatus("AWAITING HUMAN", "running");
  else if (run?.status === "COMPLETED") {
    setStatus("COMPLETE", "complete");
    clearInterval(state.timer);
  }
}

async function decideApproval(button) {
  const siblings = button.closest(".decision-row").querySelectorAll("button");
  siblings.forEach((node) => { node.disabled = true; });
  try {
    const response = await fetch(`${state.apiUrl}/approvals/${button.dataset.id}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ decision: button.dataset.decision }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Decision failed");
    await poll();
  } catch (error) {
    $("#error").textContent = `Decision failed: ${error.message}`;
    siblings.forEach((node) => { node.disabled = false; });
  }
}

async function poll() {
  if (!state.runId) return;
  try {
    const [traceResponse, runResponse] = await Promise.all([
      fetch(`${state.apiUrl}/runs/${state.runId}/trace`),
      fetch(`${state.apiUrl}/runs/${state.runId}`),
    ]);
    const traceData = await traceResponse.json();
    const runData = await runResponse.json();
    traceData.steps.forEach(addTrace);
    renderItems(runData.items);
  } catch (error) {
    $("#error").textContent = `Polling failed: ${error.message}`;
  }
}

async function runDemo() {
  clearInterval(state.timer);
  state.seen.clear();
  $("#trace").className = "trace empty";
  $("#trace").innerHTML = "<p>Submitting the synthetic shift to Amazon API Gateway…</p>";
  $("#items").innerHTML = '<p class="placeholder">Waiting for policy results…</p>';
  $("#error").textContent = "";
  setStatus("RUNNING", "running");
  $("#run").disabled = true;
  try {
    const response = await fetch(`${state.apiUrl}/runs`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ raw_text: $("#handover").value, property_id: "DEMO-RIYADH-01" }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "AWS rejected the run");
    state.runId = data.run_id;
    $("#run-id").textContent = state.runId.slice(0, 12).toUpperCase();
    await poll();
    state.timer = setInterval(poll, 1800);
  } catch (error) {
    setStatus("FAILED", "failed");
    $("#error").textContent = error.message;
  } finally {
    $("#run").disabled = false;
  }
}

fetch("config.json").then((response) => response.json()).then((config) => {
  state.apiUrl = config.apiUrl.replace(/\/$/, "");
  $("#run").addEventListener("click", runDemo);
}).catch(() => { $("#error").textContent = "Demo configuration could not be loaded."; });
