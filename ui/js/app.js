const STATUSES = [
  'Saved',
  'To Review',
  'Applied',
  'Interviewing',
  'Offer',
  'Accepted',
  'Rejected',
  'Withdrawn',
  'Archived'
];

const STATUS_COLORS = {
  Saved: '#A7B0BE',
  'To Review': '#B88CFF',
  Applied: '#F4C35A',
  Interviewing: '#55B8FF',
  Offer: '#FF9E57',
  Accepted: '#39D98A',
  Rejected: '#FF6B6B',
  Withdrawn: '#8D96A5',
  Archived: '#6F7784'
};

const SOURCES = [
  // Tunisia
  'Keejob',
  'Tanitjobs',
  'Emploi.nat.tn',
  'Tunisie Travail',
  'EmploiTunisie',
  'Optioncarriere Tunisie',
  'Careerjet Tunisie',

  // France
  'APEC',
  'France Travail',
  'Welcome to the Jungle',
  'JobTeaser',
  'HelloWork',
  'Cadremploi',
  'Meteojob',
  'LesJeudis',
  "L'Etudiant",
  'iQuesta',
  'Wizbii',
  'StudentJob',

  // International / general
  'LinkedIn',
  'Indeed',
  'Glassdoor',
  'Monster',
  'Talent.com',
  'Jooble',
  'Careerjet',
  'EURES',
  'EURAXESS',
  'Wellfound',
  'Remote OK',
  'We Work Remotely',

  // ATS / careers platforms
  'Workday',
  'SmartRecruiters',
  'Greenhouse',
  'Lever',
  'Ashby',
  'SAP SuccessFactors',
  'Oracle Careers',
  'Company careers page',

  // MENA / wider region
  'Bayt',
  'GulfTalent',
  'NaukriGulf',

  // Other channels
  'Recruiter / Agency',
  'Referral',
  'School / Alumni',
  'Other'
];

const FEATURED_SOURCES = [
  'LinkedIn',
  'Keejob',
  'Tanitjobs',
  'Indeed',
  'Welcome to the Jungle',
  'JobTeaser',
  'Glassdoor',
  'Bayt'
];

const CURRENCIES = [
  { code: 'EUR', name: 'Euro', flag: '🇪🇺', countries: 'Eurozone France Germany Italy Spain Belgium Netherlands Portugal Austria Ireland Finland Greece Luxembourg' },
  { code: 'USD', name: 'US Dollar', flag: '🇺🇸', countries: 'United States USA America' },
  { code: 'TND', name: 'Tunisian Dinar', flag: '🇹🇳', countries: 'Tunisia Tunisian' },
  { code: 'MAD', name: 'Moroccan Dirham', flag: '🇲🇦', countries: 'Morocco Moroccan' },
  { code: 'DZD', name: 'Algerian Dinar', flag: '🇩🇿', countries: 'Algeria Algerian' },
  { code: 'LYD', name: 'Libyan Dinar', flag: '🇱🇾', countries: 'Libya Libyan' },
  { code: 'EGP', name: 'Egyptian Pound', flag: '🇪🇬', countries: 'Egypt Egyptian' },
  { code: 'SAR', name: 'Saudi Riyal', flag: '🇸🇦', countries: 'Saudi Arabia Saudi' },
  { code: 'AED', name: 'UAE Dirham', flag: '🇦🇪', countries: 'United Arab Emirates UAE Dubai Abu Dhabi Emirati' },
  { code: 'QAR', name: 'Qatari Riyal', flag: '🇶🇦', countries: 'Qatar Qatari' },
  { code: 'KWD', name: 'Kuwaiti Dinar', flag: '🇰🇼', countries: 'Kuwait Kuwaiti' },
  { code: 'BHD', name: 'Bahraini Dinar', flag: '🇧🇭', countries: 'Bahrain Bahraini' },
  { code: 'OMR', name: 'Omani Rial', flag: '🇴🇲', countries: 'Oman Omani' },
  { code: 'JOD', name: 'Jordanian Dinar', flag: '🇯🇴', countries: 'Jordan Jordanian' },
  { code: 'LBP', name: 'Lebanese Pound', flag: '🇱🇧', countries: 'Lebanon Lebanese' },
  { code: 'IQD', name: 'Iraqi Dinar', flag: '🇮🇶', countries: 'Iraq Iraqi' },
  { code: 'TRY', name: 'Turkish Lira', flag: '🇹🇷', countries: 'Turkey Türkiye Turkish' },
  { code: 'GBP', name: 'Pound Sterling', flag: '🇬🇧', countries: 'United Kingdom UK Britain British England' },
  { code: 'CAD', name: 'Canadian Dollar', flag: '🇨🇦', countries: 'Canada Canadian' },
  { code: 'CHF', name: 'Swiss Franc', flag: '🇨🇭', countries: 'Switzerland Swiss' }
];

const PAGE_META = {
  dashboard: ['JOB SEARCH COMMAND CENTER', 'Dashboard'],
  applications: ['TRACKING', 'Applications'],
  pipeline: ['STATUS FLOW', 'Pipeline'],
  analyzer: ['LOCAL CV MATCH', 'Analyzer'],
  exports: ['FILES & HISTORY', 'Exports'],
  settings: ['PREFERENCES & DATA', 'Settings'],
  guide: ['HELP & LEARNING', 'Guide']
};

const FILTER_COLUMNS = [
  'company',
  'job_title',
  'status',
  'match_score',
  'rating',
  'location',
  'date_saved',
  'source'
];

const state = {
  applications: [],
  stats: {},
  settings: {},
  recentProjects: [],
  exportHistory: [],
  backupDir: '',
  selectedIds: new Set(),
  onboardingShown: false,
  tableFilters: Object.fromEntries(
    FILTER_COLUMNS.map(column => [column, null])
  ),
  tableSort: {
    column: null,
    direction: null
  }
};

let initialized = false;

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function formatDate(value) {
  if (!value) return '—';

  const d = new Date(value);
  if (Number.isNaN(d.getTime())) {
    return String(value).slice(0, 10);
  }

  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit'
  });
}

function fileName(path) {
  return path ? String(path).split(/[\\/]/).pop() : '';
}

function normalizeText(value) {
  return String(value ?? '').trim().toLocaleLowerCase();
}

function displayValue(value) {
  const text = String(value ?? '').trim();
  return text || '(Blank)';
}

function statusColor(status) {
  return STATUS_COLORS[status] || '#BC965D';
}

function statusPill(status) {
  const color = statusColor(status);

  return `
    <span
      class="status-pill"
      style="--status-color:${color};--status-border:${color}55;--status-bg:${color}16"
    >
      ${escapeHtml(status || 'Saved')}
    </span>
  `;
}

function ratingStars(value) {
  const rating = Math.max(
    0,
    Math.min(
      5,
      Number(value || 0)
    )
  );

  return rating
    ? '★'.repeat(rating)
    : '—';
}

function parseDate(value) {
  const date = new Date(value || '');

  return Number.isNaN(date.getTime())
    ? null
    : date;
}

function monthKey(value) {
  const date = parseDate(value);

  if (!date) {
    return '(Unknown month)';
  }

  return `${date.getFullYear()}-${String(
    date.getMonth() + 1
  ).padStart(2, '0')}`;
}

function monthLabel(key) {
  if (key === '(Unknown month)') {
    return key;
  }

  const [year, month] = key
    .split('-')
    .map(Number);

  const date = new Date(
    year,
    month - 1,
    1
  );

  return date.toLocaleDateString(
    undefined,
    {
      month: 'long',
      year: 'numeric'
    }
  );
}

function scoreBucket(score) {
  if (
    score === null ||
    score === undefined ||
    score === ''
  ) {
    return 'none';
  }

  const value = Number(score);

  if (Number.isNaN(value)) {
    return 'none';
  }

  if (value >= 80) {
    return '80-100';
  }

  if (value >= 60) {
    return '60-79';
  }

  if (value >= 40) {
    return '40-59';
  }

  return '0-39';
}

function sourceMatches(query) {
  const value = normalizeText(query);

  if (!value) {
    return FEATURED_SOURCES.slice();
  }

  return SOURCES
    .filter(
      source =>
        normalizeText(source)
          .startsWith(value)
    )
    .slice(0, 10);
}

async function api(method, ...args) {
  const fn =
    window.pywebview?.api?.[method];

  if (!fn) {
    throw new Error(
      'JAM backend is not ready yet.'
    );
  }

  const result =
    await fn(...args);

  if (!result?.ok) {
    throw new Error(
      result?.error ||
      'Unknown JAM error.'
    );
  }

  return result;
}

function toast(
  message,
  type = 'success'
) {
  const root =
    $('#toastRoot');

  if (!root) {
    return;
  }

  const node =
    document.createElement('div');

  node.className =
    `toast ${
      type === 'error'
        ? 'error'
        : ''
    }`;

  node.textContent =
    message;

  root.appendChild(node);

  setTimeout(
    () => node.remove(),
    3300
  );
}

function openModal({
  kicker = 'JAM',
  title = '',
  body = '',
  actions = '',
  wide = false
}) {
  const root =
    $('#modalRoot');

  root.classList.add('active');

  root.innerHTML = `
    <div
      class="modal-backdrop"
      data-modal-backdrop
    >
      <section
        class="modal ${
          wide
            ? 'modal-wide'
            : ''
        }"
        role="dialog"
        aria-modal="true"
      >
        <div class="modal-head">
          <div>
            <div class="eyebrow">
              ${escapeHtml(kicker)}
            </div>

            <h2>
              ${escapeHtml(title)}
            </h2>
          </div>

          <button
            class="icon-btn"
            data-close-modal
          >
            ×
          </button>
        </div>

        <div class="modal-body">
          ${body}
        </div>

        ${
          actions
            ? `
              <div class="modal-actions">
                ${actions}
              </div>
            `
            : ''
        }
      </section>
    </div>
  `;

  $('[data-close-modal]', root)
    ?.addEventListener(
      'click',
      closeModal
    );

  $('[data-modal-backdrop]', root)
    ?.addEventListener(
      'click',
      event => {
        if (
          event.target.hasAttribute(
            'data-modal-backdrop'
          )
        ) {
          closeModal();
        }
      }
    );

  return root;
}

