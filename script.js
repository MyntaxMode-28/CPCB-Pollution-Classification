const el = (id) => document.getElementById(id);
let currentCategory = null; // tracks the most recent classification, used to pre-fill EC/Consent forms

function setStep(name) {
  document.querySelectorAll('.steps li').forEach(li => {
    li.classList.remove('active');
    if (li.dataset.step === name) li.classList.add('active');
  });
}

// Sidebar steps are now clickable — jump directly to any section at any time.
document.querySelectorAll('.steps li').forEach(li => {
  li.addEventListener('click', () => showPanel(li.dataset.step));
});

function showPanel(name) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  el('panel-' + name).classList.add('active');
  setStep(name);
}

function catClass(cat) {
  const c = (cat || '').toLowerCase();
  if (c === 'red') return 'cat-red';
  if (c === 'orange') return 'cat-orange';
  if (c === 'green') return 'cat-green';
  return 'cat-white';
}

function syncCategoryDropdowns(cat) {
  if (!cat || !['Red', 'Orange', 'Green'].includes(cat)) return;
  currentCategory = cat;
  const ecSel = el('ec-category');
  const consentSel = el('consent-category');
  if (ecSel) ecSel.value = cat;
  if (consentSel) consentSel.value = cat;
}

const freqMap = { Red: '6 months', Orange: '12 months', Green: '24 months', White: 'No routine' };

function showLoading(container, message) {
  container.innerHTML = `<div class="loading"><span class="spinner"></span>${message}</div>`;
}

// ---------- SEARCH ----------

el('search-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const query = el('search-input').value.trim();
  if (!query) return;
  showLoading(el('search-results'), `Searching for "${query}"…`);
  const res = await fetch('/api/search', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ query })
  });
  const data = await res.json();
  renderSearchResults(data, query);
});

function renderSearchResults(data, query) {
  const box = el('search-results');
  box.innerHTML = '';

  let aiHint = '';
  if (data.ai_suggested) {
    aiHint = `<div class="ai-hint">✨ No exact match for "${query}" — local AI suggested the closest real sector: <b>${data.ai_suggested}</b></div>`;
  } else if (data.ai_attempted && data.ai_raw_suggestion) {
    aiHint = `<div class="ai-hint">⚠️ AI was consulted and suggested "<b>${data.ai_raw_suggestion}</b>", but even that didn't match anything in the database.</div>`;
  } else if (data.ai_attempted && !data.ai_raw_suggestion) {
    aiHint = `<div class="ai-hint">⚠️ AI fallback was attempted but got no response — Ollama may not be running. Check <a href="/api/ai/status" target="_blank">/api/ai/status</a>.</div>`;
  }

  if (data.status === 'none' || !data.results.length) {
    box.innerHTML = `${aiHint}<div class="hint">❌ No match found for "${query}". Try a broader term, or run the Q-Flow assessment instead.</div>`;
    return;
  }

  if (data.status === 'multiple') {
    box.innerHTML = aiHint;
    const list = document.createElement('ul');
    list.className = 'candidate-list';
    data.results.forEach((r, i) => {
      const li = document.createElement('li');
      li.className = 'candidate-item';
      li.innerHTML = `
        <div><b>${i + 1}. ${r.sector}</b><br>
        <span class="result-meta"><span>${r.source}</span></span></div>
        <span class="cat-badge ${catClass(r.category)}">${r.category} · PI ${r.pi ?? '—'}</span>`;
      li.addEventListener('click', () => { showPanel('result'); renderFullResult(r); });
      list.appendChild(li);
    });
    const header = document.createElement('div');
    header.className = 'hint';
    header.textContent = '🔍 Multiple matches found — select the correct sector:';
    box.appendChild(header);
    box.appendChild(list);
    return;
  }

  // exact — single match (or single 17-category hit)
  box.innerHTML = aiHint;
  showPanel('result');
  renderFullResult(data.results[0]);
}

