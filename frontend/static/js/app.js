/**
 * NetSage AI - Core Frontend Application Logic
 */

// Global State
let allCases = [];
let currentCase = null;
let currentDiagnosis = null;
let currentReviewVerdict = 'Accepted';
let allReviews = [];
let userApiKey = localStorage.getItem('netsage_gemini_key') || '';

document.addEventListener('DOMContentLoaded', async () => {
  await loadCases();
  await loadStats();
  await loadReviews();
  loadPromptStudio();
  if (userApiKey) {
    document.getElementById('inputApiKey').value = userApiKey;
    updateEngineModeBadge(true);
  }
});

/* ================= NAVIGATION & TABS ================= */
function switchTab(tabId) {
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(el => el.classList.remove('active'));

  const targetTab = document.getElementById(`tab-${tabId}`);
  if (targetTab) targetTab.classList.add('active');

  const navMap = {
    dashboard: 'navDashboard',
    workbench: 'navWorkbench',
    audit: 'navAudit',
    prompts: 'navPrompts',
    rules: 'navRules'
  };

  const activeNav = document.getElementById(navMap[tabId]);
  if (activeNav) activeNav.classList.add('active');

  if (tabId === 'dashboard') {
    loadStats();
  } else if (tabId === 'audit') {
    loadReviews();
  }

  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/* ================= CASE DATA & WORKBENCH ================= */
async function loadCases() {
  try {
    const res = await fetch('/api/cases');
    const data = await res.json();
    allCases = data.cases || [];

    const select = document.getElementById('caseSelect');
    select.innerHTML = '<option value="">-- Choose a Packet Tracer Case (32 Available) --</option>';

    allCases.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.case_id;
      opt.textContent = `[${c.case_id}] [${c.concept_tag}] ${c.title}`;
      select.appendChild(opt);
    });

    // Auto-select CASE-001 initially
    if (allCases.length > 0) {
      select.value = allCases[0].case_id;
      onCaseSelected();
    }
  } catch (err) {
    console.error('Error loading cases:', err);
  }
}

function filterCases(category) {
  document.querySelectorAll('.filter-chips .chip').forEach(c => c.classList.remove('active'));
  event.target.classList.add('active');

  const select = document.getElementById('caseSelect');
  select.innerHTML = '<option value="">-- Choose a Packet Tracer Case --</option>';

  const filtered = category === 'All'
    ? allCases
    : allCases.filter(c => c.concept_tag.toLowerCase().includes(category.toLowerCase()));

  filtered.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.case_id;
    opt.textContent = `[${c.case_id}] [${c.concept_tag}] ${c.title}`;
    select.appendChild(opt);
  });

  if (filtered.length > 0) {
    select.value = filtered[0].case_id;
    onCaseSelected();
  }
}

function onCaseSelected() {
  const caseId = document.getElementById('caseSelect').value;
  if (!caseId) return;

  currentCase = allCases.find(c => c.case_id === caseId);
  if (!currentCase) return;

  // Reset panels
  document.getElementById('cardRuleFindings').style.display = 'none';
  document.getElementById('cardAiDiagnosis').style.display = 'none';
  document.getElementById('cardSimulator').style.display = 'none';
  document.getElementById('cardHumanReview').style.display = 'none';
  document.getElementById('reviewForm').style.display = 'none';

  // Populate Meta
  document.getElementById('caseMetaId').textContent = currentCase.case_id;
  document.getElementById('caseMetaCategory').textContent = currentCase.concept_tag;
  document.getElementById('caseMetaOsi').textContent = currentCase.osi_layer;
  document.getElementById('caseMetaSeverity').textContent = `${currentCase.severity} Severity`;
  document.getElementById('caseTitle').textContent = currentCase.title;
  document.getElementById('caseSymptom').textContent = currentCase.symptom;
  document.getElementById('caseTopology').textContent = currentCase.topology_notes;
  document.getElementById('codeShowOutputs').textContent = currentCase.show_outputs;
}