function closeModal() {
  const root =
    $('#modalRoot');

  root.classList.remove('active');
  root.innerHTML = '';
}

function confirmDialog(
  title,
  message,
  confirmLabel = 'Yes, continue'
) {
  return new Promise(
    resolve => {
      const root =
        openModal({
          kicker:
            'CONFIRMATION',

          title,

          body: `
            <p class="muted">
              ${escapeHtml(message)}
            </p>
          `,

          actions: `
            <button
              class="btn secondary"
              data-no
            >
              Cancel
            </button>

            <button
              class="btn danger"
              data-yes
            >
              ${escapeHtml(confirmLabel)}
            </button>
          `
        });

      $('[data-no]', root)
        .onclick =
        () => {
          closeModal();
          resolve(false);
        };

      $('[data-yes]', root)
        .onclick =
        () => {
          closeModal();
          resolve(true);
        };
    }
  );
}

function navigate(page) {
  $$('.page').forEach(
    node =>
      node.classList.remove(
        'active'
      )
  );

  $(`#${page}Page`)
    ?.classList
    .add('active');

  $$('.nav-item').forEach(
    node => {
      node.classList.toggle(
        'active',
        node.dataset.page === page
      );
    }
  );

  const meta =
    PAGE_META[page] ||
    PAGE_META.dashboard;

  $('#pageEyebrow').textContent =
    meta[0];

  $('#pageTitle').textContent =
    meta[1];

  if (page === 'applications') {
    renderTable();
  }

  if (page === 'pipeline') {
    renderPipeline();
  }

  if (page === 'exports') {
    renderExportHistory();
  }
}

function renderStats() {
  const stats =
    state.stats || {};

  $('#statTotal').textContent =
    stats.total ?? 0;

  $('#statApplied').textContent =
    stats.applied ?? 0;

  $('#statInterviewing').textContent =
    stats.interviewing ?? 0;

  $('#statAccepted').textContent =
    stats.accepted ?? 0;

  $('#statRejected').textContent =
    stats.rejected ?? 0;

  $('#statAverageDay').textContent =
    stats.average_per_day ?? 0;

  $('#statAverageScore').textContent =
    `${
      stats.average_match_score ?? 0
    }%`;
}

function renderRecentApplications() {
  const root =
    $('#recentApplications');

  const apps =
    state.applications.slice(
      0,
      6
    );

  if (!apps.length) {
    root.innerHTML = `
      <div class="panel">
        <p class="muted">
          Nothing tracked yet.
          Add a job or open Capture Mode.
        </p>
      </div>
    `;

    return;
  }

  root.innerHTML =
    apps
      .map(
        app => `
          <div class="recent-item">

            <strong>
              ${escapeHtml(
                app.company ||
                'Unknown company'
              )}
            </strong>

            <span>
              ${escapeHtml(
                app.job_title ||
                'Untitled role'
              )}
            </span>

            ${statusPill(app.status)}

            <span>
              ${formatDate(
                app.date_saved
              )}
            </span>

          </div>
        `
      )
      .join('');
}

function rowMatchesSetFilter(
  app,
  column,
  selected
) {
  if (selected === null) {
    return true;
  }

  let value;

  if (column === 'rating') {
    value =
      String(
        Number(
          app.rating || 0
        )
      );
  } else if (
    column === 'date_saved'
  ) {
    value =
      monthKey(
        app.date_saved
      );
  } else if (
    column === 'match_score'
  ) {
    value =
      scoreBucket(
        app.match_score
      );
  } else {
    value =
      displayValue(
        app[column]
      );
  }

  return selected.has(value);
}

function getFilteredApplications() {
  const search =
    normalizeText(
      $('#searchInput')?.value || ''
    );

  let rows =
    state.applications.filter(
      app => {
        if (search) {
          const haystack = [
            app.company,
            app.job_title,
            app.location,
            app.source,
            app.notes,
            app.contact_name,
            app.status
          ]
            .join(' ')
            .toLocaleLowerCase();

          if (
            !haystack.includes(search)
          ) {
            return false;
          }
        }

        for (
          const column
          of FILTER_COLUMNS
        ) {
          if (
            !rowMatchesSetFilter(
              app,
              column,
              state.tableFilters[column]
            )
          ) {
            return false;
          }
        }

        return true;
      }
    );

  const {
    column,
    direction
  } = state.tableSort;

  if (
    !column ||
    !direction
  ) {
    return rows;
  }

  const multiplier =
    direction === 'asc'
      ? 1
      : -1;

  rows =
    rows
      .slice()
      .sort(
        (a, b) => {
          if (
            column === 'match_score'
          ) {
            const av =
              a.match_score === null ||
              a.match_score === undefined
                ? -1
                : Number(a.match_score);

            const bv =
              b.match_score === null ||
              b.match_score === undefined
                ? -1
                : Number(b.match_score);

            return (
              (av - bv) *
              multiplier
            );
          }

          if (
            column === 'rating'
          ) {
            return (
              (
                Number(
                  a.rating || 0
                ) -
                Number(
                  b.rating || 0
                )
              ) *
              multiplier
            );
          }

          if (
            column === 'date_saved'
          ) {
            const av =
              parseDate(
                a.date_saved
              )?.getTime() ?? 0;

            const bv =
              parseDate(
                b.date_saved
              )?.getTime() ?? 0;

            return (
              (av - bv) *
              multiplier
            );
          }

          const av =
            normalizeText(
              a[column]
            );

          const bv =
            normalizeText(
              b[column]
            );

          return (
            av.localeCompare(
              bv,
              undefined,
              {
                sensitivity:
                  'base'
              }
            ) *
            multiplier
          );
        }
      );

  return rows;
}

function renderTable() {
  const body =
    $('#jobsTableBody');

  const rows =
    getFilteredApplications();

  const emptyState =
    $('#tableEmpty');

  emptyState.classList.toggle(
    'visible',
    rows.length === 0
  );

  const emptyTitle =
    $('h3', emptyState);

  const emptyText =
    $('p', emptyState);

  if (
    emptyTitle &&
    emptyText
  ) {
    if (
      state.applications.length === 0
    ) {
      emptyTitle.textContent =
        'No jobs yet';

      emptyText.textContent =
        'Add your first opportunity or use Capture Mode while browsing jobs.';
    } else {
      emptyTitle.textContent =
        'No jobs match the current filters';

      emptyText.textContent =
        'Change or clear the column filters to show more applications.';
    }
  }

  body.innerHTML =
    rows
      .map(
        app => `
          <tr data-id="${app.id}">

            <td class="check-col">
              <input
                class="row-check"
                type="checkbox"
                data-id="${app.id}"
                ${
                  state.selectedIds.has(
                    app.id
                  )
                    ? 'checked'
                    : ''
                }
              >
            </td>

            <td>
              <span class="row-title">
                ${escapeHtml(
                  app.company || '—'
                )}
              </span>

              <span class="row-sub">
                ${escapeHtml(
                  app.work_mode || ''
                )}
              </span>
            </td>

            <td>
              <button
                class="text-btn row-edit"
                data-id="${app.id}"
              >
                ${escapeHtml(
                  app.job_title ||
                  'Untitled role'
                )}
              </button>
            </td>

            <td>
              ${statusPill(app.status)}
            </td>

            <td class="score-cell">
              ${
                app.match_score == null
                  ? '—'
                  : `${app.match_score}%`
              }
            </td>

            <td class="rating-cell">
              ${ratingStars(
                app.rating
              )}
            </td>

            <td>
              ${escapeHtml(
                app.location || '—'
              )}
            </td>

            <td>
              ${formatDate(
                app.date_saved
              )}
            </td>

            <td>
              ${escapeHtml(
                app.source || '—'
              )}
            </td>

            <td class="delete-col">
              <button
                class="row-delete"
                data-delete-id="${app.id}"
                title="Delete"
              >
                ×
              </button>
            </td>

          </tr>
        `
      )
      .join('');

  updateSelectionUi();
  renderTableHeaderState();
}

function updateSelectionUi() {
  const count =
    state.selectedIds.size;

  $('#selectionLabel').textContent =
    `${count} selected`;

  $('#bulkDeleteBtn').disabled =
    count === 0;

  const editSelectedBtn =
    $('#editSelectedBtn');

  if (editSelectedBtn) {
    editSelectedBtn.hidden =
      count !== 1;

    editSelectedBtn.disabled =
      count !== 1;
  }

  const visibleIds =
    getFilteredApplications()
      .map(
        app => app.id
      );

  $('#selectAllRows').checked =
    visibleIds.length > 0 &&
    visibleIds.every(
      id =>
        state.selectedIds.has(id)
    );
}

function cycleSort(column) {
  const current =
    state.tableSort;

  let firstDirection =
    'asc';

  if (
    [
      'match_score',
      'rating',
      'date_saved'
    ].includes(column)
  ) {
    firstDirection =
      'desc';
  }

  if (
    current.column !== column ||
    !current.direction
  ) {
    state.tableSort = {
      column,
      direction:
        firstDirection
    };
  } else if (
    current.direction ===
    firstDirection
  ) {
    state.tableSort = {
      column,
      direction:
        firstDirection === 'asc'
          ? 'desc'
          : 'asc'
    };
  } else {
    state.tableSort = {
      column: null,
      direction: null
    };
  }

  renderTable();
}

function renderTableHeaderState() {
  $$('.jobs-table thead [data-sort]')
    .forEach(
      button => {
        const indicator =
          $(
            '.sort-indicator',
            button
          );

        if (!indicator) {
          return;
        }

        if (
          state.tableSort.column !==
          button.dataset.sort
        ) {
          indicator.textContent = '';

          button.classList.remove(
            'active'
          );

          return;
        }

        indicator.textContent =
          state.tableSort.direction ===
          'asc'
            ? '↑'
            : '↓';

        button.classList.add(
          'active'
        );
      }
    );

  $$('.jobs-table thead [data-filter]')
    .forEach(
      button => {
        button.classList.toggle(
          'active',
          state.tableFilters[
            button.dataset.filter
          ] !== null
        );
      }
    );

  const clear =
    $('#clearTableFiltersBtn');

  if (clear) {
    const active =
      Boolean(
        state.tableSort.column ||
        FILTER_COLUMNS.some(
          column =>
            state.tableFilters[
              column
            ] !== null
        ) ||
        normalizeText(
          $('#searchInput')?.value || ''
        )
      );

    clear.disabled =
      !active;
  }
}