function renderFullResult(r) {
  syncCategoryDropdowns(r.category);
  const freq = r.inspection_frequency || freqMap[r.category] || 'N/A';
  el('result-body').innerHTML = `
    <div class="result-card">
      <table class="spec-table">
        <tr><th colspan="2">1. Sector Information</th></tr>
        <tr><td>Sector Name</td><td><b>${r.sector}</b></td></tr>
        <tr><td>Source</td><td>${r.source}</td></tr>
      </table>
      <table class="spec-table">
        <tr><th colspan="2">2. Pollution Index Summary</th></tr>
        <tr><td>Pollution Index (PI)</td><td>${r.pi ?? '—'}</td></tr>
        <tr><td>Category</td><td><span class="cat-badge ${catClass(r.category)}">${r.category}</span></td></tr>
      </table>
      <table class="spec-table">
        <tr><th colspan="2">3. Regulatory Requirements</th></tr>
        <tr><td>Inspection Frequency</td><td><b>${freq}</b></td></tr>
        <tr><td>17-Category Status</td><td>${r.seventeen_category ? 'Yes — Quarterly override applies' : 'No'}</td></tr>
      </table>
      ${r.notes ? `<div class="result-note">⚠ ${r.notes}</div>` : ''}
      <div class="disclaimer">Disclaimer: AI-generated response based on CPCB Classification 2025 methodology.
      Final classification and regulatory decisions rest with CPCB/MoEF&CC/SPCB/PCC.</div>
    </div>
    ${applicabilityHtml(r.category)}`;
  wireToolLinks();
}

// ---------- Q-FLOW ----------

el('goto-qflow').addEventListener('click', async () => {
  showPanel('qflow');
  const nameField = el('qflow-sector-name');
  if (!nameField.value.trim() && el('search-input').value.trim()) {
    nameField.value = el('search-input').value.trim();
  }
  const res = await fetch('/api/qflow/start', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ sector_name: nameField.value.trim() })
  });
  const data = await res.json();
  renderQuestion(data);
});

function backButtonHtml(canGoBack) {
  return canGoBack ? `<button type="button" id="qflow-back-btn" class="link-btn">\u2190 Back to previous question</button>` : '';
}

function wireBackButton() {
  const btn = el('qflow-back-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const res = await fetch('/api/qflow/back', { method: 'POST' });
    if (!res.ok) return;
    const data = await res.json();
    renderQuestion(data);
  });
}

function renderQuestion(data) {
  const box = el('qflow-body');

  if (data.type === 'numeric_unit') {
    const unitOptions = data.units.map(u =>
      `<option value="${u.key}" ${u.key === data.default_unit ? 'selected' : ''}>${u.label}</option>`
    ).join('');
    const defaultLabel = (data.units.find(u => u.key === data.default_unit) || {}).label;
    box.innerHTML = `
      <div class="qflow-question">${data.text}</div>
      ${defaultLabel ? `<p class="hint" style="margin-bottom:10px;">Unit pre-selected as <b>${defaultLabel}</b>
        based on your fuel type — change it below if your figure is in a different unit.</p>` : ''}
      <form id="qflow-numeric-form" class="search-row">
        <input type="number" step="any" id="qflow-numeric-input" placeholder="Amount" required autofocus>
        <select id="qflow-unit-select">${unitOptions}</select>
        <button type="submit">Next</button>
      </form>
      <p class="hint" style="margin-top:8px;">If your fuel amount is measured by volume (e.g. cubic
      metres of gas) rather than weight, convert to kg first — exact volume-to-weight conversion
      varies by fuel type and isn't built in, to avoid guessing at a density figure.</p>
      ${backButtonHtml(data.can_go_back)}`;
    el('qflow-numeric-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const value = el('qflow-numeric-input').value;
      const unit = el('qflow-unit-select').value;
      const res = await fetch('/api/qflow/answer', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ value, unit })
      });
      const next = await res.json();
      if (next.done) { renderQflowResult(next.result); } else { renderQuestion(next); }
    });
    wireBackButton();
    return;
  }

  if (data.type === 'numeric') {
    box.innerHTML = `
      <div class="qflow-question">${data.text}</div>
      <form id="qflow-numeric-form" class="search-row">
        <input type="number" step="any" id="qflow-numeric-input" placeholder="${data.unit || ''}" required autofocus>
        <button type="submit">Next</button>
      </form>
      ${backButtonHtml(data.can_go_back)}`;
    el('qflow-numeric-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const value = el('qflow-numeric-input').value;
      const res = await fetch('/api/qflow/answer', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ value })
      });
      const next = await res.json();
      if (next.done) { renderQflowResult(next.result); } else { renderQuestion(next); }
    });
    wireBackButton();
    return;
  }

  box.innerHTML = `<div class="qflow-question">${data.text}</div><div class="qflow-options"></div>${backButtonHtml(data.can_go_back)}`;
  const opts = box.querySelector('.qflow-options');
  data.options.forEach((opt, i) => {
    const btn = document.createElement('button');
    btn.className = 'qflow-option';
    btn.textContent = `${i + 1}. ${opt}`;
    btn.addEventListener('click', async () => {
      const res = await fetch('/api/qflow/answer', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ choice: i + 1 })
      });
      const next = await res.json();
      if (next.done) {
        renderQflowResult(next.result);
      } else {
        renderQuestion(next);
      }
    });
    opts.appendChild(btn);
  });
  wireBackButton();
}