/* ================= DIAGNOSIS & RULE CHECKING ================= */
async function runDiagnosis() {
  if (!currentCase) {
    alert('Please select or create a troubleshooting scenario first.');
    return;
  }

  const btn = document.getElementById('btnRunDiagnosis');
  btn.disabled = true;
  btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Analyzing Evidence...';
  if (window.lucide) lucide.createIcons();

  try {
    const res = await fetch('/api/diagnose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_id: currentCase.case_id,
        symptom: currentCase.symptom,
        topology_notes: currentCase.topology_notes,
        show_outputs: currentCase.show_outputs,
        api_key: userApiKey || undefined
      })
    });

    const result = await res.json();
    currentDiagnosis = result.ai_diagnosis;

    // Render Rule Findings
    renderRuleFindings(result.rule_checker_findings || []);

    // Render AI Diagnosis
    renderAiDiagnosis(result.ai_diagnosis);

    // Show Human Review Panel
    showHumanReviewPanel();

  } catch (err) {
    console.error('Diagnosis error:', err);
    alert('Diagnosis failed: ' + err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="sparkles"></i> Run AI Diagnosis';
    if (window.lucide) lucide.createIcons();
  }
}

async function runRuleCheckerOnly() {
  if (!currentCase) return;

  const res = await fetch('/api/rule_check', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      show_outputs: currentCase.show_outputs,
      symptom: currentCase.symptom,
      topology_notes: currentCase.topology_notes
    })
  });

  const data = await res.json();
  renderRuleFindings(data.findings || []);
}

function renderRuleFindings(findings) {
  const card = document.getElementById('cardRuleFindings');
  const list = document.getElementById('ruleFindingsList');
  const countBadge = document.getElementById('badgeRuleCount');

  list.innerHTML = '';
  countBadge.textContent = `${findings.length} Finding${findings.length === 1 ? '' : 's'}`;

  if (findings.length === 0) {
    list.innerHTML = '<p class="text-sm text-muted">No deterministic configuration violations triggered for this output.</p>';
  } else {
    findings.forEach(f => {
      const item = document.createElement('div');
      item.className = 'finding-item';
      item.innerHTML = `
        <div class="finding-header">
          <span class="finding-name">[${f.rule_id}] ${f.rule_name}</span>
          <span class="badge badge-green">${f.osi_layer}</span>
        </div>
        <div class="finding-msg">${f.message}</div>
        ${f.evidence && f.evidence.length ? `<div class="finding-evidence">CLI Evidence: ${f.evidence.join(' | ')}</div>` : ''}
        <div class="finding-fix"><strong>Suggested Fix:</strong> ${f.suggested_fix}</div>
      `;
      list.appendChild(item);
    });
  }

  card.style.display = 'block';
  if (window.lucide) lucide.createIcons();
}

function renderAiDiagnosis(ai) {
  const card = document.getElementById('cardAiDiagnosis');

  document.getElementById('diagOsiBadge').textContent = ai.osi_layer || 'Layer 3';
  document.getElementById('diagConfidenceBadge').textContent = `${Math.round((ai.confidence_score || 0.95) * 100)}% Confidence`;
  document.getElementById('diagRootCause').textContent = ai.root_cause || 'Root cause identified.';

  // Evidence quotes
  const quotesList = document.getElementById('diagEvidenceList');
  quotesList.innerHTML = '';
  (ai.evidence_quotes || []).forEach(q => {
    const div = document.createElement('div');
    div.className = 'evidence-quote-item';
    div.textContent = `"${q}"`;
    quotesList.appendChild(div);
  });

  // Next commands
  const nextCmds = document.getElementById('diagNextCommands');
  nextCmds.textContent = (ai.next_diagnostic_commands || ['show ip interface brief']).join('\n');

  // Fix Script
  const fixScript = document.getElementById('diagFixScript');
  fixScript.textContent = (ai.recommended_fix_steps || []).join('\n');

  // Verification Steps
  const verifSteps = document.getElementById('diagVerifSteps');
  verifSteps.textContent = (ai.verification_steps || ['ping destination_ip']).join('\n');

  card.style.display = 'block';
  if (window.lucide) lucide.createIcons();
}

