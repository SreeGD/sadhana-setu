// Backup / restore view — export to JSON, import from JSON.

import { el, toast, todayISO } from "../util.js";
import * as store from "../store.js";

function download(filename, text) {
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 100);
}

export async function render(root) {
  const s = store.storageSummary();

  const exportBtn = el("button", { class: "primary" }, "Download backup");
  exportBtn.addEventListener("click", () => {
    const data = store.exportAll();
    const json = JSON.stringify(data, null, 2);
    download(`sadhana-setu-backup-${todayISO()}.json`, json);
    toast("Backup downloaded");
    render(root);
  });

  const fileInput = el("input", { type: "file", accept: "application/json,.json", id: "import-file" });
  const strategySel = el("select", { id: "strategy" },
    el("option", { value: "merge" }, "Merge (keep both, later wins)"),
    el("option", { value: "replace" }, "Replace (overwrite everything)"),
  );
  const importBtn = el("button", { class: "secondary" }, "Restore from backup");
  importBtn.addEventListener("click", async () => {
    const file = fileInput.files?.[0];
    if (!file) return toast("Choose a backup file first");
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      const result = store.importAll(data, strategySel.value);
      toast(`Restored ${result.rounds} days, ${result.hearing} notes, ${result.checkins} check-ins`);
      render(root);
    } catch (e) {
      toast("Restore failed: " + e.message);
    }
  });

  const clearBtn = el("button", {
    class: "secondary",
    style: "color:#8B0000; border-color:#FFCCCC;",
  }, "Clear all local data");
  clearBtn.addEventListener("click", () => {
    if (confirm("This deletes ALL tracker data on this device. Are you sure?")) {
      store.clearAll();
      toast("Cleared");
      render(root);
    }
  });

  root.innerHTML = "";

  root.appendChild(el("div", { class: "meta-line" },
    "Backup and restore your tracker data. Your data never leaves your device unless you choose where to save the file."
  ));

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Current data on this device"),
    el("ul", { style: "list-style:none; padding:0;" },
      el("li", {}, el("strong", {}, "Days with rounds recorded: "), String(s.rounds)),
      el("li", {}, el("strong", {}, "Hearing notes: "), String(s.hearing)),
      el("li", {}, el("strong", {}, "Saturday check-ins: "), String(s.checkins)),
      el("li", {}, el("strong", {}, "Storage used: "), `${(s.bytes / 1024).toFixed(1)} KB`),
      el("li", {}, el("strong", {}, "Last export: "),
        s.last_export ? new Date(s.last_export).toLocaleString() : "never"),
      el("li", {}, el("strong", {}, "Last import: "),
        s.last_import ? new Date(s.last_import).toLocaleString() : "never"),
    ),
  ));

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Export — Download backup"),
    el("p", {}, "Emits a JSON file you can save anywhere — Desktop, iCloud Drive, Dropbox, email to yourself, AirDrop to phone. You decide where."),
    el("div", {}, exportBtn),
  ));

  root.appendChild(el("div", { class: "view-card" },
    el("h3", {}, "Import — Restore from backup"),
    el("p", {}, "Restore a backup JSON. Choose merge to keep both sets of data (later edits win), or replace to overwrite everything on this device."),
    el("label", { class: "field" }, "Backup file"),
    fileInput,
    el("label", { class: "field" }, "Strategy"),
    strategySel,
    el("div", { style: "margin-top:0.8rem;" }, importBtn),
  ));

  root.appendChild(el("div", { class: "view-card", style: "border-left-color: #8B0000;" },
    el("h3", { style: "color:#8B0000;" }, "Clear local data"),
    el("p", {}, "Removes all rounds, hearing notes, and check-ins from this browser. Content libraries are unaffected. Use this if you've moved to a new device and don't need the old data."),
    el("div", {}, clearBtn),
  ));
}