function allFilterValues(column) {
  let values;

  if (column === 'status') {
    const extra =
      state.applications
        .map(
          app => app.status
        )
        .filter(Boolean);

    values = [
      ...STATUSES,
      ...extra
    ];
  } else if (
    column === 'rating'
  ) {
    return [
      '5',
      '4',
      '3',
      '2',
      '1',
      '0'
    ];
  } else if (
    column === 'match_score'
  ) {
    return [
      '80-100',
      '60-79',
      '40-59',
      '0-39',
      'none'
    ];
  } else if (
    column === 'date_saved'
  ) {
    values =
      state.applications.map(
        app =>
          monthKey(
            app.date_saved
          )
      );

    return [
      ...new Set(values)
    ].sort(
      (a, b) =>
        b.localeCompare(a)
    );
  } else {
    values =
      state.applications.map(
        app =>
          displayValue(
            app[column]
          )
      );
  }

  return [
    ...new Set(values)
  ].sort(
    (a, b) =>
      a.localeCompare(
        b,
        undefined,
        {
          sensitivity:
            'base'
        }
      )
  );
}

function filterValueLabel(
  column,
  value
) {
  if (column === 'rating') {
    return value === '0'
      ? 'No rating'
      : '★'.repeat(
          Number(value)
        );
  }

  if (
    column === 'date_saved'
  ) {
    return monthLabel(value);
  }

  if (
    column === 'match_score'
  ) {
    const labels = {
      '80-100':
        '80–100%',
      '60-79':
        '60–79%',
      '40-59':
        '40–59%',
      '0-39':
        '0–39%',
      none:
        'No score'
    };

    return (
      labels[value] ||
      value
    );
  }

  return value;
}

function filterColumnTitle(column) {
  const labels = {
    company: 'Company',
    job_title: 'Job title',
    status: 'Status',
    match_score: 'Score',
    rating: 'Rating',
    location: 'Location',
    date_saved: 'Date saved',
    source: 'Source'
  };

  return (
    labels[column] ||
    column
  );
}

function filterSupportsSearch(column) {
  return [
    'company',
    'job_title',
    'location',
    'source'
  ].includes(column);
}

function filterSupportsSort(column) {
  return [
    'company',
    'job_title',
    'match_score',
    'rating',
    'date_saved'
  ].includes(column);
}

function sortButtonLabels(column) {
  if (
    column === 'match_score' ||
    column === 'rating'
  ) {
    return [
      [
        'desc',
        'Highest first'
      ],
      [
        'asc',
        'Lowest first'
      ]
    ];
  }

  if (
    column === 'date_saved'
  ) {
    return [
      [
        'desc',
        'Newest first'
      ],
      [
        'asc',
        'Oldest first'
      ]
    ];
  }

  return [
    [
      'asc',
      'A → Z'
    ],
    [
      'desc',
      'Z → A'
    ]
  ];
}

function closeTableFilter() {
  const root =
    $('#tableFilterRoot');

  if (root) {
    root.innerHTML = '';
  }
}

function openColumnFilter(
  column,
  anchor
) {
  closeTableFilter();

  const root =
    $('#tableFilterRoot');

  const values =
    allFilterValues(column);

  const selected =
    state.tableFilters[column];

  const allSelected =
    selected === null;

  const sortMarkup =
    filterSupportsSort(column)
      ? `
        <div class="filter-sort-row">

          ${sortButtonLabels(column)
            .map(
              (
                [
                  direction,
                  label
                ]
              ) => `
                <button
                  class="filter-sort-btn ${
                    state.tableSort.column ===
                      column &&
                    state.tableSort.direction ===
                      direction
                      ? 'active'
                      : ''
                  }"
                  data-filter-sort="${direction}"
                >
                  ${escapeHtml(label)}
                </button>
              `
            )
            .join('')}

        </div>
      `
      : '';

  const searchMarkup =
    filterSupportsSearch(column)
      ? `
        <div class="filter-search-wrap">

          <input
            class="filter-search"
            type="search"
            placeholder="Search values..."
            data-filter-search
          >

        </div>
      `
      : '';

  root.innerHTML = `
    <div
      class="table-filter-popover"
      data-filter-popover
    >

      <div class="filter-pop-head">

        <strong>
          Filter ${
            escapeHtml(
              filterColumnTitle(
                column
              )
            )
          }
        </strong>

        <button
          class="filter-link"
          data-filter-clear
        >
          Clear
        </button>

      </div>

      ${sortMarkup}

      ${searchMarkup}

      <div class="filter-option-actions">

        <button
          class="filter-link"
          data-filter-all
        >
          Select all
        </button>

        <button
          class="filter-link"
          data-filter-none
        >
          None
        </button>

      </div>

      <div
        class="filter-options"
        data-filter-options
      >

        ${
          values.length
            ? values
                .map(
                  value => {
                    const checked =
                      allSelected ||
                      selected.has(
                        value
                      );

                    const color =
                      column === 'status'
                        ? statusColor(
                            value
                          )
                        : null;

                    return `
                      <label
                        class="filter-option"
                        data-filter-option
                        data-search-value="${
                          escapeHtml(
                            normalizeText(
                              filterValueLabel(
                                column,
                                value
                              )
                            )
                          )
                        }"
                      >

                        <input
                          type="checkbox"
                          data-filter-value="${
                            escapeHtml(
                              value
                            )
                          }"
                          ${
                            checked
                              ? 'checked'
                              : ''
                          }
                        >

                        ${
                          color
                            ? `
                              <span
                                class="filter-status-dot"
                                style="background:${color}"
                              ></span>
                            `
                            : ''
                        }

                        <span>
                          ${
                            escapeHtml(
                              filterValueLabel(
                                column,
                                value
                              )
                            )
                          }
                        </span>

                      </label>
                    `;
                  }
                )
                .join('')
            : `
              <div class="filter-no-values">
                No values yet.
              </div>
            `
        }

      </div>

    </div>
  `;

  const popover =
    $(
      '[data-filter-popover]',
      root
    );

  const rect =
    anchor.getBoundingClientRect();

  const width =
    270;

  let left =
    rect.right - width;

  let top =
    rect.bottom + 6;

  if (left < 12) {
    left = 12;
  }

  if (
    left + width >
    window.innerWidth - 12
  ) {
    left =
      window.innerWidth -
      width -
      12;
  }

  popover.style.left =
    `${left}px`;

  popover.style.top =
    `${top}px`;

  requestAnimationFrame(
    () => {
      const popRect =
        popover.getBoundingClientRect();

      if (
        popRect.bottom >
        window.innerHeight - 12
      ) {
        top =
          Math.max(
            12,
            rect.top -
            popRect.height -
            6
          );

        popover.style.top =
          `${top}px`;
      }
    }
  );

  $('[data-filter-search]', root)
    ?.addEventListener(
      'input',
      event => {
        const query =
          normalizeText(
            event.target.value
          );

        $$(
          '[data-filter-option]',
          root
        ).forEach(
          option => {
            option.style.display =
              option
                .dataset
                .searchValue
                .includes(query)
                ? ''
                : 'none';
          }
        );
      }
    );

  $('[data-filter-clear]', root)
    .onclick =
    () => {
      state.tableFilters[
        column
      ] = null;

      if (
        state.tableSort.column ===
        column
      ) {
        state.tableSort = {
          column: null,
          direction: null
        };
      }

      closeTableFilter();
      renderTable();
    };

  $('[data-filter-all]', root)
    .onclick =
    () => {
      state.tableFilters[
        column
      ] = null;

      $$(
        '[data-filter-value]',
        root
      ).forEach(
        input => {
          input.checked = true;
        }
      );

      renderTable();
    };

  $('[data-filter-none]', root)
    .onclick =
    () => {
      state.tableFilters[
        column
      ] =
        new Set();

      $$(
        '[data-filter-value]',
        root
      ).forEach(
        input => {
          input.checked = false;
        }
      );

      renderTable();
    };

  $$(
    '[data-filter-sort]',
    root
  ).forEach(
    button => {
      button.onclick =
      () => {
        const direction =
          button.dataset.filterSort;

        if (
          state.tableSort.column ===
            column &&
          state.tableSort.direction ===
            direction
        ) {
          state.tableSort = {
            column: null,
            direction: null
          };
        } else {
          state.tableSort = {
            column,
            direction
          };
        }

        renderTable();

        openColumnFilter(
          column,
          anchor
        );
      };
    }
  );

  $$(
    '[data-filter-value]',
    root
  ).forEach(
    input => {
      input.addEventListener(
        'change',
        () => {
          let current =
            state.tableFilters[
              column
            ];

          if (current === null) {
            current =
              new Set(values);
          } else {
            current =
              new Set(current);
          }

          const value =
            input.dataset.filterValue;

          if (input.checked) {
            current.add(value);
          } else {
            current.delete(value);
          }

          state.tableFilters[
            column
          ] =
            current.size ===
              values.length
              ? null
              : current;

          renderTable();
        }
      );
    }
  );
}

function clearTableFilters() {
  FILTER_COLUMNS.forEach(
    column => {
      state.tableFilters[
        column
      ] = null;
    }
  );

  state.tableSort = {
    column: null,
    direction: null
  };

  if ($('#searchInput')) {
    $('#searchInput').value = '';
  }

  closeTableFilter();
  renderTable();
}