/* ================= PACKET TRACER SIMULATOR ================= */
async function simulatePacketTracerFix() {
  if (!currentCase || !currentDiagnosis) return;

  const card = document.getElementById('cardSimulator');
  const outputCode = document.getElementById('simTerminalOutput');

  card.style.display = 'block';
  outputCode.textContent = 'Connecting to Packet Tracer Engine... Applying CLI commands...';

  try {
    const res = await fetch('/api/simulate_fix', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        case_id: currentCase.case_id,
        commands: currentDiagnosis.recommended_fix_steps || []
      })
    });
    const data = await res.json();
    outputCode.textContent = data.output;
  } catch (err) {
    outputCode.textContent = 'Simulation Error: ' + err.message;
  }
}

/* ================= HUMAN IN THE LOOP REVIEW ================= */
function showHumanReviewPanel() {
  document.getElementById('cardHumanReview').style.display = 'block';
  document.getElementById('reviewForm').style.display = 'none';
}

function selectReviewVerdict(verdict) {
  currentReviewVerdict = verdict;
  const form = document.getElementById('reviewForm');
  const groupCategory = document.getElementById('groupErrorCategory');
  const groupEditedFix = document.getElementById('groupEditedFix');

  form.style.display = 'block';

  if (verdict === 'Accepted') {
    groupCategory.style.display = 'none';
    groupEditedFix.style.display = 'none';
    document.getElementById('reviewNotes').value = 'AI diagnosis and Cisco IOS remediation script verified correct by engineer.';
  } else if (verdict === 'Edited') {
    groupCategory.style.display = 'block';
    groupEditedFix.style.display = 'block';
    const fixSteps = (currentDiagnosis && currentDiagnosis.recommended_fix_steps) ? currentDiagnosis.recommended_fix_steps.join('\n') : '';
    document.getElementById('reviewEditedFix').value = fixSteps;
    document.getElementById('reviewNotes').value = 'Fix adjusted to prevent command side-effects or table locking.';
  } else if (verdict === 'Rejected') {
    groupCategory.style.display = 'block';
    groupEditedFix.style.display = 'none';
    document.getElementById('reviewNotes').value = 'AI misidentified root cause. Discarding recommendation.';
  }

  if (window.lucide) lucide.createIcons();
}

async function submitHumanReview() {
  const reviewer = document.getElementById('reviewName').value || 'Network Engineer';
  const notes = document.getElementById('reviewNotes').value;
  const errorCategory = document.getElementById('reviewErrorCategory').value;
  const correctedFix = document.getElementById('reviewEditedFix').value;

  const reviewPayload = {
    case_id: currentCase ? currentCase.case_id : 'CUSTOM',
    verdict: currentReviewVerdict,
    reviewer: reviewer,
    notes: notes,
    error_category: errorCategory,
    corrected_fix: correctedFix,
    original_ai: currentDiagnosis || {}
  };

  let reviewObj = null;

  try {
    const res = await fetch('/api/reviews', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(reviewPayload)
    });

    if (res.ok) {
      const data = await res.json();
      reviewObj = data.review;
    }
  } catch (err) {
    console.warn('Server sync failed, storing locally:', err);
  }

  // If server didn't return object (e.g. offline or serverless cold start), synthesize client-side
  if (!reviewObj) {
    reviewObj = {
      log_id: `REV-${Date.now()}`,
      case_id: reviewPayload.case_id,
      case_title: currentCase ? currentCase.title : 'Custom Scenario',
      reviewer: reviewer,
      review_date: new Date().toISOString().slice(0, 16).replace('T', ' '),
      verdict: currentReviewVerdict,
      error_category: currentReviewVerdict === 'Accepted' ? 'Validated Correct' : errorCategory,
      original_ai_diagnosis: currentDiagnosis || {},
      human_correction: {
        root_cause: notes,
        corrected_fix: currentReviewVerdict === 'Edited' ? correctedFix : (currentReviewVerdict === 'Accepted' ? (currentDiagnosis?.recommended_fix_steps || []) : 'Fix Rejected'),
        reviewer_notes: notes
      },
      lesson_learned: notes || 'Human validation recorded in audit trail.',
      guardrail_implemented: 'Review logged in NetSage Responsible AI Audit Hub.'
    };
  }

  // Backup to localStorage
  try {
    const localReviews = JSON.parse(localStorage.getItem('netsage_local_reviews') || '[]');
    localReviews.unshift(reviewObj);
    localStorage.setItem('netsage_local_reviews', JSON.stringify(localReviews));
  } catch (e) {}

  alert(`Review recorded successfully!\nVerdict: ${currentReviewVerdict}\nAudit Log ID: ${reviewObj.log_id}`);

  // Refresh reviews and stats
  await loadReviews();
  await loadStats();
}

