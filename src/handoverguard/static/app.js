const SHIFT_ID = "SHIFT-NIGHT-2408";

const elements = {
  runButton: document.querySelector("#run-button"),
  resetButton: document.querySelector("#reset-button"),
  issueList: document.querySelector("#issue-list"),
  auditList: document.querySelector("#audit-list"),
  agentSummary: document.querySelector("#agent-summary"),
  unresolvedCount: document.querySelector("#unresolved-count"),
  taskCount: document.querySelector("#task-count"),
  approvalCount: document.querySelector("#approval-count"),
  auditStatus: document.querySelector("#audit-status"),
  auditCount: document.querySelector("#audit-count"),
  duplicateCount: document.querySelector("#duplicate-count"),
  rawNoteCount: document.querySelector("#raw-note-count"),
  chainShort: document.querySelector("#chain-short"),
  toast: document.querySelector("#toast"),
};

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed (${response.status})`);
  }
  return response.json();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function label(value) {
  return value.replaceAll("_", " ");
}

function renderIssues(issues, approvals) {
  if (!issues.length) {
    elements.issueList.innerHTML = '<div class="empty-state">No issues in this shift.</div>';
    return;
  }

  elements.issueList.innerHTML = issues
    .map((issue, index) => {
      const status = issue.duplicate_of ? "duplicate" : issue.status;
      const approval = approvals.find((item) => item.issue_id === issue.id);
      const detail = [issue.department, issue.category, issue.room_label]
        .filter(Boolean)
        .map(label)
        .join(" · ");
      const checkpoint = approval
        ? `<div class="checkpoint checkpoint-${escapeHtml(approval.status)}">
            <div>
              <span class="checkpoint-label">HUMAN CHECKPOINT · ${escapeHtml(label(approval.status))}</span>
              <p>${escapeHtml(approval.reason)}</p>
            </div>
            ${
              approval.status === "pending"
                ? `<div class="checkpoint-actions">
                    <button class="decision decision-reject" data-approval-id="${escapeHtml(approval.id)}" data-decision="reject">Reject</button>
                    <button class="decision decision-approve" data-approval-id="${escapeHtml(approval.id)}" data-decision="approve">Approve</button>
                  </div>`
                : `<span class="decision-proof mono">DECIDED BY ${escapeHtml(approval.decided_by || "human-operator")}</span>`
            }
          </div>`
        : "";
      return `
        <article class="issue">
          <span class="issue-index">${String(index + 1).padStart(2, "0")}</span>
          <div class="issue-copy">
            <strong>${escapeHtml(issue.summary)}</strong>
            <span>${escapeHtml(detail)}</span>
          </div>
          <span class="badge badge-${escapeHtml(status)}">${escapeHtml(label(status))}</span>
          ${checkpoint}
        </article>`;
    })
    .join("");
}

function renderAudit(events) {
  if (!events.length) {
    elements.auditList.innerHTML = '<li class="timeline-empty">No operational events yet.</li>';
    elements.chainShort.textContent = "GENESIS";
    return;
  }
  elements.auditList.innerHTML = events
    .slice()
    .reverse()
    .map(
      (event) => `
      <li>
        <strong>${escapeHtml(label(event.event_type))}</strong>
        <span>#${event.sequence} · ${escapeHtml(event.actor)}</span>
      </li>`,
    )
    .join("");
  elements.chainShort.textContent = events.at(-1).event_hash.slice(0, 10).toUpperCase();
}

function renderSummary(report) {
  const held = report.awaiting_approval_count;
  const tasks = report.tasks.length;
  elements.agentSummary.innerHTML = `
    <p>
      <strong>${tasks} safe internal ${tasks === 1 ? "task" : "tasks"}</strong> created.
      ${held} sensitive ${held === 1 ? "decision is" : "decisions are"} held for a person.
      Duplicate notes are linked, never double-actioned. No issue was silently resolved.
    </p>`;
}

async function refresh() {
  const [report, approvals, audit, events] = await Promise.all([
    request(`/api/shifts/${SHIFT_ID}/handover`),
    request(`/api/shifts/${SHIFT_ID}/approvals`),
    request("/api/audit/verify"),
    request("/api/audit/events"),
  ]);
  renderIssues(report.issues, approvals);
  renderAudit(events);
  renderSummary(report);
  elements.unresolvedCount.textContent = report.unresolved_count;
  elements.taskCount.textContent = report.tasks.length;
  elements.approvalCount.textContent = report.awaiting_approval_count;
  elements.auditStatus.textContent = audit.valid ? "Verified" : "Warning";
  elements.auditCount.textContent = `${audit.event_count} signed operational events`;
  elements.duplicateCount.textContent = report.duplicate_count;
  elements.rawNoteCount.textContent = `${report.raw_note_count} raw notes · ${report.unresolved_count} canonical issues`;
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("toast-visible");
  window.setTimeout(() => elements.toast.classList.remove("toast-visible"), 2600);
}

async function withBusy(button, work) {
  const original = button.innerHTML;
  button.disabled = true;
  button.textContent = "Working…";
  try {
    await work();
  } catch (error) {
    showToast(error.message);
  } finally {
    button.disabled = false;
    button.innerHTML = original;
  }
}

elements.resetButton.addEventListener("click", () =>
  withBusy(elements.resetButton, async () => {
    await request("/api/demo/reset", { method: "POST" });
    await refresh();
    showToast("Synthetic night shift reset.");
  }),
);

elements.runButton.addEventListener("click", () =>
  withBusy(elements.runButton, async () => {
    await request("/api/shifts/process", {
      method: "POST",
      body: JSON.stringify({ shift_id: SHIFT_ID }),
    });
    await refresh();
    showToast("Safe work completed. Human checkpoints preserved.");
  }),
);

elements.issueList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-approval-id]");
  if (!button) return;
  await withBusy(button, async () => {
    const decision = button.dataset.decision;
    await request(`/api/approvals/${button.dataset.approvalId}/decision`, {
      method: "POST",
      body: JSON.stringify({ decision }),
    });
    await refresh();
    showToast(
      decision === "approve"
        ? "Approved. An owned follow-up task was created."
        : "Rejected. The sensitive action remains blocked.",
    );
  });
});

async function boot() {
  try {
    const report = await request(`/api/shifts/${SHIFT_ID}/handover`);
    if (!report.issues.length) {
      await request("/api/demo/reset", { method: "POST" });
    }
    await refresh();
  } catch (error) {
    showToast(error.message);
  }
}

boot();