function renderPipeline() {
  const root = $('#pipelineBoard');

  const stages = STATUSES.filter(
    status => status !== 'Archived'
  );

  root.innerHTML = stages
    .map(status => {
      const apps = state.applications.filter(
        app => app.status === status
      );
      const color = statusColor(status);

      return `
        <section class="pipeline-column">
          <div class="pipeline-head">
            <strong style="color:${color}">
              ${escapeHtml(status)}
            </strong>
            <span>${apps.length}</span>
          </div>

          <div class="pipeline-items">
            ${
              apps.length
                ? apps.map(app => `
                    <article class="pipeline-card" data-pipeline-card="${app.id}">
                      <button
                        type="button"
                        class="pipeline-card-delete"
                        data-pipeline-delete="${app.id}"
                        title="Delete application"
                      >×</button>

                      <strong>
                        ${escapeHtml(app.job_title || 'Untitled')}
                      </strong>

                      <small>
                        ${escapeHtml(app.company || 'Unknown company')}
                      </small>

                      <small>
                        ${
                          app.match_score == null
                            ? 'Not analyzed'
                            : `${app.match_score}% match`
                        }
                      </small>
                    </article>
                  `).join('')
                : `<small class="muted">No applications</small>`
            }
          </div>
        </section>
      `;
    })
    .join('');
}

function setupPipelineDrag() {
  const board = $('#pipelineBoard');
  if (!board || board.dataset.dragReady === '1') return;
  board.dataset.dragReady = '1';

  let dragging = false;
  let moved = false;
  let startX = 0;
  let startY = 0;
  let startScrollLeft = 0;
  let startScrollTop = 0;

  board.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    if (event.target.closest('button, input, a, select, textarea')) return;

    dragging = true;
    moved = false;
    startX = event.clientX;
    startY = event.clientY;
    startScrollLeft = board.scrollLeft;
    startScrollTop = board.scrollTop;
    board.classList.add('dragging');
    board.setPointerCapture?.(event.pointerId);
  });

  board.addEventListener('pointermove', event => {
    if (!dragging) return;
    const dx = event.clientX - startX;
    const dy = event.clientY - startY;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) moved = true;
    board.scrollLeft = startScrollLeft - dx;
    board.scrollTop = startScrollTop - dy;
    if (moved) event.preventDefault();
  });

  const stopDrag = event => {
    if (!dragging) return;
    dragging = false;
    board.classList.remove('dragging');
    try { board.releasePointerCapture?.(event.pointerId); } catch (_) {}
    setTimeout(() => { moved = false; }, 0);
  };

  board.addEventListener('pointerup', stopDrag);
  board.addEventListener('pointercancel', stopDrag);

  board.addEventListener('click', event => {
    const button = event.target.closest('[data-pipeline-delete]');
    if (!button) return;
    event.stopPropagation();
    deleteOne(Number(button.dataset.pipelineDelete));
  });
}

function renderExportHistory() {
  const root =
    $('#exportHistory');

  if (
    !state.exportHistory.length
  ) {
    root.innerHTML = `
      <div class="panel">
        <p class="muted">
          No exports yet.
        </p>
      </div>
    `;

    return;
  }

  root.innerHTML =
    state.exportHistory
      .map(
        item => `
          <div class="history-item">

            <strong>
              ${escapeHtml(
                item.export_type
              )}
            </strong>

            <span
              title="${escapeHtml(
                item.path
              )}"
            >
              ${escapeHtml(
                fileName(
                  item.path
                )
              )}
            </span>

            <span>
              ${item.row_count}
              row(s)
            </span>

            <button
              class="btn secondary"
              data-open-path="${
                escapeHtml(
                  item.path
                )
              }"
            >
              Open
            </button>

          </div>
        `
      )
      .join('');
}

function currencyByCode(code) {
  return CURRENCIES.find(
    currency => currency.code === code
  ) || CURRENCIES[0];
}

function currencyDisplay(currency) {
  return `${currency.flag} ${currency.code} — ${currency.name}`;
}

function currencyMatches(query) {
  const needle = normalizeText(query);
  if (!needle) return CURRENCIES;

  return CURRENCIES.filter(currency =>
    normalizeText(
      `${currency.code} ${currency.name} ${currency.countries}`
    ).includes(needle)
  );
}

function renderCurrencySuggestions(query = '') {
  const root = $('#salaryCurrencySuggestions');
  if (!root) return;

  const matches = currencyMatches(query);
  root.innerHTML = matches.map(currency => `
    <button
      type="button"
      class="currency-option"
      data-currency-code="${currency.code}"
    >
      <span class="flag">${currency.flag}</span>
      <span class="code">${currency.code}</span>
      <span>
        ${escapeHtml(currency.name)}
        <small>${escapeHtml(currency.countries.split(' ').slice(0, 4).join(' '))}</small>
      </span>
    </button>
  `).join('');

  root.hidden = matches.length === 0;

  $$('[data-currency-code]', root).forEach(button => {
    button.onclick = () => {
      selectSalaryCurrency(button.dataset.currencyCode);
      root.hidden = true;
    };
  });
}

function selectSalaryCurrency(code) {
  const currency = currencyByCode(code || 'EUR');
  $('#salaryCurrency').value = currency.code;
  $('#salaryCurrencySearch').value = currencyDisplay(currency);
}

function setupCurrencyPicker() {
  const input = $('#salaryCurrencySearch');
  const menu = $('#salaryCurrencySuggestions');
  if (!input || !menu) return;

  input.addEventListener('focus', () => {
    input.select();
    renderCurrencySuggestions('');
  });

  input.addEventListener('input', () => {
    renderCurrencySuggestions(input.value);
  });

  input.addEventListener('keydown', event => {
    if (event.key === 'Escape') menu.hidden = true;
  });

  document.addEventListener('click', event => {
    if (!$('#salaryCurrencyPicker')?.contains(event.target)) {
      menu.hidden = true;
    }
  });
}

function renderSettings() {
  const cv = state.settings.cv_path || '';

  $('#selectedCvPath').textContent =
    cv || 'No CV selected yet.';

  $('#settingsCvPath').textContent =
    cv || 'No CV selected.';

  $('#salaryMin').value =
    state.settings.salary_target_min || '';

  $('#salaryMax').value =
    state.settings.salary_target_max || '';

  selectSalaryCurrency(
    state.settings.salary_currency || 'EUR'
  );

  const backupPath = $('#backupPathText');
  if (backupPath) {
    backupPath.textContent =
      state.backupDir || 'Windows local app data';
  }
}

function renderAll() {
  renderStats();
  renderRecentApplications();
  renderTable();
  renderPipeline();
  renderExportHistory();
  renderSettings();
}

async function reloadData() {
  const result =
    await api(
      'bootstrap'
    );

  state.applications =
    result.applications || [];

  state.stats =
    result.stats || {};

  state.settings =
    result.settings || {};

  state.recentProjects =
    result.recent_projects || [];

  state.exportHistory =
    result.export_history || [];

  state.backupDir =
    result.backup_dir || '';

  state.selectedIds =
    new Set(
      [...state.selectedIds]
        .filter(
          id =>
            state.applications.some(
              app =>
                app.id === id
            )
        )
    );

  renderAll();
}

window.jamRefreshFromCapture =
  async function () {
    try {
      await reloadData();
    } catch (error) {
      console.error(error);
    }
  };

function jobFormBody(app = {}) {
  const status =
    app.status || 'Saved';

  const rating =
    Number(
      app.rating || 0
    );

  return `
    <div
      class="job-editor-grid"
      id="jobForm"
      data-id="${app.id || ''}"
    >

      <label>
        Company

        <input
          class="control full draft-main"
          name="company"
          value="${
            escapeHtml(
              app.company || ''
            )
          }"
          autocomplete="off"
        >
      </label>

      <label>
        Job title

        <input
          class="control full draft-main"
          name="job_title"
          value="${
            escapeHtml(
              app.job_title || ''
            )
          }"
          autocomplete="off"
        >
      </label>

      <label>
        Location

        <input
          class="control full draft-main"
          name="location"
          value="${
            escapeHtml(
              app.location || ''
            )
          }"
          autocomplete="off"
        >
      </label>

      <label>
        Work mode

        <select
          class="control full"
          name="work_mode"
        >
          <option value=""></option>

          ${
            [
              'Onsite',
              'Hybrid',
              'Remote'
            ]
              .map(
                value => `
                  <option
                    value="${value}"
                    ${
                      app.work_mode ===
                      value
                        ? 'selected'
                        : ''
                    }
                  >
                    ${value}
                  </option>
                `
              )
              .join('')
          }
        </select>
      </label>

      <div
        class="job-editor-field job-editor-section"
        data-status-picker
      >

        <span>
          Status
        </span>

        <input
          type="hidden"
          name="status"
          value="${
            escapeHtml(status)
          }"
          data-status-value
        >

        <button
          type="button"
          class="inline-picker-trigger"
          data-status-trigger
        >

          <span
            class="inline-picker-current"
          >

            <span
              class="status-dot"
              style="background:${
                statusColor(status)
              }"
            ></span>

            <span data-status-text>
              ${escapeHtml(status)}
            </span>

          </span>

          <span>
            ▾
          </span>

        </button>

        <div
          class="inline-picker-menu"
          data-status-menu
          hidden
        >

          ${
            STATUSES
              .map(
                value => `
                  <button
                    type="button"
                    class="inline-picker-option"
                    data-status-option="${
                      escapeHtml(value)
                    }"
                  >

                    <span
                      class="status-dot"
                      style="background:${
                        statusColor(value)
                      }"
                    ></span>

                    <span>
                      ${escapeHtml(value)}
                    </span>

                  </button>
                `
              )
              .join('')
          }

        </div>
      </div>

      <div class="job-editor-field">

        <span>
          Rating
        </span>

        <div
          class="star-picker"
          data-rating-picker
          data-rating="${rating}"
        >

          <input
            type="hidden"
            name="rating"
            value="${rating}"
            data-rating-value
          >

          ${
            [1, 2, 3, 4, 5]
              .map(
                index => `
                  <button
                    type="button"
                    data-star="${index}"
                    title="${index} star${
                      index > 1
                        ? 's'
                        : ''
                    }"
                  >
                    ${
                      index <= rating
                        ? '★'
                        : '☆'
                    }
                  </button>
                `
              )
              .join('')
          }

          <button
            type="button"
            class="star-clear"
            data-star-clear
          >
            Clear
          </button>

        </div>
      </div>

      <div
        class="job-editor-field job-editor-section source-autocomplete"
      >

        <span>
          Source
        </span>

        <input
          class="control full draft-main"
          name="source"
          value="${
            escapeHtml(
              app.source || ''
            )
          }"
          placeholder="LinkedIn, Keejob, Welcome to the Jungle..."
          autocomplete="off"
          data-source-input
        >

        <div
          class="source-suggestions"
          data-source-suggestions
          hidden
        ></div>

      </div>

      <label>
        Salary text

        <input
          class="control full draft-main"
          name="salary_text"
          value="${
            escapeHtml(
              app.salary_text || ''
            )
          }"
          placeholder="45k–55k / 3000 TND / etc."
        >
      </label>

      <label class="job-editor-span-2">
        Job URL

        <input
          class="control full draft-main"
          name="url"
          value="${
            escapeHtml(
              app.url || ''
            )
          }"
          autocomplete="off"
        >
      </label>

      <label>
        Contact name

        <input
          class="control full draft-main"
          name="contact_name"
          value="${
            escapeHtml(
              app.contact_name || ''
            )
          }"
        >
      </label>

      <label>
        Contact link

        <input
          class="control full draft-main"
          name="contact_url"
          value="${
            escapeHtml(
              app.contact_url || ''
            )
          }"
        >
      </label>

      <label class="job-editor-span-2">
        Description

        <textarea
          class="control full draft-main"
          name="description"
        >${
          escapeHtml(
            app.description || ''
          )
        }</textarea>
      </label>

      <label class="job-editor-span-2">
        Notes

        <textarea
          class="control full draft-main"
          name="notes"
        >${
          escapeHtml(
            app.notes || ''
          )
        }</textarea>
      </label>

      <div
        class="job-editor-analysis-note ${
          app.match_score != null
            ? 'visible'
            : ''
        }"
        data-analysis-note
      >

        <span>
          CV Match analysis
        </span>

        <strong data-analysis-note-value>
          ${
            app.match_score == null
              ? 'Not analyzed'
              : `${app.match_score}%`
          }
        </strong>

      </div>

    </div>
  `;
}