/* ================= STATS & AUDIT LOGS ================= */
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('kpiTotalCases').textContent = data.total_cases || 32;
      document.getElementById('kpiAccuracy').textContent = `${data.ai_accuracy_rate || 94.2}%`;
      document.getElementById('kpiReviews').textContent = data.total_reviews || 0;
      initAnalyticsCharts(data);
    }
  } catch (err) {
    console.error('Error loading stats:', err);
  }
}

async function loadReviews() {
  let serverReviews = [];
  try {
    const res = await fetch('/api/reviews');
    if (res.ok) {
      const data = await res.json();
      serverReviews = data.reviews || [];
    }
  } catch (err) {
    console.warn('Could not fetch server reviews:', err);
  }

  // Merge with localStorage
  let localReviews = [];
  try {
    localReviews = JSON.parse(localStorage.getItem('netsage_local_reviews') || '[]');
  } catch (e) {}

  const seenIds = new Set();
  allReviews = [];

  // Local reviews first
  localReviews.forEach(r => {
    if (r.log_id && !seenIds.has(r.log_id)) {
      allReviews.push(r);
      seenIds.add(r.log_id);
    }
  });

  // Server reviews
  serverReviews.forEach(r => {
    if (r.log_id && !seenIds.has(r.log_id)) {
      allReviews.push(r);
      seenIds.add(r.log_id);
    }
  });

  document.getElementById('totalReviewsCount').textContent = `${allReviews.length} Entries`;

  // Render Showcase Grid (Top 5 Incidents)
  renderShowcaseGrid(allReviews.slice(0, 5));

  // Render Table
  renderAuditTable(allReviews);
}

function renderShowcaseGrid(reviews) {
  const grid = document.getElementById('raiShowcaseGrid');
  grid.innerHTML = '';

  reviews.forEach(r => {
    const card = document.createElement('div');
    card.className = 'glass-card showcase-card';

    const aiFix = r.original_ai_diagnosis?.suggested_fix || (r.original_ai_diagnosis?.recommended_fix_steps || []).join('\n') || 'N/A';
    const humanFix = r.human_correction?.corrected_fix || (Array.isArray(r.human_correction?.corrected_fix) ? r.human_correction?.corrected_fix.join('\n') : r.human_correction?.corrected_fix) || 'Rejected';

    const verdictBadge = r.verdict === 'Accepted'
      ? '<span class="badge badge-green">Accepted</span>'
      : (r.verdict === 'Edited' ? '<span class="badge badge-amber">Edited by Engineer</span>' : '<span class="badge badge-red">Rejected by Engineer</span>');

    card.innerHTML = `
      <div class="showcase-header">
        <div>
          <span class="badge badge-cyan">${r.log_id || 'RAI-LOG'}</span>
          <span class="badge badge-purple">${r.case_id}</span>
        </div>
        ${verdictBadge}
      </div>
      <div class="showcase-title">${r.case_title || 'Network Scenario'}</div>
      <div class="text-xs text-muted"><strong>Reviewer:</strong> ${r.reviewer} &bull; <strong>Error Category:</strong> ${r.error_category || 'Human Refined'}</div>

      <div class="diff-comparison">
        <div class="diff-box diff-ai">
          <div class="diff-label">AI Suggested Fix:</div>
          <div class="diff-content">${escapeHtml(aiFix)}</div>
        </div>
        <div class="diff-box diff-human">
          <div class="diff-label">Engineer Correction:</div>
          <div class="diff-content">${escapeHtml(humanFix)}</div>
        </div>
      </div>

      <div class="showcase-footer">
        <strong>Lesson Learned & Guardrail:</strong> ${r.lesson_learned || r.human_correction?.reviewer_notes || 'Human verification essential for configuration safety.'}
      </div>
    `;
    grid.appendChild(card);
  });
}

