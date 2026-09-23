(() => {
  'use strict';

  let initialized = false;
  let activePreset = null;
  let savedViews = [];

  const PRESETS = [
    ['applied_week', 'Applied this week'],
    ['interviewing', 'Interviewing'],
    ['score_70', 'Score ≥ 70'],
    ['five_stars', '5 stars'],
    ['not_analyzed', 'Not analyzed'],
    ['france', 'France'],
    ['tunisia', 'Tunisia']
  ];

  function tr(text) {
    return window.JAM_I18N?.translate
      ? window.JAM_I18N.translate(text)
      : text;
  }

  function safeJson(value, fallback = {}) {
    try {
      return JSON.parse(value || '');
    } catch (_) {
      return fallback;
    }
  }

  function fmtDateTime(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return String(value);
    return date.toLocaleString(
      window.JAM_I18N?.language === 'fr' ? 'fr-FR' : 'en-GB',
      {
        year: 'numeric',
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }
    );
  }

  function mondayStart() {
    const now = new Date();
    const day = now.getDay() || 7;
    const start = new Date(now);
    start.setHours(0, 0, 0, 0);
    start.setDate(now.getDate() - day + 1);
    return start;
  }

  function applyPreset(rows) {
    if (!activePreset) return rows;

    switch (activePreset) {
      case 'applied_week': {
        const start = mondayStart().getTime();
        return rows.filter(app => {
          const date = new Date(app.date_applied || '');
          return !Number.isNaN(date.getTime()) && date.getTime() >= start;
        });
      }

      case 'interviewing':
        return rows.filter(app => app.status === 'Interviewing');

      case 'score_70':
        return rows.filter(app => Number(app.match_score) >= 70);

      case 'five_stars':
        return rows.filter(app => Number(app.rating || 0) === 5);

      case 'not_analyzed':
        return rows.filter(app => app.match_score === null || app.match_score === undefined);

      case 'france':
        return rows.filter(app => {
          const value = normalizeText(app.location);
          return ['france','paris','lyon','marseille','lille','toulouse','bordeaux','nantes','nice','montpellier','rennes','strasbourg','ile de france','île-de-france','idf'].some(token => value.includes(normalizeText(token)));
        });

      case 'tunisia':
        return rows.filter(app => {
          const value = normalizeText(app.location);
          return ['tunisia','tunisie','tunis','ariana','sousse','sfax','monastir','ben arous','nabeul','bizerte'].some(token => value.includes(normalizeText(token)));
        });

      default:
        return rows;
    }
  }

  function installPresetFilter() {
    const original = window.getFilteredApplications;
    if (typeof original !== 'function' || original.__batch2Wrapped) return;

    const wrapped = function(...args) {
      return applyPreset(original(...args));
    };
    wrapped.__batch2Wrapped = true;
    window.getFilteredApplications = wrapped;
    try { getFilteredApplications = wrapped; } catch (_) {}
  }

  function injectApplicationControls() {
    const page = $('#applicationsPage');
    const toolbar = $('.toolbar', page);
    if (!page || !toolbar || $('#batch2PresetStrip')) return;

    const left = $('.toolbar-left', toolbar);
    const right = $('.toolbar-right', toolbar);

    const details = document.createElement('button');
    details.id = 'detailsSelectedBtn';
    details.className = 'btn secondary';
    details.hidden = true;
    details.textContent = tr('Details');
    left.appendChild(details);

    const bulk = document.createElement('button');
    bulk.id = 'bulkUpdateBtn';
    bulk.className = 'btn secondary';
    bulk.disabled = true;
    bulk.textContent = tr('Bulk update');
    left.appendChild(bulk);

    const saveView = document.createElement('button');
    saveView.id = 'saveViewBtn';
    saveView.className = 'btn secondary compact-action';
    saveView.textContent = tr('Save view');
    right.appendChild(saveView);

    const views = document.createElement('button');
    views.id = 'savedViewsBtn';
    views.className = 'btn secondary compact-action';
    views.textContent = tr('Saved views');
    right.appendChild(views);

    const strip = document.createElement('div');
    strip.id = 'batch2PresetStrip';
    strip.className = 'batch2-filter-strip';
    strip.innerHTML = `
      ${PRESETS.map(([key, label]) => `
        <button class="preset-btn" type="button" data-preset="${key}">${escapeHtml(tr(label))}</button>
      `).join('')}
      <span class="batch2-filter-spacer"></span>
      <button class="preset-btn" type="button" data-clear-preset>${escapeHtml(tr('Clear preset'))}</button>
    `;
    toolbar.insertAdjacentElement('afterend', strip);

    strip.addEventListener('click', event => {
      const preset = event.target.closest('[data-preset]');
      const clear = event.target.closest('[data-clear-preset]');
      if (preset) {
        activePreset = activePreset === preset.dataset.preset ? null : preset.dataset.preset;
        paintPresetButtons();
        renderTable();
      } else if (clear) {
        activePreset = null;
        paintPresetButtons();
        renderTable();
      }
    });

    details.onclick = () => openSelectedDetails();
    bulk.onclick = () => openBulkUpdate();
    saveView.onclick = () => saveCurrentView();
    views.onclick = () => showSavedViews();
  }

  function paintPresetButtons() {
    $$('#batch2PresetStrip [data-preset]').forEach(button => {
      button.classList.toggle('active', button.dataset.preset === activePreset);
    });
  }

  function syncBatch2SelectionUi() {
    const count = state.selectedIds.size;
    const details = $('#detailsSelectedBtn');
    const bulk = $('#bulkUpdateBtn');
    if (details) details.hidden = count !== 1;
    if (bulk) bulk.disabled = count === 0;
  }

  function wrapSelectionUi() {
    const original = window.updateSelectionUi;
    if (typeof original !== 'function' || original.__batch2Wrapped) return;
    const wrapped = function(...args) {
      const result = original(...args);
      syncBatch2SelectionUi();
      return result;
    };
    wrapped.__batch2Wrapped = true;
    window.updateSelectionUi = wrapped;
    try { updateSelectionUi = wrapped; } catch (_) {}
  }

  function enhanceRenderedRows() {
    $$('#jobsTableBody tr[data-id]').forEach(row => {
      const id = Number(row.dataset.id);
      const app = state.applications.find(item => item.id === id);
      if (!app || !app.url || row.querySelector('[data-table-open-url]')) return;

      const titleButton = row.querySelector('.row-edit');
      if (!titleButton) return;

      const open = document.createElement('button');
      open.type = 'button';
      open.className = 'text-btn table-open-url';
      open.dataset.tableOpenUrl = String(id);
      open.title = tr('Open job link');
      open.textContent = '↗';
      titleButton.insertAdjacentElement('afterend', open);
    });
  }

  function wrapRenderTable() {
    const original = window.renderTable;
    if (typeof original !== 'function' || original.__batch2Wrapped) return;
    const wrapped = function(...args) {
      const result = original(...args);
      enhanceRenderedRows();
      syncBatch2SelectionUi();
      return result;
    };
    wrapped.__batch2Wrapped = true;
    window.renderTable = wrapped;
    try { renderTable = wrapped; } catch (_) {}

    const body = $('#jobsTableBody');
    if (body && body.dataset.batch2UrlBound !== '1') {
      body.dataset.batch2UrlBound = '1';
      body.addEventListener('click', event => {
        const button = event.target.closest('[data-table-open-url]');
        if (!button) return;
        event.stopPropagation();
        const app = state.applications.find(item => item.id === Number(button.dataset.tableOpenUrl));
        if (app?.url) api('open_url', app.url).catch(error => toast(error.message, 'error'));
      });
    }
  }

  function wrapReloadData() {
    const original = window.reloadData;
    if (typeof original !== 'function' || original.__batch2Wrapped) return;
    const wrapped = async function(...args) {
      const result = await original(...args);
      await loadSavedViews();
      return result;
    };
    wrapped.__batch2Wrapped = true;
    window.reloadData = wrapped;
    try { reloadData = wrapped; } catch (_) {}
  }

  function structuredSalaryMarkup(app = {}) {
    const currency = escapeHtml(app.salary_currency || state.settings?.salary_currency || 'EUR');
    return `
      <div class="structured-salary-block" data-structured-salary>
        <span class="eyebrow">${escapeHtml(tr('STRUCTURED SALARY'))}</span>
        <div class="structured-salary-grid">
          <label>${escapeHtml(tr('Minimum'))}<input class="control full draft-main" name="salary_min" type="number" min="0" step="100" value="${escapeHtml(app.salary_min ?? '')}"></label>
          <label>${escapeHtml(tr('Maximum'))}<input class="control full draft-main" name="salary_max" type="number" min="0" step="100" value="${escapeHtml(app.salary_max ?? '')}"></label>
          <label>${escapeHtml(tr('Currency'))}<select class="control full" name="salary_currency">${CURRENCIES.map(item => `<option value="${item.code}" ${item.code === currency ? 'selected' : ''}>${escapeHtml(`${item.flag} ${item.code}`)}</option>`).join('')}</select></label>
          <label>${escapeHtml(tr('Period'))}<select class="control full" name="salary_period"><option value=""></option><option value="Annual" ${app.salary_period === 'Annual' ? 'selected' : ''}>${escapeHtml(tr('Annual'))}</option><option value="Monthly" ${app.salary_period === 'Monthly' ? 'selected' : ''}>${escapeHtml(tr('Monthly'))}</option><option value="Hourly" ${app.salary_period === 'Hourly' ? 'selected' : ''}>${escapeHtml(tr('Hourly'))}</option></select></label>
          <label>${escapeHtml(tr('Basis'))}<select class="control full" name="salary_basis"><option value=""></option><option value="Gross" ${app.salary_basis === 'Gross' ? 'selected' : ''}>${escapeHtml(tr('Gross'))}</option><option value="Net" ${app.salary_basis === 'Net' ? 'selected' : ''}>${escapeHtml(tr('Net'))}</option></select></label>
        </div>
      </div>
    `;
  }

  function addOpenButton(input, label) {
    if (!input || input.parentElement.querySelector('.job-inline-open')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn secondary job-inline-open';
    button.textContent = tr(label);
    button.onclick = async () => {
      const value = String(input.value || '').trim();
      if (!value) return toast(tr('No link to open.'), 'error');
      try { await api('open_url', value); } catch (error) { toast(error.message, 'error'); }
    };
    input.insertAdjacentElement('afterend', button);
  }

  function showDuplicateOverlay(duplicates, onSaveAnyway) {
    const first = duplicates[0];
    const overlay = document.createElement('div');
    overlay.className = 'batch2-overlay';
    overlay.innerHTML = `
      <section class="batch2-overlay-card">
        <div class="batch2-overlay-head">
          <div class="eyebrow">${escapeHtml(tr('POSSIBLE DUPLICATE'))}</div>
          <h2>${escapeHtml(tr('This application may already be tracked.'))}</h2>
        </div>
        <div class="batch2-overlay-body">
          <div class="details-card">
            <strong>${escapeHtml(first.company || '—')}</strong>
            <div>${escapeHtml(first.job_title || '—')}</div>
            <small class="muted">${escapeHtml(first.duplicate_reason || '')}</small>
          </div>
          ${duplicates.length > 1 ? `<p class="muted">${duplicates.length} ${escapeHtml(tr('possible matches found'))}</p>` : ''}
        </div>
        <div class="batch2-overlay-actions">
          <button class="btn secondary" data-dup-cancel>${escapeHtml(tr('Cancel'))}</button>
          <button class="btn secondary" data-dup-open>${escapeHtml(tr('Open existing'))}</button>
          <button class="btn gold" data-dup-save>${escapeHtml(tr('Save anyway'))}</button>
        </div>
      </section>
    `;
    document.body.appendChild(overlay);
    $('[data-dup-cancel]', overlay).onclick = () => overlay.remove();
    $('[data-dup-open]', overlay).onclick = () => {
      overlay.remove();
      closeModal();
      showApplicationDetails(first.id);
    };
    $('[data-dup-save]', overlay).onclick = async () => {
      overlay.remove();
      await onSaveAnyway();
    };
  }

  function enhanceJobModal(app = null) {
    const root = $('#modalRoot');
    const form = $('#jobForm', root);
    if (!form || form.dataset.batch2Ready === '1') return;
    form.dataset.batch2Ready = '1';

    const salaryText = form.querySelector('[name="salary_text"]')?.closest('label');
    if (salaryText) salaryText.insertAdjacentHTML('afterend', structuredSalaryMarkup(app || {}));

    addOpenButton(form.querySelector('[name="url"]'), 'Open job link');
    addOpenButton(form.querySelector('[name="contact_url"]'), 'Open contact link');

    const save = $('[data-save-job]', root);
    const originalSave = save?.onclick;
    if (save && typeof originalSave === 'function') {
      save.onclick = async event => {
        event?.preventDefault?.();
        try {
          const payload = Object.fromEntries(new FormData(form).entries());
          if (app?.id) payload.id = app.id;
          const result = await api('check_duplicates', payload);
          const duplicates = result.duplicates || [];
          if (duplicates.length) {
            showDuplicateOverlay(duplicates, originalSave);
            return;
          }
          await originalSave();
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    }
  }

  function wrapJobModal() {
    const original = window.openJobModal;
    if (typeof original !== 'function' || original.__batch2Wrapped) return;
    const wrapped = function(app = null) {
      const result = original(app);
      enhanceJobModal(app);
      return result;
    };
    wrapped.__batch2Wrapped = true;
    window.openJobModal = wrapped;
    try { openJobModal = wrapped; } catch (_) {}
  }

  function salaryDescription(app) {
    if (app.salary_min == null && app.salary_max == null) return app.salary_text || '—';
    const range = [app.salary_min, app.salary_max].filter(value => value !== null && value !== undefined && value !== '').join(' – ');
    return `${range} ${app.salary_currency || ''} ${app.salary_period || ''} ${app.salary_basis || ''}`.trim();
  }

  function analysisBreakdownMarkup(analysis) {
    const detail = analysis?.detail_breakdown || {};
    const entries = Object.entries(detail).filter(([, item]) => item?.applicable);
    if (!entries.length) return `<p class="muted">${escapeHtml(tr('No score breakdown saved.'))}</p>`;
    return entries.map(([name, item]) => `
      <div class="timeline-item">
        <div><strong>${escapeHtml(name)}</strong><br><small>${escapeHtml(String(item.raw_points ?? 0))} / ${escapeHtml(String(item.weight ?? 0))}</small></div>
      </div>
    `).join('');
  }

  async function showApplicationDetails(id) {
    try {
      const result = await api('get_application_details', Number(id));
      const app = result.application;
      const analysis = app.analysis || {};
      const timeline = (app.status_history || []).map(item => `
        <div class="timeline-item">
          <span>${statusPill(item.status)}</span>
          <small>${escapeHtml(fmtDateTime(item.changed_at))}</small>
        </div>
      `).join('') || `<p class="muted">${escapeHtml(tr('No status history yet.'))}</p>`;

      const body = `
        <div class="details-grid">
          <div class="details-card"><strong>${escapeHtml(tr('Company'))}</strong>${escapeHtml(app.company || '—')}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Job title'))}</strong>${escapeHtml(app.job_title || '—')}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Status'))}</strong>${statusPill(app.status)}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Score'))}</strong>${app.match_score == null ? '—' : `${app.match_score}%`}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Location'))}</strong>${escapeHtml(app.location || '—')} ${escapeHtml(app.work_mode || '')}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Salary'))}</strong>${escapeHtml(salaryDescription(app))}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Date saved'))}</strong>${escapeHtml(fmtDateTime(app.date_saved))}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Date applied'))}</strong>${escapeHtml(fmtDateTime(app.date_applied))}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Source'))}</strong>${escapeHtml(app.source || '—')}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Rating'))}</strong>${ratingStars(app.rating)}</div>
          <div class="details-card details-span-2">
            <strong>${escapeHtml(tr('Job URL'))}</strong>
            <div class="details-link-row"><span class="link-value">${escapeHtml(app.url || '—')}</span>${app.url ? `<button class="btn secondary" data-details-job-url>${escapeHtml(tr('Open'))}</button>` : ''}</div>
          </div>
          <div class="details-card details-span-2">
            <strong>${escapeHtml(tr('Contact'))}</strong>
            <div>${escapeHtml(app.contact_name || '—')}</div>
            <div class="details-link-row"><span class="link-value">${escapeHtml(app.contact_url || '—')}</span>${app.contact_url ? `<button class="btn secondary" data-details-contact-url>${escapeHtml(tr('Open'))}</button>` : ''}</div>
          </div>
          <div class="details-card details-span-2"><strong>${escapeHtml(tr('Description'))}</strong><div class="details-pre">${escapeHtml(app.description || '—')}</div></div>
          <div class="details-card details-span-2"><strong>${escapeHtml(tr('Notes'))}</strong><div class="details-pre">${escapeHtml(app.notes || '—')}</div></div>
          <div class="details-card details-span-2"><strong>${escapeHtml(tr('Status history'))}</strong><div class="status-timeline">${timeline}</div></div>
          <div class="details-card details-span-2"><strong>${escapeHtml(tr('Analyzer score breakdown'))}</strong><div class="status-timeline">${analysisBreakdownMarkup(analysis)}</div></div>
        </div>
      `;

      const root = openModal({
        kicker: 'APPLICATION DETAILS',
        title: `${app.company || ''} • ${app.job_title || ''}`,
        body,
        actions: `
          <button class="btn secondary" data-details-close>${escapeHtml(tr('Close'))}</button>
          <button class="btn gold" data-details-edit>${escapeHtml(tr('Edit application'))}</button>
        `,
        wide: true
      });
      $('[data-details-close]', root).onclick = closeModal;
      $('[data-details-edit]', root).onclick = () => {
        closeModal();
        openJobModal(app);
      };
      $('[data-details-job-url]', root)?.addEventListener('click', () => api('open_url', app.url).catch(error => toast(error.message, 'error')));
      $('[data-details-contact-url]', root)?.addEventListener('click', () => api('open_url', app.contact_url).catch(error => toast(error.message, 'error')));
    } catch (error) {
      toast(error.message, 'error');
    }
  }

  function openSelectedDetails() {
    if (state.selectedIds.size !== 1) return;
    showApplicationDetails([...state.selectedIds][0]);
  }

  function openBulkUpdate() {
    const count = state.selectedIds.size;
    if (!count) return;
    const root = openModal({
      kicker: 'BULK UPDATE',
      title: `${count} ${tr('selected applications')}`,
      body: `
        <p class="muted">${escapeHtml(tr('Leave a field blank to keep its current value.'))}</p>
        <div class="batch2-bulk-fields">
          <label>${escapeHtml(tr('Status'))}<select class="control full" data-bulk-status><option value=""></option>${STATUSES.map(status => `<option value="${escapeHtml(status)}">${escapeHtml(status)}</option>`).join('')}</select></label>
          <label>${escapeHtml(tr('Source'))}<input class="control full" data-bulk-source placeholder="LinkedIn"></label>
          <label>${escapeHtml(tr('Rating'))}<select class="control full" data-bulk-rating><option value=""></option>${[0,1,2,3,4,5].map(value => `<option value="${value}">${value ? '★'.repeat(value) : tr('No rating')}</option>`).join('')}</select></label>
        </div>
      `,
      actions: `<button class="btn secondary" data-bulk-cancel>${escapeHtml(tr('Cancel'))}</button><button class="btn gold" data-bulk-apply>${escapeHtml(tr('Apply changes'))}</button>`
    });
    $('[data-bulk-cancel]', root).onclick = closeModal;
    $('[data-bulk-apply]', root).onclick = async () => {
      const payload = {};
      const status = $('[data-bulk-status]', root).value;
      const source = $('[data-bulk-source]', root).value.trim();
      const rating = $('[data-bulk-rating]', root).value;
      if (status) payload.status = status;
      if (source) payload.source = source;
      if (rating !== '') payload.rating = Number(rating);
      if (!Object.keys(payload).length) return toast(tr('Choose at least one change.'), 'error');
      try {
        await api('bulk_update_applications', [...state.selectedIds], payload);
        closeModal();
        await reloadData();
        toast(tr('Selected applications updated.'));
      } catch (error) { toast(error.message, 'error'); }
    };
  }

  function viewStateSnapshot() {
    const filters = {};
    for (const column of FILTER_COLUMNS) {
      const value = state.tableFilters[column];
      filters[column] = value === null ? null : [...value];
    }
    return {
      search: $('#searchInput')?.value || '',
      preset: activePreset,
      tableSort: {...state.tableSort},
      tableFilters: filters
    };
  }

  function applyViewState(saved) {
    const snapshot = saved || {};
    if ($('#searchInput')) $('#searchInput').value = snapshot.search || '';
    activePreset = snapshot.preset || null;
    state.tableSort = snapshot.tableSort || {column: null, direction: null};
    const filters = snapshot.tableFilters || {};
    for (const column of FILTER_COLUMNS) {
      const value = filters[column];
      state.tableFilters[column] = value === null || value === undefined ? null : new Set(value);
    }
    paintPresetButtons();
    renderTable();
  }

  function askTextOverlay(title, initial = '') {
    return new Promise(resolve => {
      const overlay = document.createElement('div');
      overlay.className = 'batch2-overlay';
      overlay.innerHTML = `
        <section class="batch2-overlay-card">
          <div class="batch2-overlay-head"><div class="eyebrow">JAM</div><h2>${escapeHtml(title)}</h2></div>
          <div class="batch2-overlay-body"><input class="control full" data-text-value value="${escapeHtml(initial)}"></div>
          <div class="batch2-overlay-actions"><button class="btn secondary" data-text-cancel>${escapeHtml(tr('Cancel'))}</button><button class="btn gold" data-text-save>${escapeHtml(tr('Save'))}</button></div>
        </section>
      `;
      document.body.appendChild(overlay);
      const input = $('[data-text-value]', overlay);
      input.focus(); input.select();
      const finish = value => { overlay.remove(); resolve(value); };
      $('[data-text-cancel]', overlay).onclick = () => finish(null);
      $('[data-text-save]', overlay).onclick = () => finish(input.value.trim());
      input.addEventListener('keydown', event => { if (event.key === 'Enter') finish(input.value.trim()); if (event.key === 'Escape') finish(null); });
    });
  }

  async function loadSavedViews() {
    try {
      const result = await api('list_saved_views');
      savedViews = result.items || [];
    } catch (error) {
      console.error(error);
    }
  }

  async function saveCurrentView() {
    const name = await askTextOverlay(tr('Save current view'));
    if (!name) return;
    try {
      const result = await api('save_view', name, viewStateSnapshot());
      savedViews = result.items || [];
      toast(tr('View saved.'));
    } catch (error) { toast(error.message, 'error'); }
  }

  function showSavedViews() {
    const body = savedViews.length ? `
      <div class="saved-views-list">
        ${savedViews.map(view => `
          <div class="saved-view-item" data-view-id="${view.id}">
            <div><strong>${escapeHtml(view.name)}</strong><div class="muted">${escapeHtml(fmtDateTime(view.updated_at))}</div></div>
            <div class="saved-view-actions">
              <button class="btn secondary" data-view-open="${view.id}">${escapeHtml(tr('Open'))}</button>
              <button class="btn secondary" data-view-rename="${view.id}">${escapeHtml(tr('Rename'))}</button>
              <button class="btn danger subtle" data-view-delete="${view.id}">${escapeHtml(tr('Delete'))}</button>
            </div>
          </div>
        `).join('')}
      </div>` : `<p class="muted">${escapeHtml(tr('No saved views yet.'))}</p>`;
    const root = openModal({kicker: 'SAVED VIEWS', title: tr('Saved views'), body, wide: true});
    $$('[data-view-open]', root).forEach(button => button.onclick = () => {
      const view = savedViews.find(item => item.id === Number(button.dataset.viewOpen));
      if (view) { applyViewState(view.state); closeModal(); }
    });
    $$('[data-view-rename]', root).forEach(button => button.onclick = async () => {
      const view = savedViews.find(item => item.id === Number(button.dataset.viewRename));
      if (!view) return;
      const name = await askTextOverlay(tr('Rename saved view'), view.name);
      if (!name) return;
      try { const result = await api('rename_saved_view', view.id, name); savedViews = result.items || []; closeModal(); showSavedViews(); } catch (error) { toast(error.message, 'error'); }
    });
    $$('[data-view-delete]', root).forEach(button => button.onclick = async () => {
      try { const result = await api('delete_saved_view', Number(button.dataset.viewDelete)); savedViews = result.items || []; closeModal(); showSavedViews(); } catch (error) { toast(error.message, 'error'); }
    });
  }

  async function importExcelBatch2() {
    try {
      const result = await api('preview_excel_dialog');
      if (result.cancelled) return;
      const preview = result.preview || {};
      const body = `
        <div class="details-grid">
          <div class="import-preview-card"><strong>${escapeHtml(tr('Rows detected'))}</strong>${Number(preview.total_rows || 0)}</div>
          <div class="import-preview-card"><strong>${escapeHtml(tr('Possible duplicates'))}</strong>${Number(preview.duplicate_rows || 0)}</div>
          <div class="import-preview-card details-span-2"><strong>${escapeHtml(tr('Column mapping'))}</strong><div class="import-mapping-list">${(preview.columns || []).map(column => `<div class="import-mapping-row"><span>${escapeHtml(column.header)}</span><span>→</span><span class="${column.recognized ? '' : 'unknown'}">${escapeHtml(column.field || tr('Ignored'))}</span></div>`).join('')}</div></div>
          <div class="import-preview-card details-span-2"><strong>${escapeHtml(tr('Preview'))}</strong><table class="import-preview-table"><thead><tr><th>#</th><th>${escapeHtml(tr('Company'))}</th><th>${escapeHtml(tr('Job title'))}</th><th>${escapeHtml(tr('Status'))}</th></tr></thead><tbody>${(preview.preview || []).map(row => `<tr><td>${row.row}</td><td>${escapeHtml(row.company)}</td><td>${escapeHtml(row.job_title)}</td><td>${escapeHtml(row.status)} ${row.duplicate ? `<span class="import-duplicate">${escapeHtml(tr('Duplicate'))}</span>` : ''}</td></tr>`).join('')}</tbody></table></div>
          <label class="details-span-2"><input type="checkbox" data-import-duplicates> ${escapeHtml(tr('Import possible duplicates too'))}</label>
        </div>
      `;
      const root = openModal({
        kicker: 'EXCEL IMPORT PREVIEW',
        title: preview.file_name || tr('Excel import preview'),
        body,
        actions: `<button class="btn secondary" data-import-cancel>${escapeHtml(tr('Cancel'))}</button><button class="btn gold" data-import-confirm>${escapeHtml(tr('Import'))}</button>`,
        wide: true
      });
      $('[data-import-cancel]', root).onclick = closeModal;
      $('[data-import-confirm]', root).onclick = async () => {
        try {
          const imported = await api('confirm_excel_import', preview.path, $('[data-import-duplicates]', root).checked);
          closeModal();
          await reloadData();
          showImportReport(imported.summary || {});
        } catch (error) { toast(error.message, 'error'); }
      };
    } catch (error) { toast(error.message, 'error'); }
  }

  function showImportReport(summary) {
    const failures = summary.failures || [];
    const root = openModal({
      kicker: 'EXCEL IMPORT',
      title: tr('Import complete'),
      body: `
        <div class="details-grid">
          <div class="details-card"><strong>${escapeHtml(tr('Imported'))}</strong>${Number(summary.imported || 0)}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Blank rows skipped'))}</strong>${Number(summary.skipped || 0)}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Duplicates skipped'))}</strong>${Number(summary.duplicates_skipped || 0)}</div>
          <div class="details-card"><strong>${escapeHtml(tr('Rows failed'))}</strong>${Number(summary.failed || 0)}</div>
          ${failures.length ? `<div class="details-card details-span-2"><strong>${escapeHtml(tr('Import errors'))}</strong><div class="details-pre">${failures.map(item => `${tr('Row')} ${item.row}: ${item.error}`).map(escapeHtml).join('\n')}</div></div>` : ''}
        </div>
      `,
      actions: `<button class="btn gold" data-report-done>${escapeHtml(tr('Done'))}</button>`,
      wide: true
    });
    $('[data-report-done]', root).onclick = closeModal;
  }

  function renderExportHistoryBatch2() {
    const root = $('#exportHistory');
    if (!root) return;
    if (!state.exportHistory.length) {
      root.innerHTML = `<div class="panel"><p class="muted">${escapeHtml(tr('No exports yet.'))}</p></div>`;
      return;
    }
    root.innerHTML = state.exportHistory.map(item => `
      <div class="history-item batch2-history-item">
        <strong>${escapeHtml(item.export_type)}</strong>
        <span title="${escapeHtml(item.path)}">${escapeHtml(fileName(item.path))}</span>
        <span>${item.row_count} ${escapeHtml(tr('row(s)'))}</span>
        <div class="history-actions">
          <button class="btn secondary" data-export-open="${item.id}">${escapeHtml(tr('Open'))}</button>
          <button class="btn secondary" data-export-folder="${item.id}">${escapeHtml(tr('Open folder'))}</button>
          <button class="btn danger subtle" data-export-remove="${item.id}">${escapeHtml(tr('Remove from history'))}</button>
        </div>
      </div>
    `).join('');
  }

  function installExportHistory() {
    window.renderExportHistory = renderExportHistoryBatch2;
    try { renderExportHistory = renderExportHistoryBatch2; } catch (_) {}
    const root = $('#exportHistory');
    if (!root || root.dataset.batch2Bound === '1') return;
    root.dataset.batch2Bound = '1';
    root.addEventListener('click', async event => {
      const button = event.target.closest('[data-export-open], [data-export-folder], [data-export-remove]');
      if (!button) return;
      const id = Number(button.dataset.exportOpen || button.dataset.exportFolder || button.dataset.exportRemove);
      const item = state.exportHistory.find(row => row.id === id);
      if (!item) return;
      try {
        if (button.hasAttribute('data-export-open')) await api('open_path', item.path);
        if (button.hasAttribute('data-export-folder')) await api('open_parent_folder', item.path);
        if (button.hasAttribute('data-export-remove')) {
          const result = await api('remove_export_history', id);
          state.exportHistory = result.history || [];
          renderExportHistoryBatch2();
        }
      } catch (error) { toast(error.message, 'error'); }
    });
    renderExportHistoryBatch2();
  }

  function showRecentProjectsBatch2() {
    const body = state.recentProjects.length ? `<div class="history-list">${state.recentProjects.map(project => `
      <div class="history-item batch2-history-item">
        <div><strong>${escapeHtml(project.name)}</strong><div class="recent-project-meta"><span>${escapeHtml(String(project.application_count ?? '—'))} ${escapeHtml(tr('jobs'))}</span><span>${escapeHtml(tr('Opened'))}: ${escapeHtml(fmtDateTime(project.last_opened_at))}</span><span>${escapeHtml(tr('Modified'))}: ${escapeHtml(fmtDateTime(project.modified_at))}</span></div></div>
        <span title="${escapeHtml(project.path)}">${escapeHtml(project.path)}</span>
        <span>${project.exists ? escapeHtml(tr('Available')) : escapeHtml(tr('Missing file'))}</span>
        <div class="history-actions"><button class="btn secondary" data-open-recent="${escapeHtml(project.path)}" ${project.exists ? '' : 'disabled'}>${escapeHtml(tr('Open'))}</button><button class="btn danger subtle" data-recent-remove="${escapeHtml(project.path)}">${escapeHtml(tr('Remove from recent'))}</button></div>
      </div>
    `).join('')}</div>` : `<p class="muted">${escapeHtml(tr('No recent .jam projects yet.'))}</p>`;
    const root = openModal({kicker: 'PROJECTS', title: tr('Recent Projects'), body, wide: true});
    $$('[data-recent-remove]', root).forEach(button => button.onclick = async () => {
      try {
        const result = await api('remove_recent_project', button.dataset.recentRemove);
        state.recentProjects = result.recent_projects || [];
        closeModal(); showRecentProjectsBatch2();
      } catch (error) { toast(error.message, 'error'); }
    });
  }

  async function showLogsBatch2() {
    try {
      const result = await api('get_logs');
      const entries = result.entries || [];
      let kind = 'all';
      let query = '';
      const body = `
        <div class="log-filter-bar">
          <input class="control full" type="search" data-log-search placeholder="${escapeHtml(tr('Search logs...'))}">
          <div class="log-kind-buttons">${['all','info','success','warning','error'].map(value => `<button class="btn secondary ${value === 'all' ? 'active' : ''}" data-log-kind="${value}">${escapeHtml(tr(value[0].toUpperCase()+value.slice(1)))}</button>`).join('')}</div>
        </div>
        <div class="logs-readable" data-log-results></div>
      `;
      const root = openModal({kicker: 'DIAGNOSTICS', title: tr('JAM Activity & Logs'), body, actions: `<button class="btn secondary" data-log-close>${escapeHtml(tr('Close'))}</button><button class="btn gold" data-copy-logs>${escapeHtml(tr('Copy logs'))}</button>`, wide: true});
      const results = $('[data-log-results]', root);
      const render = () => {
        const filtered = entries.filter(entry => (kind === 'all' || entry.kind === kind) && (!query || normalizeText(`${entry.timestamp} ${entry.level} ${entry.message}`).includes(normalizeText(query))));
        results.innerHTML = filtered.length ? filtered.map(entry => `<div class="log-line log-${escapeHtml(entry.kind)}"><span class="log-symbol">${escapeHtml(entry.symbol)}</span><span class="log-time">${escapeHtml(entry.timestamp || '')}</span><span class="log-level">${escapeHtml(tr(entry.kind[0].toUpperCase()+entry.kind.slice(1)))}</span><span class="log-message">${escapeHtml(entry.message || '')}</span></div>`).join('') : `<div class="panel"><p class="muted">${escapeHtml(tr('No matching log entries.'))}</p></div>`;
      };
      $('[data-log-search]', root).addEventListener('input', event => { query = event.target.value; render(); });
      $$('[data-log-kind]', root).forEach(button => button.onclick = () => { kind = button.dataset.logKind; $$('[data-log-kind]', root).forEach(item => item.classList.toggle('active', item === button)); render(); });
      $('[data-log-close]', root).onclick = closeModal;
      $('[data-copy-logs]', root).onclick = async () => toast(await copyText(result.text || '') ? tr('Logs copied.') : tr('Could not copy logs.'), 'success');
      render();
    } catch (error) { toast(error.message, 'error'); }
  }

  function installButtonOverrides() {
    const importButton = $('#importExcelBtn');
    if (importButton) importButton.onclick = importExcelBatch2;
    const recentButton = $('#recentProjectsBtn');
    if (recentButton) recentButton.onclick = showRecentProjectsBatch2;
    const logsButton = $('#logsBtn');
    if (logsButton) logsButton.onclick = showLogsBatch2;
  }

  async function init() {
    if (initialized) return;
    initialized = true;
    installPresetFilter();
    wrapSelectionUi();
    wrapRenderTable();
    wrapReloadData();
    wrapJobModal();
    injectApplicationControls();
    installExportHistory();
    installButtonOverrides();
    await loadSavedViews();
    syncBatch2SelectionUi();
  }

  document.addEventListener('pywebviewready', () => setTimeout(init, 80));
  window.setTimeout(() => {
    if (!initialized && window.pywebview?.api) init();
  }, 260);
})();