function initializeJobEditorControls(
  root,
  markDraft
) {
  const form =
    $('#jobForm', root);

  // STATUS
  const statusPicker =
    $('[data-status-picker]', form);

  const statusTrigger =
    $(
      '[data-status-trigger]',
      statusPicker
    );

  const statusMenu =
    $(
      '[data-status-menu]',
      statusPicker
    );

  const statusInput =
    $(
      '[data-status-value]',
      statusPicker
    );

  const statusText =
    $(
      '[data-status-text]',
      statusPicker
    );

  const statusDot =
    $(
      '.status-dot',
      statusTrigger
    );

  statusTrigger.onclick =
    () => {
      const opening =
        statusMenu.hidden;

      statusMenu.hidden =
        !opening;

      statusTrigger.classList.toggle(
        'open',
        opening
      );
    };

  $$(
    '[data-status-option]',
    statusMenu
  ).forEach(
    button => {
      button.onclick =
      () => {
        const value =
          button.dataset.statusOption;

        statusInput.value =
          value;

        statusText.textContent =
          value;

        statusDot.style.background =
          statusColor(value);

        statusMenu.hidden =
          true;

        statusTrigger.classList.remove(
          'open'
        );

        markDraft();
      };
    }
  );

  // RATING
  const ratingPicker =
    $(
      '[data-rating-picker]',
      form
    );

  const ratingInput =
    $(
      '[data-rating-value]',
      ratingPicker
    );

  const stars =
    $$(
      '[data-star]',
      ratingPicker
    );

  const paintStars =
    value => {
      stars.forEach(
        button => {
          const index =
            Number(
              button.dataset.star
            );

          button.textContent =
            index <= value
              ? '★'
              : '☆';
        }
      );
    };

  stars.forEach(
    button => {
      const value =
        Number(
          button.dataset.star
        );

      button.onmouseenter =
        () =>
          paintStars(value);

      button.onmouseleave =
        () =>
          paintStars(
            Number(
              ratingInput.value ||
              0
            )
          );

      button.onclick =
        () => {
          ratingInput.value =
            String(value);

          ratingPicker.dataset.rating =
            String(value);

          paintStars(value);

          markDraft();
        };
    }
  );

  $('[data-star-clear]', ratingPicker)
    .onclick =
    () => {
      ratingInput.value =
        '0';

      ratingPicker.dataset.rating =
        '0';

      paintStars(0);

      markDraft();
    };

  // SOURCE AUTOCOMPLETE
  const sourceInput =
    $(
      '[data-source-input]',
      form
    );

  const sourceMenu =
    $(
      '[data-source-suggestions]',
      form
    );

  const hideSourceMenu =
    () => {
      sourceMenu.hidden =
        true;

      sourceMenu.innerHTML =
        '';
    };

  const showSourceMenu =
    () => {
      const matches =
        sourceMatches(
          sourceInput.value
        );

      if (!matches.length) {
        hideSourceMenu();
        return;
      }

      sourceMenu.innerHTML =
        matches
          .map(
            source => `
              <button
                type="button"
                class="source-suggestion"
                data-source-choice="${
                  escapeHtml(source)
                }"
              >
                ${escapeHtml(source)}
              </button>
            `
          )
          .join('');

      sourceMenu.hidden =
        false;

      $$(
        '[data-source-choice]',
        sourceMenu
      ).forEach(
        button => {
          button.onclick =
          () => {
            sourceInput.value =
              button.dataset.sourceChoice;

            hideSourceMenu();

            markDraft();

            sourceInput.focus();

            sourceInput.setSelectionRange(
              sourceInput.value.length,
              sourceInput.value.length
            );
          };
        }
      );
    };

  sourceInput.addEventListener(
    'focus',
    showSourceMenu
  );

  sourceInput.addEventListener(
    'input',
    () => {
      markDraft();
      showSourceMenu();
    }
  );

  sourceInput.addEventListener(
    'keydown',
    event => {
      if (
        event.key === 'Escape'
      ) {
        hideSourceMenu();
      }
    }
  );

  form.addEventListener(
    'click',
    event => {
      if (
        !statusPicker.contains(
          event.target
        )
      ) {
        statusMenu.hidden =
          true;

        statusTrigger.classList.remove(
          'open'
        );
      }

      if (
        !sourceInput.contains(
          event.target
        ) &&
        !sourceMenu.contains(
          event.target
        )
      ) {
        hideSourceMenu();
      }
    }
  );

  return {
    hideSourceMenu
  };
}

function readFormPayload(
  form,
  existing = null,
  draftStartedAt = null,
  analysis = null
) {
  const data =
    Object.fromEntries(
      new FormData(form)
        .entries()
    );

  data.rating =
    Number(
      data.rating || 0
    );

  if (existing?.id) {
    data.id =
      existing.id;
  }

  data.date_saved =
    existing?.date_saved ||
    draftStartedAt ||
    new Date().toISOString();

  if (analysis) {
    data.match_score =
      analysis.score_available
        ? analysis.score
        : null;

    data.analysis_json =
      JSON.stringify(
        analysis
      );
  }

  return data;
}

function updateJobEditorAnalysisNote(
  root,
  analysis
) {
  const note =
    $(
      '[data-analysis-note]',
      root
    );

  const value =
    $(
      '[data-analysis-note-value]',
      root
    );

  if (
    !note ||
    !value
  ) {
    return;
  }

  note.classList.add(
    'visible'
  );

  value.textContent =
    analysis.score_available
      ? `${analysis.score}%`
      : 'No reliable score';
}

function openJobModal(app = null) {
  const existing =
    app || {};

  let draftStartedAt =
    existing.date_saved ||
    null;

  let pendingAnalysis =
    null;

  const root =
    openModal({
      kicker:
        existing.id
          ? 'EDIT APPLICATION'
          : 'NEW OPPORTUNITY',

      title:
        existing.id
          ? `${
              existing.company || ''
            } • ${
              existing.job_title || ''
            }`
          : 'Add Job',

      body:
        jobFormBody(
          existing
        ),

      actions: `
        <button
          class="btn secondary"
          data-cancel-job
        >
          Cancel
        </button>

        <button
          class="btn secondary"
          data-analyze-form
        >
          Analyze
        </button>

        <button
          class="btn gold"
          data-save-job
        >
          ${
            existing.id
              ? 'Save changes'
              : 'Save application'
          }
        </button>
      `,

      wide: true
    });

  const form =
    $('#jobForm', root);

  const markDraft =
    () => {
      if (!draftStartedAt) {
        draftStartedAt =
          new Date()
            .toISOString();
      }
    };

  $$('.draft-main', form)
    .forEach(
      input => {
        input.addEventListener(
          'input',
          () => {
            if (
              String(
                input.value || ''
              ).trim()
            ) {
              markDraft();
            }
          }
        );

        input.addEventListener(
          'change',
          () => markDraft()
        );
      }
    );

  initializeJobEditorControls(
    root,
    markDraft
  );

  $('[data-cancel-job]', root)
    .onclick =
    closeModal;

  $('[data-analyze-form]', root)
    .onclick =
    async () => {
      const payload =
        readFormPayload(
          form,
          existing,
          draftStartedAt,
          pendingAnalysis
        );

      const analysis =
        await runAnalysis(
          payload
        );

      if (analysis) {
        pendingAnalysis =
          analysis;

        updateJobEditorAnalysisNote(
          root,
          analysis
        );
      }
    };

  $('[data-save-job]', root)
    .onclick =
    async () => {
      try {
        const payload =
          readFormPayload(
            form,
            existing,
            draftStartedAt,
            pendingAnalysis
          );

        if (
          !String(
            payload.company || ''
          ).trim() &&
          !String(
            payload.job_title || ''
          ).trim()
        ) {
          throw new Error(
            'Add at least a company or job title.'
          );
        }

        await api(
          'save_application',
          payload
        );

        closeModal();

        await reloadData();

        toast(
          existing.id
            ? 'Application updated.'
            : 'Application saved.'
        );

      } catch (error) {
        toast(
          error.message,
          'error'
        );
      }
    };
}

