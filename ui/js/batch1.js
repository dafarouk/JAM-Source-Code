(() => {
  'use strict';

  let initialized = false;
  let showArchived = false;
  let autosaveTimer = null;
  let mainDraftStartedAt = null;

  const COUNTRY_BY_CURRENCY = {
    EUR: 'eu',
    USD: 'us',
    TND: 'tn',
    MAD: 'ma',
    DZD: 'dz',
    LYD: 'ly',
    EGP: 'eg',
    SAR: 'sa',
    AED: 'ae',
    QAR: 'qa',
    KWD: 'kw',
    BHD: 'bh',
    OMR: 'om',
    JOD: 'jo',
    LBP: 'lb',
    IQD: 'iq',
    TRY: 'tr',
    GBP: 'gb',
    CAD: 'ca',
    CHF: 'ch'
  };

  const CURRENCY_FR = {
    EUR: ['Euro', 'euro euros zone euro france europe'],
    USD: ['Dollar américain', 'dollar dollars américain etats unis états-unis usa amerique amérique'],
    TND: ['Dinar tunisien', 'tunisie tunis tunisien tunisienne dinar'],
    MAD: ['Dirham marocain', 'maroc marocain marocaine dirham'],
    DZD: ['Dinar algérien', 'algerie algérie algerien algérien dinar'],
    LYD: ['Dinar libyen', 'libye libyen libyenne dinar'],
    EGP: ['Livre égyptienne', 'egypte égypte egyptien égyptien livre'],
    SAR: ['Riyal saoudien', 'arabie saoudite saoudien riyal'],
    AED: ['Dirham des Émirats', 'emirats émirats eau dubai abu dhabi dirham'],
    QAR: ['Riyal qatari', 'qatar qatari riyal'],
    KWD: ['Dinar koweïtien', 'koweit koweït koweitien koweïtien dinar'],
    BHD: ['Dinar bahreïni', 'bahrein bahreïn bahreini bahreïni dinar'],
    OMR: ['Rial omanais', 'oman omanais rial'],
    JOD: ['Dinar jordanien', 'jordanie jordanien dinar'],
    LBP: ['Livre libanaise', 'liban libanais livre'],
    IQD: ['Dinar irakien', 'irak iraq irakien dinar'],
    TRY: ['Livre turque', 'turquie turc turque livre'],
    GBP: ['Livre sterling', 'royaume uni angleterre britannique uk livre sterling'],
    CAD: ['Dollar canadien', 'canada canadien dollar'],
    CHF: ['Franc suisse', 'suisse swiss franc']
  };

  function tr(text) {
    if (window.JAM_I18N?.translate) {
      return window.JAM_I18N.translate(text);
    }

    return text;
  }

  function currentLanguage() {
    return window.JAM_I18N?.language || 'en';
  }

  function currencyName(currency) {
    if (
      currentLanguage() === 'fr' &&
      CURRENCY_FR[currency.code]
    ) {
      return CURRENCY_FR[currency.code][0];
    }

    return currency.name;
  }

  function currencyFlagPath(code) {
    const country = COUNTRY_BY_CURRENCY[code] || 'eu';
    return `../assets/flags/${country}.png`;
  }

  function installOfflineCurrencyFlags() {
    if (typeof window.currencyByCode !== 'function') {
      return;
    }

    window.currencyDisplay = function(currency) {
      return `${currency.code} — ${currencyName(currency)}`;
    };

    window.currencyMatches = function(query) {
      const needle = normalizeText(query);

      if (!needle) {
        return CURRENCIES;
      }

      return CURRENCIES.filter(currency => {
        const french = CURRENCY_FR[currency.code];

        return normalizeText([
          currency.code,
          currency.name,
          currency.countries,
          french?.[0] || '',
          french?.[1] || ''
        ].join(' ')).includes(needle);
      });
    };

    window.renderCurrencySuggestions = function(query = '') {
      const root = $('#salaryCurrencySuggestions');
      if (!root) return;

      const matches = window.currencyMatches(query);

      root.innerHTML = matches.map(currency => `
        <button
          type="button"
          class="currency-option"
          data-currency-code="${escapeHtml(currency.code)}"
        >
          <img
            class="currency-flag-img"
            src="${currencyFlagPath(currency.code)}"
            alt="${escapeHtml(currency.code)}"
          >

          <span class="code">
            ${escapeHtml(currency.code)}
          </span>

          <span>
            ${escapeHtml(currencyName(currency))}
            <small>
              ${escapeHtml(currency.countries.split(' ').slice(0, 4).join(' '))}
            </small>
          </span>
        </button>
      `).join('');

      root.hidden = matches.length === 0;

      $$('[data-currency-code]', root).forEach(button => {
        button.onclick = () => {
          window.selectSalaryCurrency(button.dataset.currencyCode);
          root.hidden = true;
        };
      });
    };

    window.selectSalaryCurrency = function(code) {
      const currency = window.currencyByCode(code || 'EUR');
      const picker = $('#salaryCurrencyPicker');
      const input = $('#salaryCurrencySearch');
      const hidden = $('#salaryCurrency');

      if (!picker || !input || !hidden) {
        return;
      }

      hidden.value = currency.code;
      input.value = window.currencyDisplay(currency);

      let flag = $('#salarySelectedFlag');

      if (!flag) {
        flag = document.createElement('img');
        flag.id = 'salarySelectedFlag';
        flag.className = 'salary-selected-flag';
        picker.prepend(flag);
      }

      flag.src = currencyFlagPath(currency.code);
      flag.alt = currency.code;
    };

    try {
      window.selectSalaryCurrency(
        state.settings?.salary_currency || 'EUR'
      );
    } catch (_) {
      // The settings page may not be ready yet. renderSettings will call it.
    }
  }

  function installLanguageSyncOnReload() {
    const originalReload = window.reloadData;

    if (typeof originalReload !== 'function') {
      return;
    }

    window.reloadData = async function(...args) {
      const result = await originalReload(...args);
      const language = state.settings?.language || 'en';

      if (
        window.JAM_I18N?.setLanguage &&
        window.JAM_I18N.language !== language
      ) {
        await window.JAM_I18N.setLanguage(language, false);
      }

      return result;
    };
  }

  // ============================================================
  // ARCHIVE BEHAVIOR
  // ============================================================

  function installArchiveBehavior() {
    const originalGetFiltered = window.getFilteredApplications;

    if (typeof originalGetFiltered === 'function') {
      window.getFilteredApplications = function() {
        const rows = originalGetFiltered();
        const search = normalizeText($('#searchInput')?.value || '');

        if (showArchived || search) {
          return rows;
        }

        return rows.filter(
          application => application.status !== 'Archived'
        );
      };
    }

    const toolbar = $('#applicationsPage .toolbar-left');

    if (
      toolbar &&
      !$('#archiveVisibilityBtn')
    ) {
      const button = document.createElement('button');
      button.id = 'archiveVisibilityBtn';
      button.className = 'btn secondary archive-toggle';
      button.type = 'button';

      const refreshLabel = () => {
        button.textContent = showArchived
          ? tr('Hide archived')
          : tr('Show archived');

        button.classList.toggle('active', showArchived);
      };

      button.onclick = () => {
        showArchived = !showArchived;
        refreshLabel();
        renderTable();
      };

      toolbar.appendChild(button);
      refreshLabel();
    }

    renderTable();
  }

  // ============================================================
  // MAIN ADD-JOB AUTOSAVE / CRASH RECOVERY
  // ============================================================

  function jobFormIsNew(form) {
    return Boolean(form && !String(form.dataset.id || '').trim());
  }

  function collectMainDraft(form) {
    if (!form || !jobFormIsNew(form)) {
      return null;
    }

    const data = Object.fromEntries(
      new FormData(form).entries()
    );

    const meaningful = [
      data.company,
      data.job_title,
      data.location,
      data.url,
      data.description,
      data.source,
      data.notes,
      data.salary_text,
      data.contact_name,
      data.contact_url
    ].some(value => String(value || '').trim());

    const rating = Number(data.rating || 0);
    const status = String(data.status || 'Saved');

    if (
      !meaningful &&
      rating === 0 &&
      status === 'Saved'
    ) {
      return null;
    }

    if (!mainDraftStartedAt) {
      mainDraftStartedAt = new Date().toISOString();
    }

    data.rating = rating;
    data.date_saved = mainDraftStartedAt;

    return data;
  }

  function scheduleMainDraftSave(form) {
    clearTimeout(autosaveTimer);

    autosaveTimer = setTimeout(
      async () => {
        if (!form.isConnected) {
          return;
        }

        const payload = collectMainDraft(form);

        try {
          if (payload) {
            await api(
              'save_draft',
              'main_job',
              payload
            );
          } else {
            await api(
              'clear_draft',
              'main_job'
            );
          }
        } catch (error) {
          console.debug('JAM draft autosave skipped:', error);
        }
      },
      450
    );
  }

  function installMainDraftAutosave() {
    document.addEventListener(
      'input',
      event => {
        const form = event.target.closest?.('#jobForm');

        if (
          form &&
          jobFormIsNew(form)
        ) {
          scheduleMainDraftSave(form);
        }
      },
      true
    );

    document.addEventListener(
      'change',
      event => {
        const form = event.target.closest?.('#jobForm');

        if (
          form &&
          jobFormIsNew(form)
        ) {
          scheduleMainDraftSave(form);
        }
      },
      true
    );

    document.addEventListener(
      'click',
      event => {
        const form = event.target.closest?.('#jobForm');

        if (
          form &&
          jobFormIsNew(form) &&
          event.target.closest(
            '[data-status-option], [data-star], [data-star-clear], [data-source-choice]'
          )
        ) {
          setTimeout(
            () => scheduleMainDraftSave(form),
            0
          );
        }

        if (
          event.target.closest('[data-save-job]')
        ) {
          clearTimeout(autosaveTimer);
        }

        if (
          event.target.closest('[data-close-modal]') ||
          event.target.hasAttribute?.('data-modal-backdrop')
        ) {
          const openForm = $('#jobForm');
          const payload = collectMainDraft(openForm);

          if (payload) {
            api('save_draft', 'main_job', payload).catch(() => {});
          }
        }

        if (
          event.target.closest('[data-cancel-job]')
        ) {
          clearTimeout(autosaveTimer);
          mainDraftStartedAt = null;
          api('clear_draft', 'main_job').catch(() => {});
        }
      },
      true
    );
  }

  function waitUntilModalFree(callback, attempts = 30) {
    const root = $('#modalRoot');

    if (
      !root?.classList.contains('active') ||
      attempts <= 0
    ) {
      callback();
      return;
    }

    setTimeout(
      () => waitUntilModalFree(callback, attempts - 1),
      250
    );
  }

  async function promptRecoveredMainDraft() {
    let result;

    try {
      result = await api(
        'get_draft',
        'main_job'
      );
    } catch (_) {
      return;
    }

    const draft = result.draft;

    if (
      !draft?.payload ||
      !Object.keys(draft.payload).length
    ) {
      return;
    }

    waitUntilModalFree(() => {
      const root = openModal({
        kicker: tr('RECOVERY'),
        title: tr('Unsaved job draft found'),
        body: `
          <div class="recovery-card">
            <p>
              ${escapeHtml(
                tr('JAM recovered an unsaved Add Job form from your previous session.')
              )}
            </p>

            <small class="muted">
              ${escapeHtml(tr('Recovered'))}: ${escapeHtml(draft.saved_at || '')}
            </small>
          </div>
        `,
        actions: `
          <button class="btn secondary" data-draft-discard>
            ${escapeHtml(tr('Discard draft'))}
          </button>

          <button class="btn gold" data-draft-restore>
            ${escapeHtml(tr('Restore draft'))}
          </button>
        `
      });

      $('[data-draft-discard]', root).onclick = async () => {
        await api('clear_draft', 'main_job').catch(() => {});
        mainDraftStartedAt = null;
        closeModal();
      };

      $('[data-draft-restore]', root).onclick = () => {
        mainDraftStartedAt = draft.payload.date_saved || null;
        closeModal();
        openJobModal(draft.payload);
      };
    });
  }

  // ============================================================
  // .JAM DIRTY-STATE PROTECTION / PROJECT RECOVERY
  // ============================================================

  function dirtyProjectChoice(projectState) {
    return new Promise(resolve => {
      const root = openModal({
        kicker: tr('UNSAVED PROJECT'),
        title: tr('Save .jam changes first?'),
        body: `
          <p class="muted">
            ${escapeHtml(
              tr('The active .jam project has changes that are not written to the project file yet.')
            )}
          </p>

          <div class="path-card">
            ${escapeHtml(projectState.current_path || '')}
          </div>
        `,
        actions: `
          <button class="btn secondary" data-dirty-cancel>
            ${escapeHtml(tr('Cancel'))}
          </button>

          <button class="btn danger subtle" data-dirty-discard>
            ${escapeHtml(tr('Continue without saving'))}
          </button>

          <button class="btn gold" data-dirty-save>
            ${escapeHtml(tr('Save & continue'))}
          </button>
        `
      });

      $('[data-dirty-cancel]', root).onclick = () => {
        closeModal();
        resolve(false);
      };

      $('[data-dirty-discard]', root).onclick = async () => {
        try {
          await api('discard_project_changes');
          closeModal();
          resolve(true);
        } catch (error) {
          toast(error.message, 'error');
        }
      };

      $('[data-dirty-save]', root).onclick = async () => {
        try {
          await api('save_current_project');
          closeModal();
          toast(tr('Project changes saved.'));
          resolve(true);
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    });
  }

  async function protectDirtyProject() {
    try {
      const result = await api('project_state');
      const projectState = result.project_state || {};

      if (!projectState.dirty) {
        return true;
      }

      return await dirtyProjectChoice(projectState);
    } catch (error) {
      toast(error.message, 'error');
      return false;
    }
  }

  function installDirtyProjectGuards() {
    const originalOpenProject = window.openProject;
    const originalResetFlow = window.resetFlow;

    const openButton = $('#openProjectBtn');

    if (openButton) {
      openButton.onclick = async () => {
        if (!(await protectDirtyProject())) {
          return;
        }

        if (
          state.applications.length &&
          !await confirmDialog(
            tr('Open another JAM project?'),
            tr('Opening a .jam project replaces the current in-app dataset. Save the current project first if needed.'),
            tr('Open project')
          )
        ) {
          return;
        }

        try {
          const result = await api('open_project_dialog', true);

          if (result.cancelled) {
            return;
          }

          await reloadData();
          toast(`${tr('Opened')} ${fileName(result.project.path)}`);
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    }

    const resetButton = $('#resetBtn');

    if (
      resetButton &&
      typeof originalResetFlow === 'function'
    ) {
      resetButton.onclick = async () => {
        if (await protectDirtyProject()) {
          await originalResetFlow();
        }
      };
    }

    // Recent-project buttons are created dynamically by app.js. Intercept them
    // before their original click handler so project changes cannot be lost.
    document.addEventListener(
      'click',
      async event => {
        const button = event.target.closest?.('[data-open-recent]');

        if (!button) {
          return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();

        if (!(await protectDirtyProject())) {
          return;
        }

        if (
          state.applications.length &&
          !await confirmDialog(
            tr('Replace current data?'),
            tr('Opening this project replaces the current in-app dataset.'),
            tr('Open')
          )
        ) {
          return;
        }

        try {
          const result = await api(
            'open_recent_project',
            button.dataset.openRecent,
            true
          );

          closeModal();
          await reloadData();

          toast(
            `${tr('Opened')} ${fileName(result.project.path)}`
          );
        } catch (error) {
          toast(error.message, 'error');
        }
      },
      true
    );
  }

  async function promptProjectRecovery() {
    let result;

    try {
      result = await api('project_state');
    } catch (_) {
      return;
    }

    const recovery = result.project_state?.recovery;

    if (!recovery) {
      return;
    }

    waitUntilModalFree(() => {
      const root = openModal({
        kicker: tr('PROJECT RECOVERY'),
        title: tr('Recovered .jam changes found'),
        body: `
          <p class="muted">
            ${escapeHtml(
              tr('JAM found an autosaved recovery copy from an interrupted .jam project session.')
            )}
          </p>

          <div class="recovery-grid">
            <div>
              <span>${escapeHtml(tr('Project'))}</span>
              <strong>${escapeHtml(fileName(recovery.current_project_path || '') || '—')}</strong>
            </div>

            <div>
              <span>${escapeHtml(tr('Applications'))}</span>
              <strong>${Number(recovery.application_count || 0)}</strong>
            </div>

            <div>
              <span>${escapeHtml(tr('Recovered'))}</span>
              <strong>${escapeHtml(recovery.saved_at || '')}</strong>
            </div>
          </div>
        `,
        actions: `
          <button class="btn secondary" data-project-recovery-discard>
            ${escapeHtml(tr('Discard recovery'))}
          </button>

          <button class="btn gold" data-project-recovery-restore>
            ${escapeHtml(tr('Restore recovered changes'))}
          </button>
        `,
        wide: true
      });

      $('[data-project-recovery-discard]', root).onclick = async () => {
        await api('discard_project_recovery').catch(() => {});
        closeModal();
        setTimeout(promptRecoveredMainDraft, 150);
      };

      $('[data-project-recovery-restore]', root).onclick = async () => {
        try {
          await api('restore_project_recovery');
          closeModal();
          await reloadData();
          toast(tr('Recovered project changes restored.'));
          setTimeout(promptRecoveredMainDraft, 150);
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    });
  }

  // ============================================================
  // BACKUP RESTORE
  // ============================================================

  function formatBytes(value) {
    const bytes = Number(value || 0);

    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  }

  async function showBackupRestore() {
    let result;

    try {
      result = await api('list_backups');
    } catch (error) {
      toast(error.message, 'error');
      return;
    }

    const backups = result.backups || [];

    const root = openModal({
      kicker: tr('BACKUP RESTORE'),
      title: tr('Restore a JAM backup'),
      wide: true,
      body: backups.length
        ? `
          <div class="backup-list">
            ${backups.map(item => `
              <div class="backup-list-item">
                <div>
                  <strong>${escapeHtml(item.name)}</strong>
                  <span>${escapeHtml(formatDate(item.created_at))} • ${escapeHtml(formatBytes(item.size))}</span>
                </div>

                <button
                  class="btn secondary"
                  data-restore-backup="${escapeHtml(item.path)}"
                >
                  ${escapeHtml(tr('Restore'))}
                </button>
              </div>
            `).join('')}
          </div>
        `
        : `
          <p class="muted">
            ${escapeHtml(tr('No JAM backups are available yet.'))}
          </p>
        `
    });

    $$('[data-restore-backup]', root).forEach(button => {
      button.onclick = async () => {
        const path = button.dataset.restoreBackup;

        if (!(await protectDirtyProject())) {
          return;
        }

        const confirmed = await confirmDialog(
          tr('Restore this backup?'),
          tr('JAM will create a safety backup of the current database first, then replace the live database with the selected backup.'),
          tr('Restore backup')
        );

        if (!confirmed) {
          return;
        }

        try {
          const restored = await api(
            'restore_backup',
            path,
            true
          );

          closeModal();
          await reloadData();

          toast(
            `${tr('Backup restored.')} ${fileName(restored.restore.restored)}`
          );
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    });
  }

  function injectBackupRestoreButton() {
    const actions = $('#settingsPage .backup-actions');

    if (
      !actions ||
      $('#restoreBackupBtn')
    ) {
      return;
    }

    const button = document.createElement('button');
    button.id = 'restoreBackupBtn';
    button.type = 'button';
    button.className = 'btn secondary';
    button.textContent = tr('Restore Backup');
    button.onclick = showBackupRestore;

    actions.insertBefore(
      button,
      $('#backupFolderBtn') || null
    );
  }

  // ============================================================
  // DATA LOCATIONS
  // ============================================================

  async function injectDataLocations() {
    const grid = $('#settingsPage .settings-grid');

    if (
      !grid ||
      $('#dataLocationsPanel')
    ) {
      return;
    }

    let result;

    try {
      result = await api('bootstrap');
    } catch (_) {
      return;
    }

    const locations = result.data_locations || {};

    const entries = [
      ['database', tr('Database'), locations.database],
      ['backups', tr('Backups'), locations.backups],
      ['exports', tr('Exports'), locations.exports],
      ['projects', tr('Projects'), locations.projects],
      ['logs', tr('Logs'), locations.logs],
      ['recovery', tr('Recovery'), locations.recovery]
    ];

    const panel = document.createElement('article');
    panel.id = 'dataLocationsPanel';
    panel.className = 'panel data-locations-panel';

    panel.innerHTML = `
      <span class="eyebrow">
        ${escapeHtml(tr('DATA LOCATIONS'))}
      </span>

      <h2>
        ${escapeHtml(tr('Where JAM stores your files'))}
      </h2>

      <p class="muted data-location-advice">
        ${escapeHtml(tr('For the best organization, keeping JAM data in the default locations is recommended, but you are free to choose a different folder for each item. Existing data is copied and the new path is used after restarting JAM.'))}
      </p>

      <div class="location-list">
        ${entries.map(([key, label, path]) => `
          <div class="location-row" data-location-row="${escapeHtml(key)}">
            <div>
              <strong>${escapeHtml(label)}</strong>
              <span data-location-path="${escapeHtml(key)}" title="${escapeHtml(path || '')}">${escapeHtml(path || '—')}</span>
            </div>

            <div class="location-actions">
              <button
                class="btn secondary compact-action"
                data-open-location="${escapeHtml(key)}"
              >
                ${escapeHtml(tr('Open'))}
              </button>

              <button
                class="btn secondary compact-action"
                data-edit-location="${escapeHtml(key)}"
              >
                ${escapeHtml(tr('Edit'))}
              </button>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    const leftStack =
      $('#settingsLeftColumn') ||
      $('#settingsPage .settings-left-stack');

    const danger =
      $('#settingsPage .danger-panel');

    if (leftStack) {
      // Data Locations belongs to the LEFT settings column.
      // Appending it here prevents CSS Grid from pushing it down to
      // the height of the much taller salary/settings card on the right.
      leftStack.appendChild(panel);
    } else if (danger) {
      grid.insertBefore(panel, danger);
    } else {
      grid.appendChild(panel);
    }

    $$('[data-open-location]', panel).forEach(button => {
      button.onclick = async () => {
        try {
          await api(
            'open_data_location',
            button.dataset.openLocation
          );
        } catch (error) {
          toast(error.message, 'error');
        }
      };
    });

    $$('[data-edit-location]', panel).forEach(button => {
      button.onclick = async () => {
        const key = button.dataset.editLocation;
        button.disabled = true;

        try {
          const result = await api('edit_data_location', key);
          if (result.cancelled) return;

          const pathLabel = panel.querySelector(`[data-location-path="${key}"]`);
          if (pathLabel && result.path) {
            pathLabel.textContent = result.path;
            pathLabel.title = result.path;
          }

          const root = openModal({
            kicker: tr('DATA LOCATION UPDATED'),
            title: tr('Restart JAM to apply the new path'),
            body: `
              <p class="muted">
                ${escapeHtml(tr('JAM copied the existing data to the selected folder. The current session keeps using the old path; restart JAM to switch safely to the new location.'))}
              </p>
              <div class="export-path">${escapeHtml(result.path || '')}</div>
            `,
            actions: `
              <button class="btn gold" data-location-update-close>
                ${escapeHtml(tr('Done'))}
              </button>
            `
          });

          $('[data-location-update-close]', root).onclick = closeModal;
        } catch (error) {
          toast(error.message, 'error');
        } finally {
          button.disabled = false;
        }
      };
    });
  }

  // ============================================================
  // DIAGNOSTICS
  // ============================================================

  function localizedDiagnosticDetail(check) {
    const detail = String(check.detail || '');

    if (currentLanguage() !== 'fr') {
      return detail;
    }

    const id = String(check.id || '');

    if (id === 'database') {
      if (detail.startsWith('Database is readable:')) {
        return detail.replace(
          'Database is readable:',
          'Base de données lisible :'
        );
      }

      if (detail.startsWith('Missing tables:')) {
        return detail.replace(
          'Missing tables:',
          'Tables manquantes :'
        );
      }
    }

    if (
      ['app_data', 'exports', 'backups', 'projects', 'logs', 'recovery'].includes(id)
    ) {
      if (detail.startsWith('Writable:')) {
        return detail.replace('Writable:', 'Accessible en écriture :');
      }

      if (detail.startsWith('Not writable:')) {
        return detail.replace('Not writable:', 'Non accessible en écriture :');
      }
    }

    if (id === 'flags') {
      return detail
        .replace('local flag asset(s) detected in', 'drapeau(x) local(aux) détecté(s) dans');
    }

    if (id === 'cv') {
      if (detail.startsWith('CV file is accessible:')) {
        return detail.replace('CV file is accessible:', 'Fichier CV accessible :');
      }

      return tr(detail);
    }

    if (id === 'webview2') {
      if (detail.startsWith('Detected version')) {
        return detail.replace('Detected version', 'Version détectée');
      }

      if (detail === 'Runtime detected in the Windows registry.') {
        return 'Runtime détecté dans le registre Windows.';
      }

      return tr(detail);
    }

    return tr(detail);
  }

  function diagnosticsStatusMeta(status) {
    if (status === 'ok') {
      return ['✓', 'diagnostic-ok'];
    }

    if (status === 'error') {
      return ['✕', 'diagnostic-error'];
    }

    if (status === 'warning') {
      return ['⚠', 'diagnostic-warning'];
    }

    return ['•', 'diagnostic-info'];
  }

  async function runDiagnostics() {
    let result;

    try {
      result = await api('run_diagnostics');
    } catch (error) {
      toast(error.message, 'error');
      return;
    }

    const diagnostics = result.diagnostics || {};
    const checks = diagnostics.checks || [];

    const root = openModal({
      kicker: tr('DIAGNOSTICS'),
      title: diagnostics.healthy
        ? tr('JAM looks healthy')
        : tr('JAM diagnostics found something to review'),
      wide: true,
      body: `
        <div class="diagnostic-summary ${diagnostics.healthy ? 'healthy' : 'attention'}">
          <strong>
            ${diagnostics.healthy ? '✓' : '⚠'}
            ${escapeHtml(
              diagnostics.healthy
                ? tr('Core checks passed')
                : tr('Review the checks below')
            )}
          </strong>

          <span>
            ${Number(diagnostics.error_count || 0)} ${escapeHtml(tr('errors'))}
            •
            ${Number(diagnostics.warning_count || 0)} ${escapeHtml(tr('warnings'))}
          </span>
        </div>

        <div class="diagnostic-list">
          ${checks.map(check => {
            const [symbol, cls] = diagnosticsStatusMeta(check.status);

            return `
              <div class="diagnostic-row ${cls}">
                <span class="diagnostic-symbol">${symbol}</span>
                <div>
                  <strong>${escapeHtml(tr(check.label))}</strong>
                  <span>${escapeHtml(localizedDiagnosticDetail(check))}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>

        <details class="package-details">
          <summary>${escapeHtml(tr('Installed package versions'))}</summary>
          <pre>${escapeHtml(
            Object.entries(diagnostics.packages || {})
              .map(([name, version]) => `${name}: ${version}`)
              .join('\n')
          )}</pre>
        </details>
      `,
      actions: `
        <button class="btn secondary" data-copy-diagnostics>
          ${escapeHtml(tr('Copy diagnostics'))}
        </button>

        <button class="btn gold" data-close-diagnostics>
          ${escapeHtml(tr('Done'))}
        </button>
      `
    });

    root.classList.add('diagnostics-modal');

    $('[data-close-diagnostics]', root).onclick = closeModal;

    $('[data-copy-diagnostics]', root).onclick = async () => {
      const text = checks.map(check =>
        `[${check.status.toUpperCase()}] ${check.label}: ${check.detail}`
      ).join('\n');

      await copyText(text);
      toast(tr('Diagnostics copied.'));
    };
  }

  function injectDiagnosticsButton() {
    const actions = $('#settingsPage .backup-actions');

    if (
      !actions ||
      $('#diagnosticsBtn')
    ) {
      return;
    }

    const button = document.createElement('button');
    button.id = 'diagnosticsBtn';
    button.type = 'button';
    button.className = 'btn secondary';
    button.textContent = tr('Run Diagnostics');
    button.onclick = runDiagnostics;
    actions.appendChild(button);
  }

  // ============================================================
  // LANGUAGE REFRESH HOOK
  // ============================================================

  function refreshBatch1Labels() {
    const archive = $('#archiveVisibilityBtn');
    if (archive) {
      archive.textContent = showArchived
        ? tr('Hide archived')
        : tr('Show archived');
    }

    const restore = $('#restoreBackupBtn');
    if (restore) restore.textContent = tr('Restore Backup');

    const diagnostics = $('#diagnosticsBtn');
    if (diagnostics) diagnostics.textContent = tr('Run Diagnostics');

    installOfflineCurrencyFlags();
    try {
      renderSettings();
    } catch (_) {}
  }

  function installLanguageRefreshHook() {
    if (!window.JAM_I18N?.setLanguage) {
      return;
    }

    const original = window.JAM_I18N.setLanguage.bind(window.JAM_I18N);

    window.JAM_I18N.setLanguage = async (...args) => {
      const result = await original(...args);
      refreshBatch1Labels();
      return result;
    };
  }

  // ============================================================
  // INIT
  // ============================================================

  async function init() {
    if (initialized) {
      return;
    }

    initialized = true;

    installLanguageSyncOnReload();
    installOfflineCurrencyFlags();
    installArchiveBehavior();
    installMainDraftAutosave();
    installDirtyProjectGuards();
    injectBackupRestoreButton();
    injectDiagnosticsButton();
    await injectDataLocations();
    installLanguageRefreshHook();

    setTimeout(
      async () => {
        await promptProjectRecovery();

        const projectState = await api('project_state').catch(() => null);

        if (!projectState?.project_state?.recovery) {
          await promptRecoveredMainDraft();
        }
      },
      350
    );
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
            !initialized &&
            window.pywebview?.api
          ) {
            init();
          }
        },
        250
      );
    }
  );
})();
