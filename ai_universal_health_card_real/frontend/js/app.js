const API = "";
let accessToken = localStorage.getItem("access_token");

function showPage(id) {
  document.querySelectorAll(".page").forEach(x => x.classList.add("d-none"));
  document.getElementById(id).classList.remove("d-none");
}
function authHeaders(json=true) {
  const h = {};
  if (json) h["Content-Type"] = "application/json";
  if (accessToken) h["Authorization"] = `Bearer ${accessToken}`;
  return h;
}
async function api(path, options={}) {
  options.headers = {...authHeaders(!(options.body instanceof FormData)), ...(options.headers || {})};
  const r = await fetch(API + path, options);
  const text = await r.text();
  let data = {};
  try { data = JSON.parse(text); } catch { data = {detail:text}; }
  if (!r.ok) throw new Error(data.detail || "Request failed");
  return data;
}

document.getElementById("registerForm").addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const data = await api("/api/auth/register", {method:"POST", body: JSON.stringify({
      full_name:f.get("full_name"), email:f.get("email"), phone:f.get("phone"), password:f.get("password"), role:"patient"
    })});
    accessToken = data.access_token;
    localStorage.setItem("access_token", accessToken);
    document.getElementById("registerMsg").innerHTML = '<div class="alert alert-success">Registered. Configure SMTP for real email verification; you can continue to the dashboard.</div>';
    showPage("dashboard"); loadDashboard();
  } catch(e) { document.getElementById("registerMsg").innerHTML = `<div class="alert alert-danger">${e.message}</div>`; }
});

document.getElementById("loginForm").addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target);
  try {
    const data = await api("/api/auth/login", {method:"POST", body: JSON.stringify({email:f.get("email"), password:f.get("password")})});
    accessToken = data.access_token;
    localStorage.setItem("access_token", accessToken);
    showPage("dashboard"); loadDashboard();
  } catch(e) { document.getElementById("loginMsg").innerHTML = `<div class="alert alert-danger">${e.message}</div>`; }
});

async function loadDashboard() {
  try {
    const d = await api("/api/patient/dashboard");
    document.getElementById("dashboardCards").innerHTML = `
      <div class="col-md-3"><div class="card p-3"><small>Card ID</small><b>${d.card_id}</b></div></div>
      <div class="col-md-3"><div class="card p-3"><small>Patient</small><b>${d.full_name}</b></div></div>
      <div class="col-md-3"><div class="card p-3"><small>Blood Group</small><b>${d.blood_group || "Not set"}</b></div></div>
      <div class="col-md-3"><div class="card p-3"><small>Reports</small><b>${d.reports_count}</b></div></div>`;
    const p = await api("/api/patient/profile");
    const pf = document.getElementById("profileForm");
    Object.entries(p.profile || {}).forEach(([k,v]) => {
      if (pf.elements[k] && v != null) pf.elements[k].value = v;
    });
    const h = await api("/api/patient/history");
    if (h) {
      document.getElementById("diseases").value = (h.diseases||[]).join(", ");
      document.getElementById("allergies").value = (h.allergies||[]).join(", ");
      document.getElementById("medications").value = (h.current_medications||[]).join(", ");
      document.getElementById("surgeries").value = (h.surgery_history||[]).join(", ");
      document.getElementById("vaccines").value = (h.vaccination_records||[]).join(", ");
      document.getElementById("notes").value = h.notes || "";
    }
    await loadReports();
  } catch(e) {
    if (accessToken) { localStorage.removeItem("access_token"); accessToken=null; showPage("login"); }
  }
}

document.getElementById("profileForm").addEventListener("submit", async e => {
  e.preventDefault();
  const f = new FormData(e.target), body = {};
  for (const [k,v] of f.entries()) if (v !== "") body[k] = v;
  try { await api("/api/patient/profile", {method:"PUT", body:JSON.stringify(body)}); document.getElementById("profileMsg").innerHTML='<span class="text-success">Profile saved.</span>'; loadDashboard(); }
  catch(e) { document.getElementById("profileMsg").innerHTML=`<span class="text-danger">${e.message}</span>`; }
});

async function saveHistory() {
  const arr = id => document.getElementById(id).value.split(",").map(x=>x.trim()).filter(Boolean);
  try {
    await api("/api/patient/history", {method:"PUT", body:JSON.stringify({
      diseases:arr("diseases"), allergies:arr("allergies"), current_medications:arr("medications"),
      surgery_history:arr("surgeries"), vaccination_records:arr("vaccines"), insurance_details:{}, notes:document.getElementById("notes").value
    })});
    document.getElementById("historyMsg").innerHTML='<span class="text-success">Medical history saved.</span>';
  } catch(e) { document.getElementById("historyMsg").innerHTML=`<span class="text-danger">${e.message}</span>`; }
}

document.getElementById("reportForm").addEventListener("submit", async e => {
  e.preventDefault();
  try {
    const data = await api("/api/reports/upload", {method:"POST", body:new FormData(e.target)});
    document.getElementById("reportMsg").innerHTML=`<div class="alert alert-success">Uploaded report #${data.id}. Extracted text: ${data.extracted_text_characters} characters.</div>`;
    e.target.reset(); await loadReports();
  } catch(e) { document.getElementById("reportMsg").innerHTML=`<div class="alert alert-danger">${e.message}</div>`; }
});

async function loadReports() {
  const rows = await api("/api/reports");
  document.getElementById("reportsList").innerHTML = rows.length ? rows.map(r =>
    `<div class="report-row"><b>#${r.id} ${r.report_type}</b> — ${r.filename}
    <button class="btn btn-sm btn-outline-secondary float-end" onclick="analyze(${r.id})">AI Analyze</button></div>`
  ).join("") : "<p>No medical reports uploaded yet.</p>";
}
async function analyze(id) {
  try {
    const d = await api(`/api/reports/${id}/analyze`, {method:"POST"});
    alert(`${d.summary}\n\nStatus: ${d.status}\n\n${d.disclaimer}`);
  } catch(e) { alert(e.message); }
}
async function generateQR() {
  try {
    const d = await api("/api/qr/generate", {method:"POST"});
    document.getElementById("qrUrl").href = d.emergency_url;
    document.getElementById("qrUrl").textContent = "Open emergency view";
    document.getElementById("qrImage").src = "/api/qr/png?ts=" + Date.now();
  } catch(e) { alert(e.message); }
}
async function authDownload(event, url) {
  event.preventDefault();
  const r = await fetch(url, {headers:authHeaders(false)});
  if (!r.ok) { alert("Download failed"); return false; }
  const blob = await r.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob); a.download = "digital-health-card.pdf"; a.click();
  URL.revokeObjectURL(a.href);
  return false;
}
function logout() {
  localStorage.removeItem("access_token"); accessToken=null; showPage("home");
}
if (accessToken) { showPage("dashboard"); loadDashboard(); } else showPage("home");