function renderQflowResult(result) {
  showPanel('result');
  syncCategoryDropdowns(result.Category);
  const freq = freqMap[result.Category] || 'N/A';
  const breakdownHtml = (result.breakdown || []).map(line => `<li>${line}</li>`).join('');
  const sectorName = el('qflow-sector-name').value.trim();
  const titleHtml = sectorName ? `<div class="result-title">${sectorName}</div>` : '';
  el('result-body').innerHTML = `
    ${titleHtml}
    <div class="result-card">
      <table class="spec-table">
        <tr><th colspan="2">2. Pollution Index Summary</th></tr>
        <tr><td>Water Score (PIW)</td><td>${result.PIW}</td></tr>
        <tr><td>Air Score (PIA)</td><td>${result.PIA}</td></tr>
        <tr><td>Waste Score (PIH)</td><td>${result.PIH}</td></tr>
        <tr><td>Final PI</td><td><b>${result.PI}</b></td></tr>
        <tr><td>Category</td><td><span class="cat-badge ${catClass(result.Category)}">${result.Category}</span></td></tr>
      </table>
      <table class="spec-table">
        <tr><th colspan="2">3. Regulatory Requirements</th></tr>
        <tr><td>Inspection Frequency</td><td><b>${freq}</b></td></tr>
      </table>
      <details class="breakdown-details">
        <summary>Show how this was calculated (which table row matched each answer)</summary>
        <ul class="breakdown-list">${breakdownHtml}</ul>
      </details>
      <div class="result-note">✅ Scored using official CPCB Table I/II/III thresholds (BOD/COD mg/l,
      wastewater KLD, fuel TPD, hazardous waste TPA, bed count). Sub-scores combine by
      summation within each domain (PIW = W1+W2+W3, PIA = A1+A2+A3, PIH = H1+H2 for
      hazardous waste), then the final PI formula weights the two lower domain scores in.</div>
      <div class="disclaimer">Disclaimer: AI-generated response based on CPCB Classification 2025 methodology.
      Final classification and regulatory decisions rest with CPCB/MoEF&CC/SPCB/PCC.</div>
    </div>
    ${applicabilityHtml(result.Category)}`;
  wireToolLinks();
}

function applicabilityHtml(category) {
  const applicable = ['Red', 'Orange', 'Green'].includes(category);
  if (applicable) {
    return `<div class="tool-links">
      <button id="goto-ec-panel" class="link-btn">Estimate Environmental Compensation (EC) →</button>
      <button id="goto-consent-panel" class="link-btn">Calculate CTE/CTO consent fee →</button>
    </div>`;
  }
  return `<div class="result-note">ℹ️ ${category || 'This'} category units are not subject to routine
    EC assessment or the general CTE/CTO fee formula. ${category === 'White'
      ? 'Only intimation to SPCB/PCC is required.'
      : 'Consult SPCB/PCC directly for applicable requirements.'}</div>`;
}

function wireToolLinks() {
  const ec = el('goto-ec-panel'); if (ec) ec.addEventListener('click', () => showPanel('ec'));
  const cf = el('goto-consent-panel'); if (cf) cf.addEventListener('click', () => showPanel('consent'));
}

// ---------- EC CALCULATOR ----------

el('ec-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  showLoading(el('ec-body'), 'Calculating…');
  const payload = {
    category: el('ec-category').value,
    days: el('ec-days').value,
    scale_key: el('ec-scale').value,
    location_key: el('ec-location').value,
    repeat_key: el('ec-repeat').value,
    r_factor: el('ec-r-factor').value,
  };
  const res = await fetch('/api/ec/calculate', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  renderEcResult(data);
});

