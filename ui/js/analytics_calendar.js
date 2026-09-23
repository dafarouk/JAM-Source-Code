(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const moduleState = {
    applications: [],
    events: [],
    settings: {},
    backups: [],
    notifications: [],
    currentMonth: new Date(new Date().getFullYear(), new Date().getMonth(), 1),
    selectedDate: '',
    analyticsInitialized: false,
    startupNotificationShown: false,
    initialized: false
  };

  const notificationDefinitions = [
    ['notify_interview_tomorrow', 'Interview tomorrow', 'Entretien demain'],
    ['notify_interview_hour', 'Interview soon', 'Entretien bientôt'],
    ['notify_followup_due', 'Follow-up due', 'Relance à faire'],
    ['notify_stale_application', 'Application needs attention', 'Candidature à vérifier'],
    ['notify_deadline', 'Deadline approaching', 'Échéance proche'],
    ['notify_unanalyzed', 'Unanalyzed applications', 'Candidatures non analysées'],
    ['notify_backup_stale', 'Backup reminder', 'Rappel de sauvegarde'],
    ['notify_upcoming_week', 'Upcoming week', 'Semaine à venir'],
    ['notify_inactivity', 'Search inactivity', 'Inactivité de recherche']
  ];

  function language() {
    return window.JAM_I18N?.language === 'fr' ? 'fr' : 'en';
  }

  function tr(en, fr) {
    return language() === 'fr' ? (fr || en) : en;
  }

  function esc(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  async function callApi(method, ...args) {
    const fn = window.pywebview?.api?.[method];
    if (!fn) throw new Error(tr('JAM backend is not ready yet.', 'Le moteur JAM n’est pas encore prêt.'));
    const result = await fn(...args);
    if (!result?.ok) throw new Error(result?.error || tr('Unknown JAM error.', 'Erreur JAM inconnue.'));
    return result;
  }

  function localDateKey(date) {
    if (!(date instanceof Date) || Number.isNaN(date.getTime())) return '';
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  function parseDate(value) {
    if (!value) return null;
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  function parseDateOnly(value) {
    const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!match) return null;
    return new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  }

  function startOfDay(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate());
  }

  function endOfDay(date) {
    return new Date(date.getFullYear(), date.getMonth(), date.getDate(), 23, 59, 59, 999);
  }

  function addDays(date, days) {
    const next = new Date(date);
    next.setDate(next.getDate() + days);
    return next;
  }

  function daysBetween(a, b) {
    const ms = startOfDay(b) - startOfDay(a);
    return Math.max(0, Math.round(ms / 86400000));
  }

  function formatDay(date, options = {}) {
    if (!date) return '—';
    return date.toLocaleDateString(language() === 'fr' ? 'fr-FR' : undefined, {
      year: options.year === false ? undefined : 'numeric',
      month: options.short ? 'short' : 'long',
      day: 'numeric'
    });
  }

  function formatDateTime(value) {
    const date = parseDate(value);
    if (!date) return '—';
    return date.toLocaleString(language() === 'fr' ? 'fr-FR' : undefined, {
      weekday: 'short',
      day: '2-digit',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function settingEnabled(key) {
    return String(moduleState.settings[key] ?? '1') !== '0';
  }

  async function refreshModuleData({ render = true, startup = false } = {}) {
    try {
      const result = await callApi('bootstrap');
      moduleState.applications = result.applications || [];
      moduleState.events = result.calendar_events || [];
      moduleState.settings = result.settings || {};
      moduleState.backups = result.backups || [];

      ensureAnalyticsRange();
      buildNotifications();
      renderNotificationSettings();
      renderNotificationCenter();

      if (render) {
        if ($('#analyticsPage')?.classList.contains('active')) renderAnalytics();
        if ($('#calendarPage')?.classList.contains('active')) renderCalendar();
      }

      if (startup && !moduleState.startupNotificationShown && moduleState.notifications.length) {
        moduleState.startupNotificationShown = true;
        const count = moduleState.notifications.length;
        if (typeof window.toast === 'function') {
          window.toast(
            count === 1
              ? tr('1 JAM reminder needs your attention.', '1 rappel JAM demande votre attention.')
              : tr(`${count} JAM reminders need your attention.`, `${count} rappels JAM demandent votre attention.`)
          );
        }
      }
    } catch (error) {
      console.error('JAM analytics/calendar refresh failed', error);
    }
  }

  // ============================================================
  // ANALYTICS
  // ============================================================

  function applicationDate(app, field) {
    return parseDate(app?.[field]);
  }

  function earliestApplicationDate() {
    const dates = moduleState.applications
      .map(app => applicationDate(app, 'date_saved'))
      .filter(Boolean)
      .sort((a, b) => a - b);
    return dates[0] || startOfDay(new Date());
  }

  function ensureAnalyticsRange(force = false) {
    const startInput = $('#analyticsStartDate');
    const endInput = $('#analyticsEndDate');
    if (!startInput || !endInput) return;

    const earliest = earliestApplicationDate();
    const today = startOfDay(new Date());
    startInput.min = localDateKey(earliest);
    startInput.max = localDateKey(today);
    endInput.min = localDateKey(earliest);
    endInput.max = localDateKey(today);

    if (force || !startInput.value) startInput.value = localDateKey(earliest);
    if (force || !endInput.value) endInput.value = localDateKey(today);

    if (startInput.value > endInput.value) startInput.value = endInput.value;
  }

  function analyticsRange() {
    const start = parseDateOnly($('#analyticsStartDate')?.value) || earliestApplicationDate();
    const end = parseDateOnly($('#analyticsEndDate')?.value) || startOfDay(new Date());
    return {
      start: startOfDay(start <= end ? start : end),
      end: endOfDay(start <= end ? end : start)
    };
  }

  function appsSavedInRange(start, end) {
    return moduleState.applications.filter(app => {
      const date = applicationDate(app, 'date_saved');
      return date && date >= start && date <= end;
    });
  }

  function appsAppliedInRange(start, end) {
    return moduleState.applications.filter(app => {
      const date = applicationDate(app, 'date_applied');
      return date && date >= start && date <= end;
    });
  }

  function bucketStart(date, mode) {
    if (mode === 'month') return new Date(date.getFullYear(), date.getMonth(), 1);
    if (mode === 'week') {
      const value = startOfDay(date);
      const mondayOffset = (value.getDay() + 6) % 7;
      return addDays(value, -mondayOffset);
    }
    return startOfDay(date);
  }

  function nextBucket(date, mode) {
    if (mode === 'month') return new Date(date.getFullYear(), date.getMonth() + 1, 1);
    if (mode === 'week') return addDays(date, 7);
    return addDays(date, 1);
  }

  function bucketLabel(date, mode) {
    const locale = language() === 'fr' ? 'fr-FR' : undefined;
    if (mode === 'month') return date.toLocaleDateString(locale, { month: 'short', year: '2-digit' });
    if (mode === 'week') return date.toLocaleDateString(locale, { day: '2-digit', month: 'short' });
    return date.toLocaleDateString(locale, { day: '2-digit', month: 'short' });
  }

  function buildTrendData(start, end) {
    const span = daysBetween(start, end);
    const mode = span > 210 ? 'month' : span > 50 ? 'week' : 'day';
    const first = bucketStart(start, mode);
    const last = bucketStart(end, mode);
    const map = new Map();

    for (let cursor = new Date(first); cursor <= last; cursor = nextBucket(cursor, mode)) {
      const key = localDateKey(cursor);
      map.set(key, { key, date: new Date(cursor), tracked: 0, applied: 0 });
    }

    moduleState.applications.forEach(app => {
      const saved = applicationDate(app, 'date_saved');
      if (saved && saved >= start && saved <= end) {
        const key = localDateKey(bucketStart(saved, mode));
        if (map.has(key)) map.get(key).tracked += 1;
      }

      const applied = applicationDate(app, 'date_applied');
      if (applied && applied >= start && applied <= end) {
        const key = localDateKey(bucketStart(applied, mode));
        if (map.has(key)) map.get(key).applied += 1;
      }
    });

    return { mode, rows: [...map.values()] };
  }

  function svgPath(points) {
    if (!points.length) return '';
    return points.map((point, index) => `${index ? 'L' : 'M'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ');
  }

  function renderTrendChart(start, end) {
    const root = $('#analyticsTrendChart');
    if (!root) return;

    const { mode, rows } = buildTrendData(start, end);
    const hasData = rows.some(row => row.tracked || row.applied);
    if (!rows.length || !hasData) {
      root.innerHTML = `<div class="analytics-chart-empty">${tr('No application activity in this period.', 'Aucune activité de candidature sur cette période.')}</div>`;
      return;
    }

    const width = 920;
    const height = 290;
    const left = 42;
    const right = 18;
    const top = 18;
    const bottom = 42;
    const plotWidth = width - left - right;
    const plotHeight = height - top - bottom;
    const maxValue = Math.max(1, ...rows.flatMap(row => [row.tracked, row.applied]));
    const yMax = Math.max(4, Math.ceil(maxValue / 4) * 4);
    const xStep = rows.length > 1 ? plotWidth / (rows.length - 1) : 0;
    const toY = value => top + plotHeight - (value / yMax) * plotHeight;
    const trackedPoints = rows.map((row, index) => ({ x: left + xStep * index, y: toY(row.tracked), row }));
    const appliedPoints = rows.map((row, index) => ({ x: left + xStep * index, y: toY(row.applied), row }));
    const trackedPath = svgPath(trackedPoints);
    const appliedPath = svgPath(appliedPoints);
    const baseline = top + plotHeight;
    const areaPath = `${trackedPath} L ${trackedPoints.at(-1).x.toFixed(1)} ${baseline} L ${trackedPoints[0].x.toFixed(1)} ${baseline} Z`;
    const grid = [0, 1, 2, 3, 4].map(index => {
      const value = Math.round((yMax / 4) * index);
      const y = toY(value);
      return `<line class="grid-line" x1="${left}" y1="${y}" x2="${width - right}" y2="${y}"></line><text class="axis-text" x="${left - 8}" y="${y + 3}" text-anchor="end">${value}</text>`;
    }).join('');
    const labelStep = Math.max(1, Math.ceil(rows.length / 8));
    const xLabels = rows.map((row, index) => {
      if (index % labelStep !== 0 && index !== rows.length - 1) return '';
      return `<text class="axis-text" x="${left + xStep * index}" y="${height - 13}" text-anchor="middle">${esc(bucketLabel(row.date, mode))}</text>`;
    }).join('');
    const trackedCircles = trackedPoints.map(point => `<circle class="trend-point" cx="${point.x}" cy="${point.y}" r="3.5"><title>${esc(bucketLabel(point.row.date, mode))}: ${point.row.tracked} ${tr('tracked', 'suivies')}</title></circle>`).join('');
    const appliedCircles = appliedPoints.map(point => `<circle class="applied-point" cx="${point.x}" cy="${point.y}" r="3"><title>${esc(bucketLabel(point.row.date, mode))}: ${point.row.applied} ${tr('applied', 'envoyées')}</title></circle>`).join('');

    root.innerHTML = `
      <svg class="analytics-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(tr('Application trend chart', 'Courbe des candidatures'))}">
        <defs>
          <linearGradient id="jamTrendArea" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stop-color="#d0aa70" stop-opacity=".22"></stop>
            <stop offset="1" stop-color="#d0aa70" stop-opacity="0"></stop>
          </linearGradient>
        </defs>
        ${grid}
        ${xLabels}
        <path class="tracked-area" d="${areaPath}"></path>
        <path class="tracked-line" d="${trackedPath}"></path>
        <path class="applied-line" d="${appliedPath}"></path>
        ${trackedCircles}
        ${appliedCircles}
      </svg>`;
  }

  function renderAnalyticsBars(apps) {
    const sourcesRoot = $('#analyticsSources');
    const statusesRoot = $('#analyticsStatuses');
    if (!sourcesRoot || !statusesRoot) return;

    const sourceCounts = new Map();
    apps.forEach(app => {
      const source = String(app.source || '').trim() || tr('Unknown', 'Inconnue');
      sourceCounts.set(source, (sourceCounts.get(source) || 0) + 1);
    });
    const sources = [...sourceCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8);
    const maxSource = Math.max(1, ...sources.map(([, count]) => count));
    sourcesRoot.innerHTML = sources.length
      ? sources.map(([name, count]) => `
          <div class="analytics-bar-row">
            <div class="analytics-bar-top"><span>${esc(name)}</span><strong>${count}</strong></div>
            <div class="analytics-bar-track"><i style="width:${Math.max(6, (count / maxSource) * 100)}%"></i></div>
          </div>`).join('')
      : `<div class="calendar-empty-small">${tr('No source data in this period.', 'Aucune donnée de source sur cette période.')}</div>`;

    const order = ['Saved', 'To Review', 'Applied', 'Interviewing', 'Offer', 'Accepted', 'Rejected', 'Withdrawn', 'Archived'];
    const statusCounts = new Map(order.map(status => [status, 0]));
    apps.forEach(app => statusCounts.set(app.status || 'Saved', (statusCounts.get(app.status || 'Saved') || 0) + 1));
    const maxStatus = Math.max(1, ...statusCounts.values());
    statusesRoot.innerHTML = order
      .filter(status => statusCounts.get(status) > 0)
      .map(status => `
        <div class="analytics-status-row">
          <span>${esc(status)}</span>
          <div class="analytics-status-meter"><i style="width:${(statusCounts.get(status) / maxStatus) * 100}%"></i></div>
          <strong>${statusCounts.get(status)}</strong>
        </div>`).join('') || `<div class="calendar-empty-small">${tr('No status data in this period.', 'Aucune donnée de statut sur cette période.')}</div>`;
  }

  function renderAnalytics() {
    ensureAnalyticsRange();
    const { start, end } = analyticsRange();
    const tracked = appsSavedInRange(start, end);
    const applied = appsAppliedInRange(start, end);
    const scored = tracked.map(app => Number(app.match_score)).filter(Number.isFinite);
    const avg = scored.length ? Math.round(scored.reduce((a, b) => a + b, 0) / scored.length) : 0;
    const interviews = tracked.filter(app => app.status === 'Interviewing').length;

    if ($('#analyticsTracked')) $('#analyticsTracked').textContent = String(tracked.length);
    if ($('#analyticsApplied')) $('#analyticsApplied').textContent = String(applied.length);
    if ($('#analyticsAvgScore')) $('#analyticsAvgScore').textContent = `${avg}%`;
    if ($('#analyticsInterviews')) $('#analyticsInterviews').textContent = String(interviews);

    renderTrendChart(start, end);
    renderAnalyticsBars(tracked);
    localizeFeatureUI();
  }

  function setAnalyticsPreset(days) {
    const today = startOfDay(new Date());
    const earliest = earliestApplicationDate();
    const start = days === null ? earliest : new Date(Math.max(earliest.getTime(), addDays(today, -(days - 1)).getTime()));
    $('#analyticsStartDate').value = localDateKey(start);
    $('#analyticsEndDate').value = localDateKey(today);
    renderAnalytics();
  }

  function bindAnalytics() {
    const start = $('#analyticsStartDate');
    if (!start || start.dataset.jamBound === '1') return;
    start.dataset.jamBound = '1';
    $('#analyticsEndDate')?.addEventListener('change', renderAnalytics);
    start.addEventListener('change', renderAnalytics);
    $('#analyticsAllBtn')?.addEventListener('click', () => setAnalyticsPreset(null));
    $('#analytics30Btn')?.addEventListener('click', () => setAnalyticsPreset(30));
    $('#analytics90Btn')?.addEventListener('click', () => setAnalyticsPreset(90));
  }

  // ============================================================
  // CALENDAR
  // ============================================================

  function eventsForDate(key) {
    return moduleState.events.filter(event => localDateKey(parseDate(event.event_at)) === key);
  }

  function applicationsForDate(key) {
    return moduleState.applications.filter(app => {
      const date = parseDate(app.date_applied || app.date_saved);
      return localDateKey(date) === key;
    });
  }

  function eventTypeLabel(type) {
    const map = {
      Interview: tr('Interview', 'Entretien'),
      'Follow-up': tr('Follow-up', 'Relance'),
      Deadline: tr('Deadline', 'Échéance'),
      Reminder: tr('Reminder', 'Rappel'),
      Other: tr('Other', 'Autre')
    };
    return map[type] || type;
  }

  function renderCalendarDayDetails() {
    const key = moduleState.selectedDate || localDateKey(new Date());
    const date = parseDateOnly(key) || new Date();
    const label = $('#calendarSelectedLabel');
    const root = $('#calendarSelectedItems');
    if (label) label.textContent = formatDay(date);
    if (!root) return;

    const dayEvents = eventsForDate(key).sort((a, b) => String(a.event_at).localeCompare(String(b.event_at)));
    const dayApps = applicationsForDate(key);
    const blocks = [];

    dayEvents.forEach(event => {
      const appLabel = [event.application_company, event.application_job_title].filter(Boolean).join(' · ');
      blocks.push(`
        <div class="calendar-detail-item" data-calendar-event-id="${event.id}">
          <div class="calendar-detail-top">
            <div>
              <span class="calendar-event-type">${esc(eventTypeLabel(event.event_type))}</span>
              <strong style="display:block;margin-top:6px">${esc(event.title || eventTypeLabel(event.event_type))}</strong>
              <small>${esc(formatDateTime(event.event_at))}${event.location ? ` · ${esc(event.location)}` : ''}${appLabel ? `<br>${esc(appLabel)}` : ''}</small>
            </div>
          </div>
          ${event.notes ? `<small>${esc(event.notes)}</small>` : ''}
          <div class="calendar-item-actions">
            <button type="button" data-calendar-edit="${event.id}">${tr('Edit', 'Modifier')}</button>
            <button type="button" data-calendar-complete="${event.id}">${Number(event.completed) ? tr('Reopen', 'Rouvrir') : tr('Complete', 'Terminer')}</button>
            <button type="button" data-calendar-delete="${event.id}">${tr('Delete', 'Supprimer')}</button>
          </div>
        </div>`);
    });

    dayApps.forEach(app => {
      const applied = Boolean(app.date_applied);
      blocks.push(`
        <div class="calendar-detail-item">
          <span class="calendar-event-type">${applied ? tr('Applied', 'Envoyée') : tr('Saved', 'Enregistrée')}</span>
          <strong style="display:block;margin-top:6px">${esc(app.company || tr('Unknown company', 'Entreprise inconnue'))}</strong>
          <small>${esc(app.job_title || tr('Untitled role', 'Poste sans titre'))}</small>
          <div class="calendar-item-actions"><button type="button" data-calendar-open-app="${app.id}">${tr('Open application', 'Ouvrir la candidature')}</button></div>
        </div>`);
    });

    root.innerHTML = blocks.length ? blocks.join('') : `<div class="calendar-empty-small">${tr('Nothing scheduled or tracked on this day.', 'Aucun événement ou candidature ce jour-là.')}</div>`;
    bindCalendarItemActions(root);
  }

  function renderUpcoming() {
    const root = $('#calendarUpcoming');
    if (!root) return;
    const now = new Date();
    const limit = addDays(now, 30);
    const items = moduleState.events
      .filter(event => !Number(event.completed))
      .filter(event => {
        const date = parseDate(event.event_at);
        return date && date >= now && date <= limit;
      })
      .sort((a, b) => String(a.event_at).localeCompare(String(b.event_at)))
      .slice(0, 10);

    root.innerHTML = items.length ? items.map(event => `
      <div class="calendar-detail-item">
        <span class="calendar-event-type">${esc(eventTypeLabel(event.event_type))}</span>
        <strong style="display:block;margin-top:6px">${esc(event.title || eventTypeLabel(event.event_type))}</strong>
        <small>${esc(formatDateTime(event.event_at))}${event.application_company ? `<br>${esc(event.application_company)}${event.application_job_title ? ` · ${esc(event.application_job_title)}` : ''}` : ''}</small>
        <div class="calendar-item-actions"><button type="button" data-calendar-jump="${esc(localDateKey(parseDate(event.event_at)))}">${tr('Show day', 'Voir le jour')}</button></div>
      </div>`).join('') : `<div class="calendar-empty-small">${tr('No upcoming calendar events.', 'Aucun événement à venir.')}</div>`;

    $$('[data-calendar-jump]', root).forEach(button => {
      button.addEventListener('click', () => {
        const date = parseDateOnly(button.dataset.calendarJump);
        if (!date) return;
        moduleState.currentMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        moduleState.selectedDate = localDateKey(date);
        renderCalendar();
      });
    });
  }

  function renderCalendar() {
    const month = moduleState.currentMonth;
    const monthLabel = $('#calendarMonthLabel');
    const weekdaysRoot = $('#calendarWeekdays');
    const grid = $('#calendarGrid');
    if (!monthLabel || !weekdaysRoot || !grid) return;

    const locale = language() === 'fr' ? 'fr-FR' : undefined;
    monthLabel.textContent = month.toLocaleDateString(locale, { month: 'long', year: 'numeric' });
    const weekdays = language() === 'fr'
      ? ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
      : ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    weekdaysRoot.innerHTML = weekdays.map(day => `<span>${day}</span>`).join('');

    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    const offset = (first.getDay() + 6) % 7;
    const start = addDays(first, -offset);
    const todayKey = localDateKey(new Date());
    if (!moduleState.selectedDate) moduleState.selectedDate = todayKey;

    const cells = [];
    for (let index = 0; index < 42; index += 1) {
      const date = addDays(start, index);
      const key = localDateKey(date);
      const dayEvents = eventsForDate(key).sort((a, b) => String(a.event_at).localeCompare(String(b.event_at)));
      const dayApps = applicationsForDate(key);
      const entries = [
        ...dayEvents.map(event => ({ kind: 'event', id: event.id, text: `${eventTypeLabel(event.event_type)} · ${event.title || eventTypeLabel(event.event_type)}`, completed: Number(event.completed) })),
        ...dayApps.map(app => ({ kind: 'application', id: app.id, text: `${app.date_applied ? tr('Applied', 'Envoyée') : tr('Saved', 'Enregistrée')} · ${app.company || app.job_title || 'JAM'}` }))
      ];
      const visible = entries.slice(0, 3);
      const outside = date.getMonth() !== month.getMonth();
      const classes = ['calendar-day', outside ? 'outside' : '', key === todayKey ? 'today' : '', key === moduleState.selectedDate ? 'selected' : ''].filter(Boolean).join(' ');
      cells.push(`
        <button type="button" class="${classes}" data-calendar-day="${key}">
          <span class="calendar-day-number">${date.getDate()}</span>
          <span class="calendar-day-items">
            ${visible.map(item => `<span class="calendar-chip ${item.kind === 'application' ? 'application' : ''} ${item.completed ? 'completed' : ''}">${esc(item.text)}</span>`).join('')}
            ${entries.length > 3 ? `<span class="calendar-more">+${entries.length - 3} ${tr('more', 'autre(s)')}</span>` : ''}
          </span>
        </button>`);
    }
    grid.innerHTML = cells.join('');

    $$('[data-calendar-day]', grid).forEach(button => {
      button.addEventListener('click', () => {
        moduleState.selectedDate = button.dataset.calendarDay;
        const date = parseDateOnly(moduleState.selectedDate);
        if (date && date.getMonth() !== moduleState.currentMonth.getMonth()) {
          moduleState.currentMonth = new Date(date.getFullYear(), date.getMonth(), 1);
        }
        renderCalendar();
      });
    });

    renderCalendarDayDetails();
    renderUpcoming();
    localizeFeatureUI();
  }

  function bindCalendarItemActions(root) {
    $$('[data-calendar-edit]', root).forEach(button => button.addEventListener('click', () => {
      const item = moduleState.events.find(event => Number(event.id) === Number(button.dataset.calendarEdit));
      if (item) openCalendarEventModal(item);
    }));

    $$('[data-calendar-complete]', root).forEach(button => button.addEventListener('click', async () => {
      const item = moduleState.events.find(event => Number(event.id) === Number(button.dataset.calendarComplete));
      if (!item) return;
      try {
        const result = await callApi('set_calendar_event_completed', item.id, !Number(item.completed));
        moduleState.events = result.events || [];
        buildNotifications();
        renderCalendar();
        renderNotificationCenter();
      } catch (error) {
        if (typeof window.toast === 'function') window.toast(error.message, 'error');
      }
    }));

    $$('[data-calendar-delete]', root).forEach(button => button.addEventListener('click', async () => {
      const id = Number(button.dataset.calendarDelete);
      const item = moduleState.events.find(event => Number(event.id) === id);
      if (!item) return;
      let confirmed = true;
      if (typeof window.confirmDialog === 'function') {
        confirmed = await window.confirmDialog(
          tr('Delete calendar event?', 'Supprimer l’événement ?'),
          tr('This reminder will be removed from the calendar.', 'Ce rappel sera supprimé du calendrier.'),
          tr('Delete', 'Supprimer')
        );
      } else {
        confirmed = window.confirm(tr('Delete this calendar event?', 'Supprimer cet événement ?'));
      }
      if (!confirmed) return;
      try {
        const result = await callApi('delete_calendar_event', id);
        moduleState.events = result.events || [];
        buildNotifications();
        renderCalendar();
        renderNotificationCenter();
      } catch (error) {
        if (typeof window.toast === 'function') window.toast(error.message, 'error');
      }
    }));

    $$('[data-calendar-open-app]', root).forEach(button => button.addEventListener('click', () => {
      const app = moduleState.applications.find(item => Number(item.id) === Number(button.dataset.calendarOpenApp));
      if (app && typeof window.openJobModal === 'function') window.openJobModal(app);
    }));
  }

  function openCalendarEventModal(existing = null) {
    if (typeof window.openModal !== 'function') return;
    const selected = parseDateOnly(moduleState.selectedDate) || new Date();
    const defaultDateTime = `${localDateKey(selected)}T09:00`;
    const value = existing?.event_at ? String(existing.event_at).slice(0, 16) : defaultDateTime;
    const applications = [...moduleState.applications].sort((a, b) => String(a.company || '').localeCompare(String(b.company || '')));
    const appOptions = applications.map(app => `<option value="${app.id}" ${Number(existing?.application_id) === Number(app.id) ? 'selected' : ''}>${esc(`${app.company || tr('Unknown company', 'Entreprise inconnue')} — ${app.job_title || tr('Untitled role', 'Poste sans titre')}`)}</option>`).join('');
    const root = window.openModal({
      kicker: tr('CALENDAR', 'CALENDRIER'),
      title: existing ? tr('Edit event', 'Modifier l’événement') : tr('Add event', 'Ajouter un événement'),
      body: `
        <div class="form-grid" id="calendarEventForm">
          <label>${tr('Type', 'Type')}
            <select id="calendarEventType" class="control full">
              ${['Interview', 'Follow-up', 'Deadline', 'Reminder', 'Other'].map(type => `<option value="${type}" ${existing?.event_type === type ? 'selected' : ''}>${esc(eventTypeLabel(type))}</option>`).join('')}
            </select>
          </label>
          <label>${tr('Date & time', 'Date et heure')}<input id="calendarEventAt" class="control full" type="datetime-local" value="${esc(value)}"></label>
          <label class="span-2">${tr('Title', 'Titre')}<input id="calendarEventTitle" class="control full" type="text" value="${esc(existing?.title || '')}" placeholder="${esc(tr('Interview with...', 'Entretien avec...'))}"></label>
          <label class="span-2">${tr('Linked application', 'Candidature liée')}
            <select id="calendarEventApplication" class="control full"><option value="">${tr('No linked application', 'Aucune candidature liée')}</option>${appOptions}</select>
          </label>
          <label class="span-2">${tr('Location / link', 'Lieu / lien')}<input id="calendarEventLocation" class="control full" type="text" value="${esc(existing?.location || '')}" placeholder="Teams, Meet, office..."></label>
          <label class="span-2">${tr('Notes', 'Notes')}<textarea id="calendarEventNotes" class="control full" placeholder="${esc(tr('Useful details...', 'Détails utiles...'))}">${esc(existing?.notes || '')}</textarea></label>
        </div>`,
      actions: `<button class="btn secondary" data-calendar-cancel>${tr('Cancel', 'Annuler')}</button><button class="btn gold" data-calendar-save>${tr('Save event', 'Enregistrer')}</button>`
    });

    $('[data-calendar-cancel]', root)?.addEventListener('click', () => window.closeModal?.());
    $('[data-calendar-save]', root)?.addEventListener('click', async () => {
      const payload = {
        id: existing?.id || null,
        event_type: $('#calendarEventType', root)?.value || 'Reminder',
        event_at: $('#calendarEventAt', root)?.value || '',
        title: $('#calendarEventTitle', root)?.value?.trim() || '',
        application_id: $('#calendarEventApplication', root)?.value || null,
        location: $('#calendarEventLocation', root)?.value?.trim() || '',
        notes: $('#calendarEventNotes', root)?.value?.trim() || '',
        completed: existing?.completed || 0
      };
      try {
        const result = await callApi('save_calendar_event', payload);
        moduleState.events = result.events || [];
        const savedDate = parseDate(result.item?.event_at);
        if (savedDate) {
          moduleState.currentMonth = new Date(savedDate.getFullYear(), savedDate.getMonth(), 1);
          moduleState.selectedDate = localDateKey(savedDate);
        }
        window.closeModal?.();
        buildNotifications();
        renderCalendar();
        renderNotificationCenter();
        if (typeof window.toast === 'function') window.toast(tr('Calendar event saved.', 'Événement enregistré.'));
      } catch (error) {
        if (typeof window.toast === 'function') window.toast(error.message, 'error');
      }
    });
  }

  function bindCalendar() {
    const previous = $('#calendarPrevBtn');
    if (!previous || previous.dataset.jamBound === '1') return;
    previous.dataset.jamBound = '1';
    previous.addEventListener('click', () => {
      moduleState.currentMonth = new Date(moduleState.currentMonth.getFullYear(), moduleState.currentMonth.getMonth() - 1, 1);
      renderCalendar();
    });
    $('#calendarNextBtn')?.addEventListener('click', () => {
      moduleState.currentMonth = new Date(moduleState.currentMonth.getFullYear(), moduleState.currentMonth.getMonth() + 1, 1);
      renderCalendar();
    });
    $('#calendarTodayBtn')?.addEventListener('click', () => {
      const today = new Date();
      moduleState.currentMonth = new Date(today.getFullYear(), today.getMonth(), 1);
      moduleState.selectedDate = localDateKey(today);
      renderCalendar();
    });
    $('#calendarAddEventBtn')?.addEventListener('click', () => openCalendarEventModal());
  }

  // ============================================================
  // NOTIFICATIONS
  // ============================================================

  function notification(id, category, title, message, options = {}) {
    return {
      id,
      category,
      title,
      message,
      severity: options.severity || 'normal',
      action: options.action || null,
      eventDate: options.eventDate || null
    };
  }

  function buildNotifications() {
    if (!settingEnabled('notifications_enabled')) {
      moduleState.notifications = [];
      return;
    }

    const now = new Date();
    const notes = [];
    const activeEvents = moduleState.events.filter(event => !Number(event.completed));

    activeEvents.forEach(event => {
      const date = parseDate(event.event_at);
      if (!date) return;
      const hours = (date - now) / 3600000;
      const title = event.title || eventTypeLabel(event.event_type);

      if (event.event_type === 'Interview') {
        if (settingEnabled('notify_interview_hour') && hours >= 0 && hours <= 1.5) {
          notes.push(notification(`interview-hour-${event.id}`, 'notify_interview_hour', tr('Interview soon', 'Entretien bientôt'), `${title} · ${formatDateTime(event.event_at)}`, { severity: 'urgent', action: { type: 'calendar', date: localDateKey(date) }, eventDate: date }));
        } else if (settingEnabled('notify_interview_tomorrow') && hours > 12 && hours <= 36) {
          notes.push(notification(`interview-tomorrow-${event.id}`, 'notify_interview_tomorrow', tr('Interview tomorrow', 'Entretien demain'), `${title} · ${formatDateTime(event.event_at)}`, { severity: 'warning', action: { type: 'calendar', date: localDateKey(date) }, eventDate: date }));
        }
      }

      if (event.event_type === 'Follow-up' && settingEnabled('notify_followup_due') && hours >= -72 && hours <= 12) {
        notes.push(notification(`followup-${event.id}`, 'notify_followup_due', hours < 0 ? tr('Follow-up overdue', 'Relance en retard') : tr('Follow-up due', 'Relance à faire'), `${title} · ${formatDateTime(event.event_at)}`, { severity: hours < 0 ? 'warning' : 'normal', action: { type: 'calendar', date: localDateKey(date) }, eventDate: date }));
      }

      if (event.event_type === 'Deadline' && settingEnabled('notify_deadline') && hours >= 0 && hours <= 36) {
        notes.push(notification(`deadline-${event.id}`, 'notify_deadline', tr('Deadline approaching', 'Échéance proche'), `${title} · ${formatDateTime(event.event_at)}`, { severity: 'warning', action: { type: 'calendar', date: localDateKey(date) }, eventDate: date }));
      }
    });

    if (settingEnabled('notify_stale_application')) {
      moduleState.applications
        .filter(app => !['Accepted', 'Rejected', 'Withdrawn', 'Archived'].includes(app.status))
        .map(app => ({ app, date: parseDate(app.updated_at || app.date_saved) }))
        .filter(item => item.date && (now - item.date) / 86400000 >= 10)
        .sort((a, b) => a.date - b.date)
        .slice(0, 5)
        .forEach(({ app, date }) => {
          const days = Math.floor((now - date) / 86400000);
          notes.push(notification(`stale-${app.id}`, 'notify_stale_application', tr('Application needs attention', 'Candidature à vérifier'), `${app.company || tr('Unknown company', 'Entreprise inconnue')} · ${app.job_title || tr('Untitled role', 'Poste sans titre')} · ${days} ${tr('days', 'jours')}`, { action: { type: 'application', id: app.id } }));
        });
    }

    if (settingEnabled('notify_unanalyzed')) {
      const unanalyzed = moduleState.applications.filter(app => app.match_score === null || app.match_score === undefined || app.match_score === '');
      if (unanalyzed.length) {
        notes.push(notification('unanalyzed-summary', 'notify_unanalyzed', tr('Unanalyzed applications', 'Candidatures non analysées'), tr(`${unanalyzed.length} saved job(s) still have no Analyzer score.`, `${unanalyzed.length} offre(s) n’ont pas encore de score Analyseur.`), { action: { type: 'applications' } }));
      }
    }

    if (settingEnabled('notify_backup_stale') && moduleState.applications.length) {
      const latest = moduleState.backups.map(item => parseDate(item.created_at)).filter(Boolean).sort((a, b) => b - a)[0];
      if (!latest || (now - latest) / 86400000 >= 7) {
        notes.push(notification('backup-stale', 'notify_backup_stale', tr('Backup reminder', 'Rappel de sauvegarde'), latest ? tr('Your latest JAM backup is more than 7 days old.', 'Votre dernière sauvegarde JAM date de plus de 7 jours.') : tr('No JAM backup was found yet.', 'Aucune sauvegarde JAM n’a encore été trouvée.'), { action: { type: 'settings' } }));
      }
    }

    if (settingEnabled('notify_upcoming_week')) {
      const upcoming = activeEvents.filter(event => {
        const date = parseDate(event.event_at);
        if (!date) return false;
        const hours = (date - now) / 3600000;
        return hours >= 0 && hours <= 168;
      });
      if (upcoming.length) {
        notes.push(notification('upcoming-week', 'notify_upcoming_week', tr('Upcoming week', 'Semaine à venir'), tr(`${upcoming.length} calendar event(s) are scheduled in the next 7 days.`, `${upcoming.length} événement(s) sont prévus dans les 7 prochains jours.`), { action: { type: 'calendar' } }));
      }
    }

    if (settingEnabled('notify_inactivity') && moduleState.applications.length) {
      const latest = moduleState.applications.map(app => parseDate(app.date_saved)).filter(Boolean).sort((a, b) => b - a)[0];
      if (latest && (now - latest) / 86400000 >= 3) {
        const days = Math.floor((now - latest) / 86400000);
        notes.push(notification('search-inactivity', 'notify_inactivity', tr('Search inactivity', 'Inactivité de recherche'), tr(`No new application has been saved for ${days} days.`, `Aucune nouvelle candidature enregistrée depuis ${days} jours.`), { action: { type: 'applications' } }));
      }
    }

    moduleState.notifications = notes.sort((a, b) => {
      const priority = { urgent: 0, warning: 1, normal: 2 };
      const diff = (priority[a.severity] ?? 2) - (priority[b.severity] ?? 2);
      if (diff) return diff;
      return (a.eventDate?.getTime() || Infinity) - (b.eventDate?.getTime() || Infinity);
    });
  }

  function renderNotificationSettings() {
    const master = $('#notificationsEnabled');
    if (master) master.checked = settingEnabled('notifications_enabled');
    $$('[data-notification-setting]').forEach(input => {
      input.checked = settingEnabled(input.dataset.notificationSetting);
    });
  }

  function notificationIcon(item) {
    if (item.category.includes('interview')) return '◉';
    if (item.category.includes('deadline')) return '!';
    if (item.category.includes('followup')) return '↻';
    if (item.category.includes('backup')) return '▣';
    if (item.category.includes('unanalyzed')) return '◎';
    if (item.category.includes('inactivity')) return '…';
    return '•';
  }

  function renderNotificationCenter() {
    const badge = $('#notificationBadge');
    const root = $('#notificationList');
    const summary = $('#notificationDrawerSummary');
    const count = moduleState.notifications.length;
    if (badge) {
      badge.hidden = count === 0;
      badge.textContent = count > 99 ? '99+' : String(count);
    }
    if (summary) summary.textContent = count ? tr(`${count} active reminder(s) based on your current JAM data.`, `${count} rappel(s) actif(s) selon vos données JAM.`) : tr('You are all caught up.', 'Aucun rappel en attente.');
    if (!root) return;

    root.innerHTML = count ? moduleState.notifications.map(item => `
      <div class="notification-item ${esc(item.severity)}">
        <div class="notification-item-top">
          <span class="notification-item-icon">${notificationIcon(item)}</span>
          <div class="notification-item-body">
            <strong>${esc(item.title)}</strong>
            <small>${esc(item.message)}</small>
            ${item.action ? `<button class="notification-action" type="button" data-notification-action="${esc(item.id)}">${tr('Open', 'Ouvrir')} →</button>` : ''}
          </div>
        </div>
      </div>`).join('') : `<div class="calendar-empty-small">${tr('No active notifications.', 'Aucune notification active.')}</div>`;

    $$('[data-notification-action]', root).forEach(button => button.addEventListener('click', () => {
      const item = moduleState.notifications.find(note => note.id === button.dataset.notificationAction);
      if (!item?.action) return;
      $('#notificationDrawer').hidden = true;
      const action = item.action;
      if (action.type === 'calendar') {
        if (action.date) {
          const date = parseDateOnly(action.date);
          if (date) {
            moduleState.currentMonth = new Date(date.getFullYear(), date.getMonth(), 1);
            moduleState.selectedDate = action.date;
          }
        }
        window.navigate?.('calendar');
        renderCalendar();
      } else if (action.type === 'application') {
        const app = moduleState.applications.find(candidate => Number(candidate.id) === Number(action.id));
        if (app && typeof window.openJobModal === 'function') window.openJobModal(app);
        else window.navigate?.('applications');
      } else if (action.type === 'settings') {
        window.navigate?.('settings');
      } else {
        window.navigate?.('applications');
      }
    }));
  }

  async function saveNotificationSettings() {
    const values = {
      notifications_enabled: $('#notificationsEnabled')?.checked ? '1' : '0'
    };
    $$('[data-notification-setting]').forEach(input => {
      values[input.dataset.notificationSetting] = input.checked ? '1' : '0';
    });

    try {
      const result = await callApi('save_notification_settings', values);
      moduleState.settings = result.settings || { ...moduleState.settings, ...values };
      buildNotifications();
      renderNotificationCenter();
      if (typeof window.toast === 'function') window.toast(tr('Notification settings saved.', 'Paramètres de notification enregistrés.'));
    } catch (error) {
      if (typeof window.toast === 'function') window.toast(error.message, 'error');
    }
  }

  function bindNotifications() {
    const bell = $('#notificationBellBtn');
    if (!bell || bell.dataset.jamBound === '1') return;
    bell.dataset.jamBound = '1';
    bell.addEventListener('click', async () => {
      await refreshModuleData({ render: false });
      const drawer = $('#notificationDrawer');
      if (drawer) drawer.hidden = !drawer.hidden;
    });
    $('#notificationDrawerClose')?.addEventListener('click', () => { $('#notificationDrawer').hidden = true; });
    $('#saveNotificationSettingsBtn')?.addEventListener('click', saveNotificationSettings);
  }

  // ============================================================
  // LOCALIZATION / INTEGRATION
  // ============================================================

  function localizeFeatureUI() {
    const textMap = [
      ['[data-page="analytics"] b', 'Analytics', 'Statistiques'],
      ['[data-page="calendar"] b', 'Calendar', 'Calendrier'],
      ['#analyticsPage .analytics-toolbar h2', 'Job search analytics', 'Statistiques de recherche'],
      ['#analyticsPage .analytics-toolbar p', 'See how your application activity changes over time using your own JAM data.', 'Suivez l’évolution de vos candidatures à partir de vos propres données JAM.'],
      ['#analyticsAllBtn', 'All data', 'Toutes les données'],
      ['#analytics30Btn', '30 days', '30 jours'],
      ['#analytics90Btn', '90 days', '90 jours'],
      ['#calendarPage .calendar-toolbar h2', 'Application calendar', 'Calendrier des candidatures'],
      ['#calendarPage .calendar-toolbar p', 'See applications by date and keep interviews, follow-ups and deadlines in one place.', 'Visualisez vos candidatures par date et centralisez entretiens, relances et échéances.'],
      ['#calendarTodayBtn', 'Today', 'Aujourd’hui'],
      ['#calendarAddEventBtn', '+ Add event', '+ Ajouter un événement'],
      ['#saveNotificationSettingsBtn', 'Save notification settings', 'Enregistrer les notifications']
    ];
    textMap.forEach(([selector, en, fr]) => {
      const node = $(selector);
      if (node) node.textContent = tr(en, fr);
    });

    const page = $('.page.active');
    if (page?.id === 'analyticsPage') {
      if ($('#pageEyebrow')) $('#pageEyebrow').textContent = tr('APPLICATION TRENDS', 'TENDANCES DES CANDIDATURES');
      if ($('#pageTitle')) $('#pageTitle').textContent = tr('Analytics', 'Statistiques');
    } else if (page?.id === 'calendarPage') {
      if ($('#pageEyebrow')) $('#pageEyebrow').textContent = tr('PLANNING & REMINDERS', 'PLANNING ET RAPPELS');
      if ($('#pageTitle')) $('#pageTitle').textContent = tr('Calendar', 'Calendrier');
    }
  }

  function patchNavigation() {
    const current = window.navigate;
    if (typeof current !== 'function' || current.__jamAnalyticsCalendarPatched) return;
    const patched = function(page) {
      const result = current(page);
      if (page === 'analytics') {
        refreshModuleData({ render: false }).then(() => renderAnalytics());
      } else if (page === 'calendar') {
        refreshModuleData({ render: false }).then(() => renderCalendar());
      }
      localizeFeatureUI();
      return result;
    };
    patched.__jamAnalyticsCalendarPatched = true;
    window.navigate = patched;
    try { navigate = patched; } catch (_) {}
  }

  function patchReloadData() {
    const current = window.reloadData;
    if (typeof current !== 'function' || current.__jamAnalyticsCalendarPatched) return;
    const patched = async function(...args) {
      const result = await current(...args);
      await refreshModuleData({ render: true });
      return result;
    };
    patched.__jamAnalyticsCalendarPatched = true;
    window.reloadData = patched;
    try { reloadData = patched; } catch (_) {}
  }

  function init() {
    if (moduleState.initialized) return;
    moduleState.initialized = true;
    try {
      if (typeof PAGE_META === 'object') {
        PAGE_META.analytics = ['APPLICATION TRENDS', 'Analytics'];
        PAGE_META.calendar = ['PLANNING & REMINDERS', 'Calendar'];
      }
    } catch (_) {}

    bindAnalytics();
    bindCalendar();
    bindNotifications();
    patchNavigation();
    patchReloadData();
    ensureAnalyticsRange(true);
    localizeFeatureUI();
    refreshModuleData({ render: true, startup: true });
  }

  const languageObserver = new MutationObserver(() => {
    localizeFeatureUI();
    renderNotificationSettings();
    renderNotificationCenter();
    if ($('#analyticsPage')?.classList.contains('active')) renderAnalytics();
    if ($('#calendarPage')?.classList.contains('active')) renderCalendar();
  });
  languageObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['lang'] });

  window.JAM_PLANNER = {
    refresh: () => refreshModuleData({ render: true }),
    openEvent: openCalendarEventModal,
    get notifications() { return [...moduleState.notifications]; }
  };

  document.addEventListener('pywebviewready', init, { once: true });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => window.setTimeout(() => {
      if (window.pywebview?.api) init();
    }, 150), { once: true });
  } else {
    window.setTimeout(() => { if (window.pywebview?.api) init(); }, 150);
  }
})();