async function deleteOne(id) {
  const app =
    state.applications.find(
      item =>
        item.id === id
    );

  const confirmed =
    await confirmDialog(
      'Delete this job?',
      `${
        app?.company || ''
      } ${
        app?.job_title || ''
      } will be removed from JAM.`,
      'Delete'
    );

  if (!confirmed) {
    return;
  }

  try {
    await api(
      'delete_application',
      id
    );

    state.selectedIds.delete(id);

    await reloadData();

    toast(
      'Job deleted.'
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

function editSelectedApplication() {
  if (state.selectedIds.size !== 1) {
    return;
  }

  const id =
    Number(
      [...state.selectedIds][0]
    );

  const app =
    state.applications.find(
      item => item.id === id
    );

  if (app) {
    openJobModal(app);
  }
}

async function bulkDelete() {
  const ids =
    [...state.selectedIds];

  if (!ids.length) {
    return;
  }

  const confirmed =
    await confirmDialog(
      'Delete selected jobs?',
      `${ids.length} selected job(s) will be permanently removed from JAM.`,
      'Delete selected'
    );

  if (!confirmed) {
    return;
  }

  try {
    await api(
      'delete_applications',
      ids
    );

    state.selectedIds.clear();

    await reloadData();

    toast(
      `${ids.length} job(s) deleted.`
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

function openAnalysisOverlay(
  content
) {
  const root =
    $('#analysisOverlayRoot');

  root.classList.add(
    'active'
  );

  root.innerHTML = `
    <div
      class="analysis-overlay-backdrop"
      data-analysis-backdrop
    >

      <section
        class="analysis-overlay-card"
      >
        ${content}
      </section>

    </div>
  `;

  $('[data-analysis-backdrop]', root)
    ?.addEventListener(
      'click',
      event => {
        if (
          event.target.hasAttribute(
            'data-analysis-backdrop'
          )
        ) {
          closeAnalysisOverlay();
        }
      }
    );

  return root;
}

function closeAnalysisOverlay() {
  const root =
    $('#analysisOverlayRoot');

  root.classList.remove(
    'active'
  );

  root.innerHTML =
    '';
}

function showAnalysisLoading() {
  const root =
    openAnalysisOverlay(`
      <div
        class="analysis-overlay-body loading-analysis"
      >

        <div class="spinner"></div>

        <strong id="analysisLoadingText">
          Validating job offer…
        </strong>

        <p class="muted">
          JAM is comparing the offer
          against the selected CV locally.
        </p>

      </div>
    `);

  const messages = [
    'Validating job offer…',
    'Extracting job requirements…',
    'Reading selected CV…',
    'Building CV evidence profile…',
    'Comparing job and CV evidence…',
    'Calculating evidence-based score…'
  ];

  let index =
    0;

  const timer =
    setInterval(
      () => {
        index =
          Math.min(
            index + 1,
            messages.length - 1
          );

        const node =
          $(
            '#analysisLoadingText',
            root
          );

        if (node) {
          node.textContent =
            messages[index];
        }
      },
      420
    );

  return timer;
}

function chips(
  values,
  cls
) {
  if (!values?.length) {
    return `
      <span class="muted">
        None detected
      </span>
    `;
  }

  return `
    <div class="chips">

      ${
        values
          .map(
            value => `
              <span
                class="chip ${cls}"
              >
                ${escapeHtml(value)}
              </span>
            `
          )
          .join('')
      }

    </div>
  `;
}

function showAnalysisResult(
  analysis
) {
  const scoreAvailable =
    Boolean(
      analysis.score_available &&
      analysis.score !== null &&
      analysis.score !== undefined
    );

  const score =
    scoreAvailable
      ? Number(
          analysis.score
        )
      : 0;

  const requiredYears =
    analysis.required_years;

  const cvYears =
    analysis.cv_years;

  const experienceText =
    requiredYears == null
      ? `No explicit experience minimum detected. CV timeline estimate: ${
          cvYears == null
            ? 'unclear'
            : `${cvYears} year(s)`
        }.`
      : `Job requirement: about ${requiredYears}+ year(s). CV timeline estimate: ${
          cvYears == null
            ? 'unclear'
            : `${cvYears} year(s)`
        }.`;

  const salary =
    analysis.salary;

  const salaryText =
    salary
      ? `${
          salary.min ?? ''
        }${
          salary.max &&
          salary.max !== salary.min
            ? `–${salary.max}`
            : ''
        } ${
          salary.currency || ''
        } ${
          salary.period || ''
        }`.trim()
      : 'No reliable salary detected.';

  const noScoreReasons =
    analysis.no_score_reasons ||
    [];

  const root =
    openAnalysisOverlay(`
      <div class="analysis-overlay-head">

        <div>

          <div class="eyebrow">
            CV MATCH RESULT
          </div>

          <h2>
            ${
              scoreAvailable
                ? `${score}% match`
                : 'No reliable score'
            }
          </h2>

        </div>

        <button
          class="icon-btn"
          data-close-analysis
        >
          ×
        </button>

      </div>

      <div class="analysis-overlay-body">

        <div class="analysis-result-top">

          ${
            scoreAvailable
              ? `
                <div
                  class="score-ring"
                  style="--score:${score}"
                >
                  <strong>
                    ${score}%
                  </strong>
                </div>
              `
              : `
                <div class="analysis-no-score">
                  NO<br>SCORE
                </div>
              `
          }

          <div class="analysis-score-meta">

            <strong>
              ${
                escapeHtml(
                  analysis.score_label ||
                  (
                    scoreAvailable
                      ? 'Evidence-based match'
                      : 'Insufficient evidence'
                  )
                )
              }
            </strong>

            <div class="confidence-line">

              <span>
                Evidence confidence
              </span>

              <b>
                ${
                  Number(
                    analysis.confidence ||
                    0
                  )
                }%
              </b>

            </div>

            <p class="muted">
              ${
                scoreAvailable
                  ? 'The score is based only on comparison dimensions JAM could actually detect.'
                  : escapeHtml(
                      noScoreReasons[0] ||
                      'JAM does not have enough reliable evidence to calculate a percentage.'
                    )
              }
            </p>

          </div>

        </div>

        <div
          class="analysis-groups"
          style="margin-top:18px"
        >

          <div class="analysis-group">

            <h4>
              Matched skills & tools
            </h4>

            ${
              chips(
                analysis.matched_skills,
                'good'
              )
            }

          </div>

          <div class="analysis-group">

            <h4>
              Missing required /
              not clearly found
            </h4>

            ${
              chips(
                analysis
                  .missing_required_skills
                  ?.length
                  ? analysis
                      .missing_required_skills
                  : analysis
                      .missing_skills,
                'missing'
              )
            }

          </div>

          <div class="analysis-group">

            <h4>
              Experience
            </h4>

            <div>
              ${
                escapeHtml(
                  experienceText
                )
              }
            </div>

          </div>

          <div class="analysis-group">

            <h4>
              Languages
            </h4>

            <div
              style="margin-bottom:7px"
            >
              Matched
            </div>

            ${
              chips(
                analysis.matched_languages,
                'good'
              )
            }

            <div
              style="margin:10px 0 7px"
            >
              Missing / not found
            </div>

            ${
              chips(
                analysis.missing_languages,
                'missing'
              )
            }

          </div>

          <div class="analysis-group">

            <h4>
              Responsibilities /
              domain evidence
            </h4>

            <div
              style="margin-bottom:7px"
            >
              Matched
            </div>

            ${
              chips(
                analysis.matched_concepts,
                'good'
              )
            }

            <div
              style="margin:10px 0 7px"
            >
              Not clearly evidenced
            </div>

            ${
              chips(
                analysis.missing_concepts,
                'missing'
              )
            }

          </div>

          <div class="analysis-group">

            <h4>
              Salary detected
            </h4>

            <div>
              ${
                escapeHtml(
                  salaryText
                )
              }
            </div>

          </div>

          ${
            noScoreReasons.length > 1
              ? `
                <div class="analysis-group">

                  <h4>
                    Why JAM did not score this
                  </h4>

                  <ul>
                    ${
                      noScoreReasons
                        .map(
                          reason => `
                            <li>
                              ${escapeHtml(reason)}
                            </li>
                          `
                        )
                        .join('')
                    }
                  </ul>

                </div>
              `
              : ''
          }

          <div class="analysis-group">

            <h4>
              What to review
            </h4>

            <ul>
              ${
                (
                  analysis.suggestions ||
                  []
                )
                  .map(
                    suggestion => `
                      <li>
                        ${escapeHtml(
                          suggestion
                        )}
                      </li>
                    `
                  )
                  .join('')
                ||
                `
                  <li>
                    No specific changes suggested.
                  </li>
                `
              }
            </ul>

          </div>

        </div>

        <div
          style="
            display:flex;
            justify-content:flex-end;
            margin-top:16px
          "
        >
          <button
            class="btn gold"
            data-close-analysis
          >
            Done
          </button>
        </div>

      </div>
    `);

  $$(
    '[data-close-analysis]',
    root
  ).forEach(
    button => {
      button.onclick =
        closeAnalysisOverlay;
    }
  );
}

async function runAnalysis(payload) {
  const timer =
    showAnalysisLoading();

  try {
    const result =
      await api(
        'analyze_job',
        payload
      );

    clearInterval(timer);

    showAnalysisResult(
      result.analysis
    );

    if (payload.id) {
      await reloadData();
    }

    return result.analysis;

  } catch (error) {
    clearInterval(timer);

    closeAnalysisOverlay();

    toast(
      error.message,
      'error'
    );

    return null;
  }
}

async function chooseCv() {
  try {
    const result =
      await api(
        'choose_cv'
      );

    if (result.cancelled) {
      return;
    }

    state.settings.cv_path =
      result.path;

    renderSettings();

    toast(
      `CV selected: ${
        fileName(
          result.path
        )
      }`
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

async function openCaptureMode() {
  try {
    const corner =
      state.settings
        .capture_corner ||
      'top-right';

    await api(
      'open_capture_window',
      corner
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

function describeActiveFilters() {
  const summary = [];
  const search = String($('#searchInput')?.value || '').trim();
  if (search) summary.push(`Search: ${search}`);

  const labels = {
    company: 'Company',
    job_title: 'Job title',
    status: 'Status',
    match_score: 'Score',
    rating: 'Rating',
    location: 'Location',
    date_saved: 'Date saved',
    source: 'Source'
  };

  FILTER_COLUMNS.forEach(column => {
    const selected = state.tableFilters[column];
    if (selected === null) return;
    const values = [...selected].map(value => filterValueLabel(column, value));
    summary.push(`${labels[column]}: ${values.length ? values.join(', ') : 'None'}`);
  });

  if (state.tableSort.column && state.tableSort.direction) {
    summary.push(
      `Sort: ${labels[state.tableSort.column] || state.tableSort.column} ${
        state.tableSort.direction === 'asc' ? 'ascending' : 'descending'
      }`
    );
  }

  if (state.selectedIds.size) {
    summary.push(`Manual selection: ${state.selectedIds.size} application(s)`);
  }

  return summary.length
    ? summary
    : ['No filters applied — all visible applications.'];
}

function showExportCompleted(kind, path) {
  const root = openModal({
    kicker: 'EXPORT COMPLETE',
    title: `${kind} file created`,
    body: `
      <div class="export-success-mark">✓</div>
      <p class="muted" style="text-align:center">
        Your JAM export is ready.
      </p>
      <div class="export-path">${escapeHtml(path)}</div>
    `,
    actions: `
      <button class="btn secondary" data-export-close>Close</button>
      <button class="btn secondary" data-export-folder>Open folder</button>
      <button class="btn gold" data-export-file>Open file now</button>
    `
  });

  $('[data-export-close]', root).onclick = closeModal;
  $('[data-export-folder]', root).onclick = async () => {
    try { await api('open_parent_folder', path); }
    catch (error) { toast(error.message, 'error'); }
  };
  $('[data-export-file]', root).onclick = async () => {
    try { await api('open_path', path); }
    catch (error) { toast(error.message, 'error'); }
  };
}

async function exportCurrent(kind) {
  const selected = [...state.selectedIds];
  const ids = selected.length
    ? selected
    : getFilteredApplications().map(app => app.id);

  try {
    const result = await api(
      kind === 'Excel' ? 'export_excel' : 'export_pdf',
      ids,
      describeActiveFilters()
    );

    state.exportHistory = result.history || state.exportHistory;
    renderExportHistory();
    showExportCompleted(kind, result.path);
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function importExcel() {
  try {
    const result = await api('import_excel_dialog');
    if (result.cancelled) return;

    await reloadData();
    const summary = result.summary || {};

    openModal({
      kicker: 'EXCEL IMPORT',
      title: 'Import complete',
      body: `
        <div class="analysis-group">
          <h4>Applications imported</h4>
          <div>${Number(summary.imported || 0)}</div>
        </div>
        <div class="analysis-group">
          <h4>Rows skipped</h4>
          <div>${Number(summary.skipped || 0)}</div>
        </div>
        <div class="analysis-group">
          <h4>Columns detected</h4>
          <div>${escapeHtml((summary.mapped_fields || []).join(', ') || 'None')}</div>
        </div>
        <p class="muted">
          JAM matched columns by their header names, so the Excel column order did not matter.
        </p>
      `,
      actions: `<button class="btn gold" data-import-done>Done</button>`
    });

    $('[data-import-done]').onclick = closeModal;
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function saveProject() {
  try {
    const result =
      await api(
        'save_project'
      );

    if (result.cancelled) {
      return;
    }

    state.recentProjects =
      result.recent_projects ||
      [];

    toast(
      `Saved ${
        fileName(
          result.path
        )
      }`
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

async function openProject() {
  if (
    state.applications.length &&
    !await confirmDialog(
      'Open another JAM project?',
      'Opening a .jam project replaces the current in-app dataset. Save the current project first if needed.',
      'Open project'
    )
  ) {
    return;
  }

  try {
    const result =
      await api(
        'open_project_dialog'
      );

    if (result.cancelled) {
      return;
    }

    await reloadData();

    toast(
      `Opened ${
        fileName(
          result.project.path
        )
      }`
    );

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

function showRecentProjects() {
  const body =
    state.recentProjects.length
      ? `
        <div class="history-list">

          ${
            state.recentProjects
              .map(
                project => `
                  <div class="history-item">

                    <strong>
                      ${escapeHtml(
                        project.name
                      )}
                    </strong>

                    <span
                      title="${
                        escapeHtml(
                          project.path
                        )
                      }"
                    >
                      ${escapeHtml(
                        project.path
                      )}
                    </span>

                    <span>
                      ${formatDate(
                        project.last_opened_at
                      )}
                    </span>

                    <button
                      class="btn secondary"
                      data-open-recent="${
                        escapeHtml(
                          project.path
                        )
                      }"
                    >
                      Open
                    </button>

                  </div>
                `
              )
              .join('')
          }

        </div>
      `
      : `
        <p class="muted">
          No recent .jam projects yet.
        </p>
      `;

  const root =
    openModal({
      kicker:
        'PROJECTS',

      title:
        'Recent Projects',

      body,

      wide:
        true
    });

  $$(
    '[data-open-recent]',
    root
  ).forEach(
    button => {
      button.onclick =
      async () => {
        const confirmed =
          state.applications.length
            ? await confirmDialog(
                'Replace current data?',
                'Opening this project replaces the current in-app dataset.',
                'Open'
              )
            : true;

        if (!confirmed) {
          return;
        }

        try {
          const result =
            await api(
              'open_recent_project',
              button.dataset.openRecent
            );

          closeModal();

          await reloadData();

          toast(
            `Opened ${
              fileName(
                result.project.path
              )
            }`
          );

        } catch (error) {
          toast(
            error.message,
            'error'
          );
        }
      };
    }
  );
}

function showAbout() {
  openModal({
    kicker:
      'ABOUT JAM',

    title:
      'JAM - Job Application Manager',

    body: `
      <div style="text-align:center">

        <img
          src="../assets/branding/jam_logo.png"
          style="
            width:150px;
            max-height:90px;
            object-fit:contain
          "
          alt="JAM"
        >

        <p class="muted">
          A local-first Windows
          job application manager
          by Farouk.
        </p>

        <div class="analysis-group">

          <strong>
            Version
          </strong>

          <div>
            0.1.0 development
          </div>

        </div>

        <p class="muted">
          Track opportunities,
          capture jobs while browsing,
          manage your pipeline,
          export clean reports
          and compare roles
          with your CV locally.
        </p>

      </div>
    `,

    actions: `
      <button
        class="btn gold"
        data-about-close
      >
        Close
      </button>
    `
  });

  $('[data-about-close]')
    ?.addEventListener(
      'click',
      closeModal
    );
}

function showContact() {
  const root =
    openModal({
      kicker:
        'CONTACT DEVELOPER',

      title:
        'Farouk',

      body: `
        <p class="muted">
          For feedback,
          bugs, ideas or
          project information,
          use the official website
          or developer GitHub.
        </p>

        <div class="button-row">

          <button
            class="btn gold"
            data-site
          >
            damergi.com
          </button>

          <button
            class="btn secondary"
            data-repo
          >
            GitHub
          </button>

        </div>
      `
    });

  $('[data-site]', root)
    .onclick =
    () =>
      api(
        'open_url',
        'https://www.damergi.com'
      );

  $('[data-repo]', root)
    .onclick =
    () =>
      api(
        'open_url',
        'https://github.com/dafarouk'
      );
}

function showSupport() {
  const root = openModal({
    kicker: 'JAM',
    title: 'Support JAM',
    body: `
      <div class="support-modal-copy">
        <div class="support-modal-heart" aria-hidden="true">♡</div>

        <h3>Support JAM</h3>

        <p>
          JAM is completely free. If the app helps you, any little support would
          be genuinely appreciated :)
        </p>

        <div class="support-free-line">
          ✓ Always free to use
        </div>
      </div>
    `,
    actions: `
      <button class="btn secondary" data-support-close>Cancel</button>
      <button class="btn gold" data-support-paypal>PayPal</button>
      <button class="btn gold" data-support-kofi>Ko-fi</button>
    `
  });

  root.classList.add('support-modal-root');

  $('[data-support-close]', root).onclick = closeModal;
  $('[data-support-paypal]', root).onclick = () =>
    api('open_url', 'https://paypal.me/BigBossManTN');
  $('[data-support-kofi]', root).onclick = () =>
    api('open_url', 'https://ko-fi.com/bigbossmantn');
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (_) {
    const area = document.createElement('textarea');
    area.value = text;
    area.style.position = 'fixed';
    area.style.opacity = '0';
    document.body.appendChild(area);
    area.select();
    const ok = document.execCommand('copy');
    area.remove();
    return ok;
  }
}

async function showLogs() {
  try {
    const result = await api('get_logs');
    const entries = result.entries || [];

    const body = `
      <p class="log-help">
        ✓ green means a normal successful action, ⚠ orange means something worth checking,
        and ✕ red means JAM recorded an error. Most users only need to look at red entries.
      </p>

      <div class="log-friendly-list">
        ${
          entries.length
            ? entries.map(entry => `
                <div class="log-entry ${escapeHtml(entry.kind || 'info')}">
                  <span class="log-symbol">${escapeHtml(entry.symbol || '•')}</span>
                  <span class="log-time">${escapeHtml(entry.timestamp || '')}</span>
                  <span class="log-message">${escapeHtml(entry.message || '')}</span>
                </div>
              `).join('')
            : `<div class="panel"><p class="muted">No log entries yet. JAM is quiet.</p></div>`
        }
      </div>
    `;

    const root = openModal({
      kicker: 'DIAGNOSTICS',
      title: 'JAM Activity & Logs',
      body,
      actions: `
        <button class="btn secondary" data-log-close>Close</button>
        <button class="btn gold" data-copy-logs>Copy logs</button>
      `,
      wide: true
    });

    $('[data-log-close]', root).onclick = closeModal;
    $('[data-copy-logs]', root).onclick = async () => {
      const ok = await copyText(result.text || '');
      toast(ok ? 'Logs copied.' : 'Could not copy logs.', ok ? 'success' : 'error');
    };
  } catch (error) {
    toast(error.message, 'error');
  }
}

async function resetFlow() {
  const first =
    await confirmDialog(
      'Reset all JAM data?',
      'Are you sure? All tracked JAM applications, settings, recent-project history and export history inside JAM will be gone.',
      "Yes, I'm sure"
    );

  if (!first) {
    return;
  }

  let cancelled =
    false;

  let remaining =
    5;

  const root =
    openModal({
      kicker:
        'FINAL RESET WARNING',

      title:
        'Last chance to cancel',

      body: `
        <p class="muted">
          JAM will reset automatically
          when the countdown reaches zero.
        </p>

        <div
          class="countdown"
          id="resetCountdown"
        >
          5
        </div>
      `,

      actions: `
        <button
          class="btn secondary"
          data-cancel-reset
        >
          Cancel reset
        </button>
      `
    });

  $('[data-cancel-reset]', root)
    .onclick =
    () => {
      cancelled =
        true;

      closeModal();

      toast(
        'Reset cancelled.'
      );
    };

  const timer =
    setInterval(
      async () => {
        if (cancelled) {
          clearInterval(timer);
          return;
        }

        remaining -= 1;

        const node =
          $('#resetCountdown');

        if (node) {
          node.textContent =
            String(remaining);
        }

        if (
          remaining <= 0
        ) {
          clearInterval(timer);

          try {
            await api(
              'reset_all_data'
            );

            closeModal();

            state.selectedIds.clear();

            clearTableFilters();

            await reloadData();

            navigate(
              'dashboard'
            );

            toast(
              'JAM data reset complete.'
            );

          } catch (error) {
            closeModal();

            toast(
              error.message,
              'error'
            );
          }
        }
      },
      1000
    );
}

async function saveSettings() {
  try {
    const currency = $('#salaryCurrency').value || 'EUR';

    await api('save_setting', 'salary_target_min', $('#salaryMin').value.trim());
    await api('save_setting', 'salary_target_max', $('#salaryMax').value.trim());
    await api('save_setting', 'salary_currency', currency);

    state.settings.salary_target_min = $('#salaryMin').value.trim();
    state.settings.salary_target_max = $('#salaryMax').value.trim();
    state.settings.salary_currency = currency;

    toast('Settings saved.');
  } catch (error) {
    toast(error.message, 'error');
  }
}

function maybeShowOnboarding() {
  if (
    state.onboardingShown ||
    state.settings.cv_path
  ) {
    return;
  }

  state.onboardingShown =
    true;

  const root =
    openModal({
      kicker:
        'WELCOME TO JAM',

      title:
        'Add your CV for matching',

      body: `
        <p class="muted">
          JAM works as a job tracker
          without a CV.
          Adding one now unlocks
          the optional local
          CV Match Analyzer.
        </p>
      `,

      actions: `
        <button
          class="btn secondary"
          data-skip-cv
        >
          Skip for now
        </button>

        <button
          class="btn gold"
          data-add-cv-now
        >
          Add CV
        </button>
      `
    });

  $('[data-skip-cv]', root)
    .onclick =
    closeModal;

  $('[data-add-cv-now]', root)
    .onclick =
    async () => {
      closeModal();
      await chooseCv();
    };
}

function bindEvents() {
  setupPipelineDrag();
  setupCurrencyPicker();
  $$('.nav-item')
    .forEach(
      button => {
        button.onclick =
          () =>
            navigate(
              button.dataset.page
            );
      }
    );

  $$('[data-nav]')
    .forEach(
      button => {
        button.onclick =
          () =>
            navigate(
              button.dataset.nav
            );
      }
    );

  $$('[data-add-job]')
    .forEach(
      button => {
        button.onclick =
          () =>
            openJobModal();
      }
    );

  $('#dashboardAddBtn').onclick =
    () =>
      openJobModal();

  $('#addJobBtn').onclick =
    () =>
      openJobModal();

  $('#dashboardAnalyzerBtn').onclick =
    () =>
      navigate(
        'analyzer'
      );

  $('#captureBtn').onclick =
    openCaptureMode;

  $('#dashboardCaptureBtn').onclick =
    openCaptureMode;

  $('#chooseCvBtn').onclick =
    chooseCv;

  $('#settingsChooseCvBtn').onclick =
    chooseCv;

  $('#runAnalyzerBtn').onclick =
    () =>
      runAnalysis({
        job_title:
          $('#analyzerTitle')
            .value
            .trim(),

        description:
          $('#analyzerDescription')
            .value
            .trim()
      });

  $('#searchInput')
    .addEventListener(
      'input',
      renderTable
    );

  $('#clearTableFiltersBtn').onclick =
    clearTableFilters;

  $('.jobs-table thead')
    .addEventListener(
      'click',
      event => {
        const filterButton =
          event.target.closest(
            '[data-filter]'
          );

        if (filterButton) {
          event.stopPropagation();

          openColumnFilter(
            filterButton
              .dataset
              .filter,
            filterButton
          );

          return;
        }

        const sortButton =
          event.target.closest(
            '[data-sort]'
          );

        if (sortButton) {
          cycleSort(
            sortButton
              .dataset
              .sort
          );
        }
      }
    );

  document.addEventListener(
    'click',
    event => {
      const root =
        $('#tableFilterRoot');

      if (
        !root?.innerHTML
      ) {
        return;
      }

      if (
        event.target.closest(
          '[data-filter-popover]'
        )
      ) {
        return;
      }

      if (
        event.target.closest(
          '[data-filter]'
        )
      ) {
        return;
      }

      closeTableFilter();
    }
  );

  $('#selectAllRows').onchange =
    event => {
      getFilteredApplications()
        .forEach(
          app => {
            if (
              event.target.checked
            ) {
              state.selectedIds.add(
                app.id
              );
            } else {
              state.selectedIds.delete(
                app.id
              );
            }
          }
        );

      renderTable();
    };

  $('#jobsTableBody')
    .addEventListener(
      'change',
      event => {
        if (
          !event.target.classList.contains(
            'row-check'
          )
        ) {
          return;
        }

        const id =
          Number(
            event.target.dataset.id
          );

        if (
          event.target.checked
        ) {
          state.selectedIds.add(id);
        } else {
          state.selectedIds.delete(id);
        }

        updateSelectionUi();
      }
    );

  $('#jobsTableBody')
    .addEventListener(
      'click',
      event => {
        const deleteButton =
          event.target.closest(
            '[data-delete-id]'
          );

        if (deleteButton) {
          deleteOne(
            Number(
              deleteButton
                .dataset
                .deleteId
            )
          );

          return;
        }

        const editButton =
          event.target.closest(
            '.row-edit'
          );

        if (editButton) {
          const app =
            state.applications.find(
              item =>
                item.id ===
                Number(
                  editButton
                    .dataset
                    .id
                )
            );

          if (app) {
            openJobModal(app);
          }
        }
      }
    );

  $('#bulkDeleteBtn').onclick =
    bulkDelete;

  const editSelectedBtn =
    $('#editSelectedBtn');

  if (editSelectedBtn) {
    editSelectedBtn.onclick =
      editSelectedApplication;
  }

  $('#jobsTableBody')
    .addEventListener(
      'dblclick',
      event => {
        if (
          event.target.closest(
            'button, input, a, select, textarea'
          )
        ) {
          return;
        }

        const row =
          event.target.closest(
            'tr[data-id]'
          );

        if (!row) {
          return;
        }

        const app =
          state.applications.find(
            item =>
              item.id ===
              Number(row.dataset.id)
          );

        if (app) {
          openJobModal(app);
        }
      }
    );

  $('#exportExcelBtn').onclick =
    () =>
      exportCurrent(
        'Excel'
      );

  $('#exportPdfBtn').onclick =
    () =>
      exportCurrent(
        'PDF'
      );

  $('#exportHistory')
    .addEventListener(
      'click',
      async event => {
        const button =
          event.target.closest(
            '[data-open-path]'
          );

        if (!button) {
          return;
        }

        try {
          await api(
            'open_path',
            button.dataset.openPath
          );

        } catch (error) {
          toast(
            error.message,
            'error'
          );
        }
      }
    );

  $('#saveProjectBtn').onclick =
    saveProject;

  $('#openProjectBtn').onclick =
    openProject;

  $('#importExcelBtn').onclick =
    importExcel;

  $('#recentProjectsBtn').onclick =
    showRecentProjects;

  $('#aboutBtn').onclick =
    showAbout;

  $('#contactBtn').onclick =
    showContact;

  $('#supportBtn')?.addEventListener('click', showSupport);
  $('#supportTopBtn').onclick = showSupport;

  $('#openExportsFolderBtn').onclick =
    async () => {
      try {
        await api(
          'open_exports_folder'
        );

      } catch (error) {
        toast(
          error.message,
          'error'
        );
      }
    };

  $('#saveSettingsBtn').onclick =
    saveSettings;

  $('#logsBtn').onclick =
    showLogs;

  $('#backupBtn').onclick =
    async () => {
      try {
        const result =
          await api(
            'create_backup'
          );

        toast(
          `Backup created: ${
            fileName(
              result.path
            )
          }`
        );

      } catch (error) {
        toast(
          error.message,
          'error'
        );
      }
    };


  $('#backupFolderBtn').onclick =
    async () => {
      try {
        await api('open_backup_folder');
      } catch (error) {
        toast(error.message, 'error');
      }
    };

  $('#resetBtn').onclick =
    resetFlow;
}

async function init() {
  if (initialized) {
    return;
  }

  initialized =
    true;

  bindEvents();

  try {
    await reloadData();

    const tutorialStarted =
      window.JAM_TUTORIAL?.autoStart?.(
        state.settings || {}
      ) === true;

    if (!tutorialStarted) {
      maybeShowOnboarding();
    }

  } catch (error) {
    toast(
      error.message,
      'error'
    );
  }
}

document.addEventListener(
  'pywebviewready',
  init
);

window.addEventListener(
  'DOMContentLoaded',
  () => {
    setTimeout(
      () => {
        if (
          window.pywebview?.api
        ) {
          init();
        }
      },
      150
    );
  }
);