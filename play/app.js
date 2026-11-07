"use strict";
// NeuralPet play page. Everything is drawn from the server's state: the body is the simulated
// centerline, the brain in the head is FlyWire geometry. All text goes in via textContent.
(() => {
  const $ = (id) => document.getElementById(id);
  const cv = $("arena"), ctx = cv.getContext("2d"), kcv = $("kc"), kctx = kcv.getContext("2d");
  let S = null, csrf = "", brain = null, busy = false, odorsFilled = false, smooth = null, cam = null;
  const VIEW = 3.5;   // body lengths across the hero view (follow camera); a minimap shows the whole arena

  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  function fit(c) {
    const r = c.getBoundingClientRect(), d = window.devicePixelRatio || 1;
    if (c.width !== Math.round(r.width * d)) { c.width = Math.round(r.width * d); c.height = Math.round(r.height * d); }
  }

  async function poll() {
    try {
      const r = await fetch("/api/state", { cache: "no-store", credentials: "same-origin" });
      if (r.status === 403) { $("msg").textContent = "Signed out: open your link with ?t=… again."; return setTimeout(poll, 3000); }
      S = await r.json(); csrf = S.csrf; render();
    } catch (e) { $("msg").textContent = "Connection lost, retrying…"; }
    setTimeout(poll, 250);
  }

  async function act(body) {
    if (busy) return; busy = true;
    try {
      const r = await fetch("/api/action", { method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body) });
      $("msg").textContent = r.ok ? "" : (await r.text()).slice(0, 120);
    } catch (e) { $("msg").textContent = "Could not reach the pet."; }
    busy = false;
  }

  // ---------- drawing
  function bodyPath(x, k) {
    // offset the simulated centerline by a width profile to get the tube outline
    const n = x.length, L = [], R = [];
    for (let i = 0; i < n; i++) {
      const a = x[Math.max(0, i - 1)], b = x[Math.min(n - 1, i + 1)];
      let tx = a[0] - b[0], ty = a[1] - b[1]; const m = Math.hypot(tx, ty) || 1; tx /= m; ty /= m;
      const s = i / (n - 1), w = k * (0.055 + 0.035 * Math.sin(Math.PI * Math.min(1, s * 1.15 + 0.08)));
      L.push([x[i][0] - ty * w, x[i][1] + tx * w]); R.push([x[i][0] + ty * w, x[i][1] - tx * w]);
    }
    return L.concat(R.reverse());
  }

  function render() {
    fit(cv);
    const W = cv.width, sc = W / VIEW, half = VIEW / 2;
    const hd = S.body[0], A = S.arena, wrap = (d) => d - A * Math.round(d / A);   // torus world
    cam = cam ? [cam[0] + 0.15 * wrap(hd[0] - cam[0]), cam[1] + 0.15 * wrap(hd[1] - cam[1])] : [hd[0], hd[1]];
    const near = (p) => [cam[0] + wrap(p[0] - cam[0]), cam[1] + wrap(p[1] - cam[1])];   // image nearest the camera
    const P = (p) => [(p[0] - cam[0] + half) * sc, W - (p[1] - cam[1] + half) * sc];
    ctx.clearRect(0, 0, W, W);
    ctx.fillStyle = css("--arena"); ctx.fillRect(0, 0, W, W);
    ctx.strokeStyle = css("--line"); ctx.lineWidth = 1;          // 1-BL grid so motion is visible
    for (let g = Math.floor(cam[0] - half); g <= cam[0] + half; g++) { const [x] = P([g, 0]); ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, W); ctx.stroke(); }
    for (let g = Math.floor(cam[1] - half); g <= cam[1] + half; g++) { const [, y] = P([0, g]); ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
    if (S.lights_off || S.torpor) { ctx.fillStyle = "rgba(10,10,30,.35)"; ctx.fillRect(0, 0, W, W); }
    // sources: soft plume + marker
    for (const s of S.sources) {
      if (!s.active) continue;
      const [px, py] = P(near(s.pos)), col = s.kind === "food" ? css("--food") : s.kind === "toy" ? css("--toy") : css("--toxic");
      const g = ctx.createRadialGradient(px, py, 0, px, py, 2 * sc);
      g.addColorStop(0, col + "55"); g.addColorStop(1, col + "00");
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(px, py, 2 * sc, 0, 7); ctx.fill();
      ctx.fillStyle = col; ctx.beginPath(); ctx.arc(px, py, 0.12 * sc, 0, 7); ctx.fill();
    }
    // body tube from the simulated centerline (lightly smoothed for display only)
    const x = S.body.map((p) => [p[0] + (near(hd)[0] - hd[0]), p[1] + (near(hd)[1] - hd[1])]);
    smooth = (smooth && smooth.length === x.length && Math.hypot(smooth[0][0] - x[0][0], smooth[0][1] - x[0][1]) < 1) ? smooth.map((p, i) => [p[0] + 0.5 * (x[i][0] - p[0]), p[1] + 0.5 * (x[i][1] - p[1])]) : x;
    const pts = bodyPath(smooth, 1).map(P);
    ctx.beginPath(); pts.forEach((p, i) => i ? ctx.lineTo(...p) : ctx.moveTo(...p)); ctx.closePath();
    ctx.fillStyle = css("--skin"); ctx.fill(); ctx.strokeStyle = css("--skin2"); ctx.lineWidth = Math.max(1, sc * 0.012); ctx.stroke();
    // energy reserve: a stripe along the body, filled from the tail by the energy fraction
    const n = smooth.length, upto = Math.max(1, Math.round(S.energy * (n - 1)));
    ctx.strokeStyle = css("--good"); ctx.lineWidth = sc * 0.035; ctx.lineCap = "round"; ctx.beginPath();
    for (let i = n - 1; i >= n - 1 - upto && i >= 0; i--) { const p = P(smooth[i]); i === n - 1 ? ctx.moveTo(...p) : ctx.lineTo(...p); }
    ctx.stroke();
    // cosmetic skin spots: count grows with age, colour from the strongest preference
    const best = (S.preferences || []).reduce((a, b) => Math.abs(b.valence) > Math.abs(a.valence) ? b : a, { valence: 0 });
    const spots = Math.min(n - 3, 1 + Math.floor(S.age_s / 600));
    ctx.fillStyle = best.valence >= 0 ? "rgba(27,175,122,.55)" : "rgba(214,87,63,.55)";
    for (let i = 0; i < spots; i++) { const p = P(smooth[3 + i]); ctx.beginPath(); ctx.arc(p[0], p[1], sc * 0.018, 0, 7); ctx.fill(); }
    // head with the brain inside
    const [hx, hy] = P(smooth[0]), r = sc * 0.15, h = -S.heading;
    ctx.fillStyle = css("--skin"); ctx.beginPath(); ctx.arc(hx, hy, r, 0, 7); ctx.fill(); ctx.stroke();
    if (brain && brain.points.length) {
      const on = new Set(S.kc), c = Math.cos(h), sn = Math.sin(h), rr = r * 0.8;
      for (let i = 0; i < brain.points.length; i++) {
        const [bx, by] = brain.points[i], [grp, idx] = brain.owner[i];
        const lit = grp === 0 && on.has(idx);
        ctx.fillStyle = lit ? "#ffcf3a" : grp === 1 ? "rgba(42,120,214,.5)" : grp === 2 ? "rgba(138,92,214,.5)" : "rgba(60,50,40,.35)";
        const sz = (lit ? 2.2 : 1.0) * (window.devicePixelRatio || 1) / 2;
        ctx.fillRect(hx + rr * (bx * c - by * sn) - sz, hy + rr * (bx * sn + by * c) - sz, 2 * sz, 2 * sz);
      }
    }
    if (S.da.r > 0 || S.da.p > 0) { ctx.strokeStyle = S.da.r > 0 ? css("--good") : css("--bad"); ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(hx, hy, r * 1.4, 0, 7); ctx.stroke(); }

    // text
    $("name").textContent = S.name; document.title = S.name + " · NeuralPet";
    $("mood").textContent = S.mood;
    $("age").textContent = "age " + dur(S.age_s);
    $("energy").style.width = (100 * S.energy).toFixed(0) + "%";
    $("curiosity").style.width = (100 * S.curiosity).toFixed(0) + "%";
    $("restbtn").textContent = S.lights_off ? "☀️ Lights on" : "🌙 Lights off";
    $("genome").textContent = "Brain wiring: " + S.genome + ".";
    $("da").textContent = S.da.r > 0 ? "reward pulse" : S.da.p > 0 ? "punishment pulse" : "quiet";
    document.querySelectorAll("#actions button").forEach((b) => (b.disabled = S.read_only || !S.alive));
    if (!odorsFilled) {
      const sel = $("odor");
      S.odorants.forEach((o) => { if (o !== "water" && o !== "oil") { const e = document.createElement("option"); e.textContent = o; e.value = o; sel.appendChild(e); } });
      odorsFilled = true;
    }
    list($("prefs"), S.preferences.slice().sort((a, b) => b.valence - a.valence), (li, p) => {
      const nm = document.createElement("span"); nm.className = "name"; nm.textContent = p.odor;
      const bar = document.createElement("div"); bar.className = "pbar"; const i = document.createElement("i");
      const v = Math.max(-1, Math.min(1, p.valence / 0.3)), w = Math.abs(v) * 50;
      i.style.left = (v >= 0 ? 50 : 50 - w) + "%"; i.style.width = w + "%"; i.style.background = v >= 0 ? css("--good") : css("--bad");
      bar.appendChild(i); li.append(nm, bar); li.title = p.valence.toFixed(3);
    });
    list($("diary"), S.diary.slice().reverse(), (li, d) => {
      const t = document.createElement("time"); t.textContent = new Date(d.t * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
      li.append(t, document.createTextNode(d.text));
    });
    // minimap: whole arena, view window, sources, pet
    const m = W * 0.26, mx = W - m - 8, my = 8, ms = m / S.arena, md = (v) => ((v % A) + A) % A, M = (p) => [mx + md(p[0]) * ms, my + m - md(p[1]) * ms];
    ctx.fillStyle = "rgba(255,255,255,.55)"; ctx.fillRect(mx, my, m, m); ctx.strokeStyle = css("--ink2"); ctx.strokeRect(mx, my, m, m);
    { const [a, b] = M(cam); ctx.strokeRect(a - half * ms, b - half * ms, VIEW * ms, VIEW * ms); }
    for (const s of S.sources) if (s.active) { const [a, b] = M(s.pos); ctx.fillStyle = s.kind === "food" ? css("--food") : s.kind === "toy" ? css("--toy") : css("--toxic"); ctx.fillRect(a - 2, b - 2, 4, 4); }
    { const [a, b] = M(hd); ctx.fillStyle = css("--skin2"); ctx.beginPath(); ctx.arc(a, b, 3, 0, 7); ctx.fill(); }
    drawKC();
  }

  function drawKC() {
    fit(kcv);
    const W = kcv.width, H = kcv.height, on = new Set(S.kc), N = 2600, cols = Math.ceil(N / 6);
    kctx.clearRect(0, 0, W, H);
    for (let i = 0; i < N; i++) {
      const x = (i % cols) / cols * W, y = Math.floor(i / cols) / 6 * H;
      kctx.fillStyle = on.has(i) ? "#ffcf3a" : css("--line");
      kctx.fillRect(x, y, Math.max(1, W / cols - 0.5), H / 6 - 1);
    }
  }

  function list(el, items, fill) {
    el.replaceChildren(...items.map((it) => { const li = document.createElement("li"); fill(li, it); return li; }));
  }
  function dur(s) { s = Math.floor(s); return s < 60 ? s + " s" : s < 3600 ? Math.floor(s / 60) + " min" : Math.floor(s / 3600) + " h " + Math.floor((s % 3600) / 60) + " min"; }

  // ---------- inputs
  document.querySelectorAll("#actions button[data-a]").forEach((b) => b.addEventListener("click", () => {
    const a = b.dataset.a;
    if (a === "offer_odor") return act({ action: a, odor: $("odor").value });
    if (a === "rest") return act({ action: a, on: !S.lights_off });
    act({ action: a });
  }));
  cv.addEventListener("click", (e) => {
    if (!S) return;
    const r = cv.getBoundingClientRect(), u = (e.clientX - r.left) / r.width, v = 1 - (e.clientY - r.top) / r.height;
    const md = (q) => ((q % S.arena) + S.arena) % S.arena, x = md(cam[0] + (u - 0.5) * VIEW) / S.arena, y = md(cam[1] + (v - 0.5) * VIEW) / S.arena;
    const item = document.querySelector("input[name=drop]:checked").value;
    act(item === "toy" ? { action: "drop", item, x, y, odor: $("odor").value } : { action: "drop", item, x, y });
  });
  $("name").addEventListener("click", () => {
    const n = prompt("New name (max 24 characters):", S ? S.name : "");
    if (n && n.trim()) act({ action: "rename", name: n.trim().slice(0, 24) });
  });
  $("newpet").addEventListener("click", () => {
    if (confirm("Start a new pet? The current one becomes a read-only memorial.")) act({ action: "new_pet", confirm: true });
  });
  document.querySelector("details:last-of-type").addEventListener("toggle", async (e) => {
    if (!e.target.open) return;
    const m = await (await fetch("/api/memorials", { credentials: "same-origin" })).json();
    list($("memorials"), m.length ? m : [null], (li, x) => {
      li.textContent = x ? `${x.name}: lived ${dur(x.age_s)}, ${x.meals} meals; liked ${(x.preferences.filter(p => p.valence > 0.02).map(p => p.odor).join(", ") || "nothing in particular")}` : "No memorials yet.";
    });
  });

  fetch("/api/brain", { credentials: "same-origin" }).then((r) => r.ok ? r.json() : null).then((b) => (brain = b)).catch(() => {});
  poll();
})();