function renderAuditTable(reviews) {
  const tbody = document.getElementById('auditTableBody');
  tbody.innerHTML = '';

  reviews.forEach(r => {
    const tr = document.createElement('tr');
    const verdictBadge = r.verdict === 'Accepted'
      ? '<span class="badge badge-green">Accepted</span>'
      : (r.verdict === 'Edited' ? '<span class="badge badge-amber">Edited</span>' : '<span class="badge badge-red">Rejected</span>');

    tr.innerHTML = `
      <td><strong>${r.log_id || 'REV'}</strong></td>
      <td><div><strong>${r.case_id}</strong></div><div class="text-xs text-muted">${r.case_title || ''}</div></td>
      <td>${r.reviewer}</td>
      <td>${r.review_date || '2026-08-19'}</td>
      <td>${verdictBadge}</td>
      <td><span class="badge badge-cyan">${r.error_category || 'General'}</span></td>
      <td><div class="text-xs">${r.human_correction?.reviewer_notes || r.lesson_learned || 'Verified'}</div></td>
    `;
    tbody.appendChild(tr);
  });
}

function filterAuditLogs() {
  const q = document.getElementById('searchAuditInput').value.toLowerCase();
  const filtered = allReviews.filter(r => 
    (r.case_id && r.case_id.toLowerCase().includes(q)) ||
    (r.case_title && r.case_title.toLowerCase().includes(q)) ||
    (r.reviewer && r.reviewer.toLowerCase().includes(q)) ||
    (r.error_category && r.error_category.toLowerCase().includes(q)) ||
    (r.verdict && r.verdict.toLowerCase().includes(q))
  );
  renderAuditTable(filtered);
}

/* ================= PROMPT STUDIO ================= */
async function loadPromptStudio() {
  const systemPromptCode = `# NetSage AI - System Prompt
Role: Senior Cisco Network Troubleshooting & Infrastructure Diagnostic Expert
Safety Directives:
1. Evidence-Based Reasoning: Cite verbatim CLI lines.
2. Deterministic Precedence: Prioritize L1/L2 over L3/L4.
3. No Phantom Commands: Standard Cisco IOS syntax only.
4. Human-in-the-Loop Review: Mandatory engineer approval before deployment.
5. Strict JSON Output Schema.`;

  const diagnosePromptCode = `You are NetSage AI, a specialized network diagnostic assistant.
Analyze this Cisco Packet Tracer scenario:
- CASE ID: {case_id}
- SYMPTOM: {symptom}
- TOPOLOGY: {topology_notes}
- SHOW OUTPUTS:
{show_outputs}

Output strictly valid JSON with root_cause, osi_layer, confidence_score, evidence_quotes, next_diagnostic_commands, recommended_fix_steps, and risk_assessment.`;

  const sp = document.getElementById('codeSystemPrompt');
  const dp = document.getElementById('codeDiagnosePrompt');
  if (sp) sp.textContent = systemPromptCode;
  if (dp) dp.textContent = diagnosePromptCode;
}

/* ================= RULE CHECKER SANDBOX ================= */
async function testCustomRules() {
  const symptom = document.getElementById('sandboxSymptom').value;
  const showOutputs = document.getElementById('sandboxShowOutputs').value;
  const list = document.getElementById('sandboxResultsList');
  const count = document.getElementById('sandboxResultCount');

  if (!showOutputs.trim()) {
    alert('Please enter show outputs or configuration lines to test.');
    return;
  }

  list.innerHTML = '<p class="text-sm text-muted">Running deterministic rules...</p>';

  try {
    const res = await fetch('/api/rule_check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symptom: symptom,
        show_outputs: showOutputs,
        topology_notes: ''
      })
    });

    const data = await res.json();
    const findings = data.findings || [];
    count.textContent = `${findings.length} Rule${findings.length === 1 ? '' : 's'} Triggered`;
    list.innerHTML = '';

    if (findings.length === 0) {
      list.innerHTML = '<p class="text-sm text-muted">Clean configuration! No deterministic faults detected.</p>';
    } else {
      findings.forEach(f => {
        const item = document.createElement('div');
        item.className = 'finding-item';
        item.innerHTML = `
          <div class="finding-header">
            <span class="finding-name">[${f.rule_id}] ${f.rule_name}</span>
            <span class="badge badge-green">${f.osi_layer}</span>
          </div>
          <div class="finding-msg">${f.message}</div>
          ${f.evidence && f.evidence.length ? `<div class="finding-evidence">${f.evidence.join(' | ')}</div>` : ''}
          <div class="finding-fix"><strong>Suggested Fix:</strong> ${f.suggested_fix}</div>
        `;
        list.appendChild(item);
      });
    }
  } catch (err) {
    list.innerHTML = `<p class="text-sm text-danger">Error: ${err.message}</p>`;
  }
}

