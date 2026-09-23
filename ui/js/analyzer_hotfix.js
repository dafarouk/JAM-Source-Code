(() => {
  'use strict';

  let lastAnalyzerContext = null;

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  function esc(value) {
    const node = document.createElement('div');
    node.textContent = String(value ?? '');
    return node.innerHTML;
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    const locale = window.JAM_I18N?.language === 'fr' ? 'fr-FR' : 'en-GB';
    return date.toLocaleString(locale, {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // ============================================================
  // ADD JOB: ensure #jobForm is a real HTMLFormElement.
  // ============================================================

  function patchJobFormFactory() {
    if (typeof window.jobFormBody !== 'function') return;
    if (window.jobFormBody.__jamPatched) return;

    const original = window.jobFormBody;

    const patched = function (...args) {
      const html = original(...args);
      const host = document.createElement('div');
      host.innerHTML = html;

      const oldRoot = host.querySelector('#jobForm');

      if (oldRoot && oldRoot.tagName !== 'FORM') {
        const form = document.createElement('form');

        for (const attr of [...oldRoot.attributes]) {
          form.setAttribute(attr.name, attr.value);
        }

        while (oldRoot.firstChild) {
          form.appendChild(oldRoot.firstChild);
        }

        oldRoot.replaceWith(form);
      }

      return host.innerHTML;
    };

    patched.__jamPatched = true;
    window.jobFormBody = patched;

    try {
      jobFormBody = patched;
    } catch (_) {
      // Global binding is not writable in some engines; window assignment is
      // enough for pywebview/WebView2 where JAM runs.
    }
  }

  // ============================================================
  // ANALYZER / ADD-EDIT JOB WINDOW LAYERING
  // ============================================================

  function patchAnalyzerWindowLayering() {
    if (typeof window.openAnalysisOverlay === 'function' &&
        !window.openAnalysisOverlay.__jamLayerPatched) {
      const originalOpenAnalysisOverlay = window.openAnalysisOverlay;

      const patchedOpenAnalysisOverlay = function (...args) {
        const modalRoot = $('#modalRoot');
        const jobEditorOpen = Boolean(
          modalRoot?.classList.contains('active') &&
          modalRoot.querySelector('#jobForm')
        );

        const root = originalOpenAnalysisOverlay(...args);
        root?.classList.toggle('analysis-over-job-modal', jobEditorOpen);
        return root;
      };

      patchedOpenAnalysisOverlay.__jamLayerPatched = true;
      window.openAnalysisOverlay = patchedOpenAnalysisOverlay;
      try { openAnalysisOverlay = patchedOpenAnalysisOverlay; } catch (_) {}
    }

    if (typeof window.openModal === 'function' &&
        !window.openModal.__jamLayerPatched) {
      const originalOpenModal = window.openModal;

      const patchedOpenModal = function (...args) {
        const root = originalOpenModal(...args);
        const analyzerOpen = $('#analysisOverlayRoot')?.classList.contains('active');
        root?.classList.toggle('modal-over-analysis', Boolean(analyzerOpen));
        return root;
      };

      patchedOpenModal.__jamLayerPatched = true;
      window.openModal = patchedOpenModal;
      try { openModal = patchedOpenModal; } catch (_) {}
    }
  }

  // ============================================================
  // ANALYZER RESULT UI
  // ============================================================

  function scoreBreakdownHtml(analysis) {
    const items = analysis.score_explanation || [];

    if (!items.length) {
      return '<p class="muted">No detailed score breakdown available.</p>';
    }

    return `
      <div class="score-breakdown-list">
        ${items.map(item => {
          const max = Number(item.max_points || 0);
          const points = Number(item.points || 0);
          const pct = max > 0 ? Math.max(0, Math.min(100, points / max * 100)) : 0;

          return `
            <div class="score-breakdown-row">
              <div class="score-breakdown-head">
                <strong>${esc(item.dimension)}</strong>
                <span>${points.toFixed(1)} / ${max.toFixed(0)}</span>
              </div>
              <div class="score-breakdown-track">
                <span style="width:${pct}%"></span>
              </div>
              <small class="muted">${esc(item.note || '')}</small>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  function evidenceHtml(items) {
    const rows = (items || []).slice(0, 8);

    if (!rows.length) {
      return '<span class="muted">None detected</span>';
    }

    return `
      <div class="analysis-evidence-list">
        ${rows.map(item => `
          <article class="analysis-evidence-item">
            <strong>${esc(item.requirement || '')}</strong>
            <div>
              <span>Job</span>
              <p>${esc(item.job_evidence || '—')}</p>
            </div>
            <div>
              <span>CV evidence</span>
              <p>${esc(item.cv_evidence || '—')}</p>
            </div>
          </article>
        `).join('')}
      </div>
    `;
  }

  function semanticEvidenceHtml(analysis) {
    const semantic = analysis.semantic_match || {};
    const evidence = semantic.evidence || [];
    const classifier = semantic.role_classifier || {};
    const predictions = classifier.top_predictions || [];
    const coverage = Number(semantic.coverage || 0);
    const model = semantic.model || analysis.ml_engine?.model || 'Local semantic engine';

    const statusLabel = value => {
      const labels = {
        strong: 'Strong',
        partial: 'Partial',
        weak: 'Weak',
        missing: 'Missing'
      };
      return labels[value] || value || 'Missing';
    };

    return `
      <div class="semantic-summary-grid">
        <div class="semantic-summary-card">
          <span>Requirement coverage</span>
          <strong>${coverage}%</strong>
        </div>

        <div class="semantic-summary-card">
          <span>Statistical role classification</span>
          <strong>${esc(classifier.predicted_family || 'Not detected')}</strong>
          ${predictions.length
            ? `<small>${predictions.map(item => `${esc(item.family)} ${Number(item.confidence || 0)}%`).join(' • ')}</small>`
            : ''}
        </div>

        <div class="semantic-summary-card">
          <span>Local ML engine</span>
          <strong>${esc(model)}</strong>
          <small>Local only — no CV/job text is sent to a cloud service.</small>
        </div>
      </div>

      <div class="semantic-evidence-list">
        ${evidence.length
          ? evidence.slice(0, 12).map(item => `
              <article class="semantic-evidence-item ${esc(item.status || 'missing')}">
                <div class="semantic-evidence-head">
                  <strong>${esc(item.requirement || '')}</strong>
                  <span>${esc(statusLabel(item.status))} • ${Number(item.similarity_pct || 0)}%</span>
                </div>
                <div class="semantic-cv-evidence">
                  <span>Best CV evidence</span>
                  <p>${esc(item.cv_evidence || '—')}</p>
                </div>
              </article>
            `).join('')
          : '<p class="muted">No semantic requirement evidence available.</p>'}
      </div>
    `;
  }

  function chipsHtml(values, cls = '') {
    if (!values?.length) {
      return '<span class="muted">None detected</span>';
    }

    return `
      <div class="chips">
        ${values.map(value => `<span class="chip ${cls}">${esc(value)}</span>`).join('')}
      </div>
    `;
  }

  function salaryText(analysis) {
    const salary = analysis.salary;
    if (!salary) return 'No reliable salary detected.';

    const range = salary.max && salary.max !== salary.min
      ? `${salary.min}–${salary.max}`
      : `${salary.min ?? ''}`;

    let fit = '';
    if (analysis.salary_fit === true) fit = ' • Within salary target';
    if (analysis.salary_fit === false) fit = ' • Outside salary target';

    return `${range} ${salary.currency || ''} ${salary.period || ''}${fit}`.trim();
  }

  function replaceAnalysisResultRenderer() {
    const renderer = function (analysis) {
      const scoreAvailable = Boolean(
        analysis?.score_available &&
        analysis.score !== null &&
        analysis.score !== undefined
      );

      const score = scoreAvailable ? Number(analysis.score) : 0;
      const role = analysis.role_match || {};
      const requiredYears = analysis.required_years;
      const cvYears = analysis.cv_years;
      const education = analysis.education_match || {};
      const requiredEducation = education.required || {};
      const cvEducation = education.cv || {};
      const reference = analysis.reference || null;

      const jobExperienceText = requiredYears == null
        ? 'No explicit experience minimum detected.'
        : `Job requirement: about ${requiredYears}+ year(s).`;

      const cvExperienceText = `CV timeline estimate: ${cvYears == null ? 'unclear' : `${cvYears} year(s)`}.`;

      const requiredEducationFields = requiredEducation.fields || [];
      const cvEducationFields = cvEducation.fields || [];

      const noScoreReasons = analysis.no_score_reasons || [];
      const penalties = analysis.penalty_reasons || [];

      const root = openAnalysisOverlay(`
        <div class="analysis-overlay-head">
          <div>
            <div class="eyebrow">CV MATCH RESULT</div>
            <h2>${scoreAvailable ? `${score}% match` : 'No reliable score'}</h2>
          </div>
          <button class="icon-btn" data-close-analysis>×</button>
        </div>

        <div class="analysis-overlay-body analyzer-v3-result">
          <div class="analysis-result-top">
            ${scoreAvailable
              ? `<div class="score-ring" style="--score:${score}"><strong>${score}%</strong></div>`
              : '<div class="analysis-no-score">NO<br>SCORE</div>'}

            <div class="analysis-score-meta">
              <strong>${esc(analysis.score_label || (scoreAvailable ? 'Evidence-based match' : 'Insufficient evidence'))}</strong>
              <div class="confidence-line">
                <span>Evidence confidence</span>
                <b>${Number(analysis.confidence || 0)}%</b>
              </div>
              <p class="muted">${esc(
                scoreAvailable
                  ? 'JAM v4 keeps the deterministic hard checks and adds local ML requirement-to-CV evidence matching plus statistical job-family classification.'
                  : (noScoreReasons[0] || 'JAM does not have enough reliable evidence to calculate a percentage.')
              )}</p>
            </div>
          </div>

          <div class="analysis-groups" style="margin-top:18px">
            <div class="analysis-group">
              <h4>Role / title alignment</h4>
              <p>${esc(role.relation || 'No reliable role evidence detected.')}</p>
              ${role.job_families?.length ? `<p class="muted">Target: ${esc(role.job_families.join(', '))}</p>` : ''}
              ${role.cv_families?.length ? `<p class="muted">CV roles: ${esc(role.cv_families.join(', '))}</p>` : ''}
            </div>

            ${reference?.value ? `
              <div class="analysis-group analysis-reference-group">
                <h4>Job reference</h4>
                <div class="analysis-reference-row">
                  <code>${esc(reference.value)}</code>
                  <button class="btn secondary compact" data-copy-reference>Copy</button>
                </div>
                <p class="muted">${esc(reference.label || 'Reference')}</p>
              </div>
            ` : ''}

            <div class="analysis-group">
              <h4>Score breakdown</h4>
              ${scoreBreakdownHtml(analysis)}
            </div>

            <div class="analysis-group analysis-semantic-group">
              <div class="analysis-group-title-row">
                <h4>Semantic requirement evidence</h4>
                <span class="analysis-engine-badge">LOCAL ML</span>
              </div>
              ${semanticEvidenceHtml(analysis)}
            </div>

            ${penalties.length ? `
              <div class="analysis-group analysis-warning-group">
                <h4>Score penalties / hard requirements</h4>
                <ul>${penalties.map(item => `<li>${esc(item)}</li>`).join('')}</ul>
                ${analysis.hard_cap && Number(analysis.hard_cap) < 100
                  ? `<p class="muted">Maximum score after hard-fit checks: ${esc(analysis.hard_cap)}%</p>`
                  : ''}
              </div>
            ` : ''}

            <div class="analysis-group">
              <h4>Matched skills & tools</h4>
              ${chipsHtml(analysis.matched_required_competencies?.length ? analysis.matched_required_competencies : analysis.matched_skills, 'good')}
            </div>

            <div class="analysis-group">
              <h4>Missing required / not clearly found</h4>
              ${chipsHtml(
                analysis.missing_required_competencies?.length
                  ? analysis.missing_required_competencies
                  : (analysis.missing_required_skills?.length
                    ? analysis.missing_required_skills
                    : analysis.missing_skills),
                'missing'
              )}
            </div>

            <div class="analysis-group">
              <h4>Experience</h4>
              <div class="analysis-experience-lines">
                <div>${esc(jobExperienceText)}</div>
                <div>${esc(cvExperienceText)}</div>
              </div>
            </div>

            <div class="analysis-group">
              <h4>Education</h4>
              <div class="analysis-education-grid">
                <div>
                  <span class="analysis-mini-label">Job requirement</span>
                  <strong>${esc(requiredEducation.label || 'Not specified')}</strong>
                  <p class="muted">${esc(requiredEducationFields.length ? requiredEducationFields.join(', ') : 'No specific field detected')}</p>
                </div>
                <div>
                  <span class="analysis-mini-label">CV evidence</span>
                  <strong>${esc(cvEducation.label || 'Not found')}</strong>
                  <p class="muted">${esc(cvEducationFields.length ? cvEducationFields.join(', ') : 'No matching field found')}</p>
                </div>
              </div>
            </div>

            <div class="analysis-group">
              <h4>Salary detected</h4>
              <div>${esc(salaryText(analysis))}</div>
            </div>

            <div class="analysis-group">
              <h4>Languages</h4>
              <div class="analysis-mini-label">Matched</div>
              ${chipsHtml(analysis.matched_languages, 'good')}
              <div class="analysis-mini-label spaced">Missing / not found</div>
              ${chipsHtml(analysis.missing_languages, 'missing')}
            </div>

            <div class="analysis-group">
              <h4>Responsibilities / domain evidence</h4>
              <div class="analysis-mini-label">Matched</div>
              ${chipsHtml(analysis.matched_concepts, 'good')}
              <div class="analysis-mini-label spaced">Not clearly evidenced</div>
              ${chipsHtml(analysis.missing_concepts, 'missing')}
            </div>

            <div class="analysis-group">
              <h4>CV evidence used</h4>
              ${evidenceHtml(analysis.matched_skill_evidence)}
            </div>

            ${noScoreReasons.length > 1 ? `
              <div class="analysis-group">
                <h4>Why JAM did not score this</h4>
                <ul>${noScoreReasons.map(reason => `<li>${esc(reason)}</li>`).join('')}</ul>
              </div>
            ` : ''}

            <div class="analysis-group">
              <h4>What to review</h4>
              <ul>
                ${(analysis.suggestions || []).length
                  ? analysis.suggestions.map(item => `<li>${esc(item)}</li>`).join('')
                  : '<li>No specific changes suggested.</li>'}
              </ul>
            </div>
          </div>

          <div class="analysis-result-footer">
            <span class="muted">${esc(analysis.method || 'JAM Match Engine v4.0')}</span>
            <div class="button-row">
              <button class="btn secondary" data-export-analysis-pdf>Export PDF</button>
              <button class="btn gold" data-close-analysis>Done</button>
            </div>
          </div>
        </div>
      `);

      $$('[data-close-analysis]', root).forEach(button => {
        button.onclick = closeAnalysisOverlay;
      });

      $('[data-copy-reference]', root)?.addEventListener('click', async () => {
        if (!reference?.value) return;
        try {
          await copyText(reference.value);
          toast('Reference copied.');
        } catch (error) {
          toast(error.message, 'error');
        }
      });

      $('[data-export-analysis-pdf]', root)?.addEventListener('click', () => {
        exportCurrentAnalyzerPdf(analysis);
      });
    };

    window.showAnalysisResult = renderer;
    try { showAnalysisResult = renderer; } catch (_) {}
  }

  function replaceRunAnalysis() {
    const runner = async function (payload) {
      const timer = showAnalysisLoading();
      const started = performance.now();

      try {
        const result = await api('analyze_job', payload);

        const elapsed = performance.now() - started;
        if (elapsed < 650) {
          await new Promise(resolve => setTimeout(resolve, 650 - elapsed));
        }

        clearInterval(timer);
        showAnalysisResult(result.analysis);

        if (payload.id) {
          await reloadData();
        } else {
          const payloadKeys = Object.keys(payload || {});
          const standalone = payloadKeys.every(key =>
            key === 'job_title' || key === 'description'
          );

          if (standalone) {
            lastAnalyzerContext = {
              job_title: payload.job_title || '',
              description: payload.description || '',
              analysis: result.analysis
            };

            const saveButton = $('#saveAnalyzerResultBtn');
            if (saveButton) saveButton.disabled = false;
          }
        }

        return result.analysis;
      } catch (error) {
        clearInterval(timer);
        closeAnalysisOverlay();
        toast(error.message, 'error');
        return null;
      }
    };

    window.runAnalysis = runner;
    try { runAnalysis = runner; } catch (_) {}
  }

  async function exportCurrentAnalyzerPdf(analysisOverride = null) {
    const context = lastAnalyzerContext || {
      job_title: $('#analyzerTitle')?.value?.trim() || '',
      description: $('#analyzerDescription')?.value?.trim() || '',
      analysis: analysisOverride || null
    };

    const analysis = analysisOverride || context.analysis;
    if (!analysis) {
      toast('Analyze a role first.', 'error');
      return;
    }

    try {
      const result = await api('export_analysis_pdf', {
        job_title: context.job_title || $('#analyzerTitle')?.value?.trim() || '',
        description: context.description || $('#analyzerDescription')?.value?.trim() || '',
        analysis
      });

      if (typeof showExportCompleted === 'function') {
        showExportCompleted('Analyzer PDF', result.path);
      } else {
        toast(`Analyzer PDF created: ${result.path}`);
      }
    } catch (error) {
      toast(error.message, 'error');
    }
  }

  // ============================================================
  // ANALYZER PAGE SAVE / CLEAR / HISTORY
  // ============================================================

  async function renderHistory(items = null) {
    const root = $('#analyzerHistoryList');
    if (!root) return;

    try {
      const data = items ? { items } : await api('list_analysis_history');
      const rows = data.items || [];

      root.innerHTML = rows.length
        ? rows.map(item => `
          <article class="analyzer-history-item" data-history-id="${item.id}">
            <div>
              <strong>${esc(item.job_title || 'Untitled analysis')}</strong>
              <small class="muted">${esc(formatDate(item.created_at))}</small>
            </div>
            <div class="analyzer-history-score ${item.score == null ? 'no-score' : ''}">
              ${item.score == null ? 'NO SCORE' : `${item.score}%`}
            </div>
            <div class="analyzer-history-actions">
              <button class="btn secondary compact" data-open-analysis-history="${item.id}">Open</button>
              <button class="icon-btn" title="Delete" data-delete-analysis-history="${item.id}">×</button>
            </div>
          </article>
        `).join('')
        : '<p class="muted analyzer-empty-history">No saved analyses yet.</p>';

      $$('[data-open-analysis-history]', root).forEach(button => {
        button.onclick = () => {
          const id = Number(button.dataset.openAnalysisHistory);
          const item = rows.find(row => Number(row.id) === id);
          if (!item) return;

          $('#analyzerTitle').value = item.job_title || '';
          $('#analyzerDescription').value = item.description || '';
          lastAnalyzerContext = {
            job_title: item.job_title || '',
            description: item.description || '',
            analysis: item.analysis || {}
          };
          $('#saveAnalyzerResultBtn').disabled = false;
          const exportButton = $('#exportAnalyzerPdfBtn');
          if (exportButton) exportButton.disabled = false;
          showAnalysisResult(item.analysis || {});
        };
      });

      $$('[data-delete-analysis-history]', root).forEach(button => {
        button.onclick = async () => {
          try {
            const result = await api('delete_analysis_history', Number(button.dataset.deleteAnalysisHistory));
            await renderHistory(result.items || []);
            toast('Saved analysis deleted.');
          } catch (error) {
            toast(error.message, 'error');
          }
        };
      });
    } catch (error) {
      root.innerHTML = `<p class="muted">${esc(error.message)}</p>`;
    }
  }

  function bindAnalyzerPageControls() {
    const runButton = $('#runAnalyzerBtn');
    const saveButton = $('#saveAnalyzerResultBtn');
    const clearButton = $('#clearAnalyzerBtn');
    const previewButton = $('#previewCvBtn');
    const exportButton = $('#exportAnalyzerPdfBtn');

    if (runButton) {
      runButton.onclick = async () => {
        const payload = {
          job_title: $('#analyzerTitle')?.value?.trim() || '',
          description: $('#analyzerDescription')?.value?.trim() || ''
        };

        const analysis = await runAnalysis(payload);

        if (analysis) {
          lastAnalyzerContext = { ...payload, analysis };
          if (saveButton) saveButton.disabled = false;
          if (exportButton) exportButton.disabled = false;
        }
      };
    }

    if (saveButton) {
      saveButton.disabled = true;
      saveButton.onclick = async () => {
        if (!lastAnalyzerContext) {
          toast('Analyze a role first.', 'error');
          return;
        }

        try {
          const result = await api('save_analysis_history', lastAnalyzerContext);
          await renderHistory(result.items || []);
          toast('Analysis saved.');
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    }

    if (exportButton) {
      exportButton.disabled = true;
      exportButton.onclick = () => exportCurrentAnalyzerPdf();
    }

    if (clearButton) {
      clearButton.onclick = () => {
        if ($('#analyzerTitle')) $('#analyzerTitle').value = '';
        if ($('#analyzerDescription')) $('#analyzerDescription').value = '';
        lastAnalyzerContext = null;
        if (saveButton) saveButton.disabled = true;
        if (exportButton) exportButton.disabled = true;
        closeAnalysisOverlay();
        $('#analyzerTitle')?.focus();
      };
    }

    if (previewButton) {
      previewButton.onclick = previewCv;
    }
  }

  // ============================================================
  // CV PREVIEW
  // ============================================================

  async function previewCv() {
    let result;

    try {
      result = await api('get_cv_preview');
    } catch (error) {
      toast(error.message, 'error');
      return;
    }

    const preview = result.preview;
    let zoom = 1;

    const content = preview.kind === 'pdf'
      ? `
        <div class="cv-preview-pages" data-cv-pages>
          ${(preview.pages || []).map((src, index) => `
            <figure class="cv-preview-page-wrap">
              <img class="cv-preview-page" src="${src}" alt="CV page ${index + 1}">
              <figcaption>Page ${index + 1}</figcaption>
            </figure>
          `).join('')}
        </div>
      `
      : `<pre class="cv-preview-text">${esc(preview.text || '')}</pre>`;

    const root = openAnalysisOverlay(`
      <div class="analysis-overlay-head cv-preview-head">
        <div>
          <div class="eyebrow">CV PREVIEW</div>
          <h2>${esc(preview.name || 'Selected CV')}</h2>
        </div>
        <div class="cv-preview-toolbar">
          <button class="btn secondary compact" data-cv-zoom-out>−</button>
          <span data-cv-zoom-label>100%</span>
          <button class="btn secondary compact" data-cv-zoom-in>+</button>
          <button class="icon-btn" data-close-analysis>×</button>
        </div>
      </div>
      <div class="cv-preview-scroll">
        ${content}
      </div>
    `);

    const applyZoom = () => {
      $$('[data-cv-pages] .cv-preview-page', root).forEach(img => {
        img.style.width = `${zoom * 100}%`;
      });
      const label = $('[data-cv-zoom-label]', root);
      if (label) label.textContent = `${Math.round(zoom * 100)}%`;
    };

    $('[data-cv-zoom-out]', root)?.addEventListener('click', () => {
      zoom = Math.max(0.6, Math.round((zoom - 0.1) * 10) / 10);
      applyZoom();
    });

    $('[data-cv-zoom-in]', root)?.addEventListener('click', () => {
      zoom = Math.min(2.2, Math.round((zoom + 0.1) * 10) / 10);
      applyZoom();
    });

    $$('[data-close-analysis]', root).forEach(button => {
      button.onclick = closeAnalysisOverlay;
    });

    applyZoom();
  }

  function init() {
    patchJobFormFactory();
    patchAnalyzerWindowLayering();
    replaceAnalysisResultRenderer();
    replaceRunAnalysis();
    bindAnalyzerPageControls();
    renderHistory();
  }

  let initialized = false;

  function safeInit() {
    if (initialized) return;
    initialized = true;
    init();
  }

  document.addEventListener('pywebviewready', () => {
    // app.js registered its pywebviewready listener first and binds its native
    // buttons synchronously, so this runs immediately after and safely applies
    // the hotfix bindings.
    safeInit();
  });

  window.setTimeout(() => {
    if (!initialized && window.pywebview?.api) {
      safeInit();
    }
  }, 350);
})();