function renderEcResult(data) {
  const box = el('ec-body');
  if (!data.applicable) {
    box.innerHTML = `<div class="hint">ℹ️ ${data.message}</div>`;
    return;
  }
  box.innerHTML = `
    <div class="result-card">
      <table class="spec-table">
        <tr><th colspan="2">Environmental Compensation Estimate</th></tr>
        <tr><td>Category-average PI used</td><td>${data.PI_ec}</td></tr>
        <tr><td>Days of violation</td><td>${data.days}</td></tr>
        <tr><td>Rupee factor (R)</td><td>₹${data.R}</td></tr>
        <tr><td>Scale factor (S)</td><td>${data.S}</td></tr>
        <tr><td>Location factor (LF)</td><td>${data.LF}</td></tr>
        <tr><td>Repeat-violation multiplier</td><td>×${data.multiplier}</td></tr>
        <tr><td>Base EC (before multiplier)</td><td>₹${data.EC_base.toLocaleString('en-IN')}</td></tr>
        <tr><td><b>Estimated Final EC</b></td><td><b>₹${data.EC_final.toLocaleString('en-IN')}</b></td></tr>
      </table>
      <div class="disclaimer">This is an illustrative estimate using CPCB's General EC formula
      (EC = PI × N × R × S × LF). Actual EC assessed by CPCB/SPCB/PCC may differ based on site
      inspection, applicable violation-specific formula, and administrative discretion. Does not
      cover sewage/biomedical/solid-waste-specific formulas.</div>
    </div>`;
}

// ---------- CONSENT FEE CALCULATOR ----------

el('consent-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  showLoading(el('consent-body'), 'Calculating…');
  const payload = {
    category: el('consent-category').value,
    capital_investment: el('consent-capital').value,
  };
  const res = await fetch('/api/consent/fee', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  renderConsentResult(data);
});

function renderConsentResult(data) {
  const box = el('consent-body');
  if (!data.applicable) {
    box.innerHTML = `<div class="hint">ℹ️ ${data.message}</div>`;
    return;
  }
  const f = data.fee, v = data.validity, t = data.timelines;
  box.innerHTML = `
    <div class="result-card">
      <table class="spec-table">
        <tr><th colspan="2">Consent Fee (CF = CI × SF × PIF)</th></tr>
        <tr><td>Capital Investment</td><td>₹${f.capital_investment.toLocaleString('en-IN')}</td></tr>
        <tr><td>Category</td><td><span class="cat-badge ${catClass(f.category)}">${f.category}</span></td></tr>
        <tr><td>Annual Consent Fee</td><td><b>₹${f.annual_fee.toLocaleString('en-IN')}</b></td></tr>
        <tr><td>Consent to Establish fee (max, ≤2× annual)</td><td>₹${f.cte_fee_max.toLocaleString('en-IN')}</td></tr>
      </table>
      <table class="spec-table">
        <tr><th colspan="2">Consent to Operate — Validity</th></tr>
        <tr><td colspan="2">${v.description}</td></tr>
      </table>
      ${t ? `
      <table class="spec-table">
        <tr><th colspan="2">Expected Processing Time (statutory maximum)</th></tr>
        <tr><td>Consent to Establish — decision within</td><td><b>${t.consent_to_establish_days} days</b></td></tr>
        <tr><td>Consent to Operate (first time) — decision within</td><td><b>${t.consent_to_operate_first_days} days</b></td></tr>
        <tr><td>Renewal / Expansion / Amendment — decision within</td><td><b>${t.consent_to_operate_renewal_expansion_days} days</b></td></tr>
      </table>
      <div class="result-note">⏱ ${t.escalation_note}</div>` : ''}
      <div class="disclaimer">Source: ${v.source}. This corrects the older fixed-year validity
      table (Red=5yr/Orange=10yr/Green=15yr) which was superseded by this amendment.</div>
    </div>`;
}

// ---------- RESET ----------

el('reset-btn').addEventListener('click', async () => {
  await fetch('/api/reset', { method: 'POST' });
  el('search-input').value = '';
  el('search-results').innerHTML = '';
  el('ec-body').innerHTML = '';
  el('consent-body').innerHTML = '';
  el('qflow-sector-name').value = '';
  currentCategory = null;
  showPanel('search');
});