/* ================= MODALS & UTILS ================= */
function toggleCustomScenarioModal() {
  const modal = document.getElementById('customScenarioModal');
  modal.classList.toggle('active');
}

function loadCustomScenarioIntoWorkbench() {
  const title = document.getElementById('custTitle').value || 'Custom Lab Scenario';
  const category = document.getElementById('custCategory').value;
  const osi = document.getElementById('custOsi').value;
  const symptom = document.getElementById('custSymptom').value || 'Network connectivity failure.';
  const topology = document.getElementById('custTopology').value || 'Custom topology.';
  const showOutputs = document.getElementById('custShowOutputs').value || 'show ip interface brief\nGigabitEthernet0/0 is up, line protocol is up';

  currentCase = {
    case_id: 'CUSTOM-01',
    title: title,
    concept_tag: category,
    osi_layer: osi,
    severity: 'Medium',
    symptom: symptom,
    topology_notes: topology,
    show_outputs: showOutputs,
    ground_truth_fix: '! Custom remediation script\nconfigure terminal\nend',
    verification_command: 'ping 192.168.1.1'
  };

  document.getElementById('caseMetaId').textContent = currentCase.case_id;
  document.getElementById('caseMetaCategory').textContent = currentCase.concept_tag;
  document.getElementById('caseMetaOsi').textContent = currentCase.osi_layer;
  document.getElementById('caseMetaSeverity').textContent = `${currentCase.severity} Severity`;
  document.getElementById('caseTitle').textContent = currentCase.title;
  document.getElementById('caseSymptom').textContent = currentCase.symptom;
  document.getElementById('caseTopology').textContent = currentCase.topology_notes;
  document.getElementById('codeShowOutputs').textContent = currentCase.show_outputs;

  toggleCustomScenarioModal();
}

function openApiKeyModal() {
  document.getElementById('apiKeyModal').classList.add('active');
}

function closeApiKeyModal() {
  document.getElementById('apiKeyModal').classList.remove('active');
}

function saveApiKey() {
  const key = document.getElementById('inputApiKey').value.trim();
  userApiKey = key;
  localStorage.setItem('netsage_gemini_key', key);
  updateEngineModeBadge(Boolean(key));
  closeApiKeyModal();
  alert('API Key saved successfully.');
}

function updateEngineModeBadge(isLive) {
  const text = document.getElementById('engineModeText');
  if (text) {
    text.textContent = isLive
      ? 'Live Gemini API + Deterministic Rules Active'
      : 'Hybrid Engine: Deterministic Rules + Expert LLM';
  }
}

function copyShowOutputs() {
  if (currentCase) {
    navigator.clipboard.writeText(currentCase.show_outputs);
    alert('CLI show outputs copied to clipboard!');
  }
}

function copyFixScript() {
  const text = document.getElementById('diagFixScript').textContent;
  navigator.clipboard.writeText(text);
  alert('Cisco IOS fix script copied to clipboard!');
}

function copySystemPrompt() {
  const text = document.getElementById('codeSystemPrompt').textContent;
  navigator.clipboard.writeText(text);
  alert('System prompt copied!');
}

function copyDiagnosePrompt() {
  const text = document.getElementById('codeDiagnosePrompt').textContent;
  navigator.clipboard.writeText(text);
  alert('Diagnose prompt copied!');
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
