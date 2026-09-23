(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);

  const isFrench = () => window.JAM_I18N?.language === 'fr';
  const tx = (en, fr) => isFrench() ? fr : en;

  const escapeHtml = value => String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');

  const callApi = async (method, ...args) => {
    if (typeof window.api === 'function') {
      return window.api(method, ...args);
    }

    const fn = window.pywebview?.api?.[method];
    if (typeof fn !== 'function') {
      throw new Error(`JAM API method unavailable: ${method}`);
    }

    const result = await fn(...args);
    if (result?.ok === false) {
      throw new Error(result.error || 'JAM operation failed.');
    }
    return result;
  };

  const openJamModal = options => {
    if (typeof window.openModal !== 'function') {
      return null;
    }
    return window.openModal(options);
  };

  const closeJamModal = () => window.closeModal?.();

  const formatBytes = value => {
    const bytes = Number(value || 0);
    if (!Number.isFinite(bytes) || bytes <= 0) return '0 MB';
    const mb = bytes / (1024 * 1024);
    if (mb >= 1024) return `${(mb / 1024).toFixed(2)} GB`;
    return `${mb.toFixed(mb >= 100 ? 0 : 1)} MB`;
  };

  const noteItems = update => {
    const items = Array.isArray(update?.note_items) ? update.note_items : [];
    if (items.length) return items;

    return String(update?.notes || '')
      .split(/\r?\n/)
      .map(line => line.trim())
      .filter(Boolean)
      .filter(line => /^[-*•]\s+/.test(line))
      .map(line => line.replace(/^[-*•]\s+/, '').trim())
      .slice(0, 30);
  };

  function renderNotes(update) {
    const items = noteItems(update);
    if (items.length) {
      return `
        <div class="update-notes-list">
          ${items.map(item => `
            <div class="update-note-item">
              <span>✓</span>
              <div>${escapeHtml(item)}</div>
            </div>
          `).join('')}
        </div>
      `;
    }

    const notes = String(update?.notes || '').trim();
    if (!notes) {
      return `<p class="muted">${tx('No patch notes were provided for this release.', 'Aucune note de version n’a été fournie pour cette mise à jour.')}</p>`;
    }

    return `<p class="update-notes-plain">${escapeHtml(notes)}</p>`;
  }

  function showSimpleInfo(title, body, options = {}) {
    const root = openJamModal({
      kicker: options.kicker || 'JAM UPDATE',
      title,
      body,
      actions: `
        <button class="btn gold" data-update-ok>${tx('Got it', 'Compris')}</button>
      `
    });

    $('[data-update-ok]', root)?.addEventListener('click', closeJamModal);
    return root;
  }

  function showUpToDate(update) {
    return showSimpleInfo(
      tx('JAM is up to date', 'JAM est à jour'),
      `
        <div class="update-status-center">
          <div class="update-success-icon">✓</div>
          <p>${tx('You already have the latest public version.', 'Vous utilisez déjà la dernière version publique.')}</p>
          <div class="update-version-pill">v${escapeHtml(update?.current || update?.latest || '')}</div>
        </div>
      `
    );
  }

  function showCheckError(update) {
    const message = update?.message || tx('The update check failed.', 'La vérification de mise à jour a échoué.');
    return showSimpleInfo(
      tx('Could not check for updates', 'Impossible de vérifier les mises à jour'),
      `<p class="muted">${escapeHtml(message)}</p>`
    );
  }

  function showUpdateAvailable(update) {
    const installReady = Boolean(update?.install_ready);
    const root = openJamModal({
      kicker: 'JAM UPDATE',
      title: tx(
        `JAM ${update.latest} is available`,
        `JAM ${update.latest} est disponible`
      ),
      body: `
        <div class="update-release-meta">
          <div>
            <span>${tx('Current', 'Actuelle')}</span>
            <strong>v${escapeHtml(update.current)}</strong>
          </div>
          <div class="update-release-arrow">→</div>
          <div>
            <span>${tx('New', 'Nouvelle')}</span>
            <strong>v${escapeHtml(update.latest)}</strong>
          </div>
        </div>

        <div class="update-patch-card">
          <div class="eyebrow">${tx('WHAT CHANGED', 'NOUVEAUTÉS')}</div>
          ${renderNotes(update)}
        </div>

        ${!installReady ? `
          <div class="update-warning-box">
            ${tx(
              'This release is visible on GitHub, but automatic installation is not ready because the Setup EXE or SHA-256 proof is missing.',
              'Cette version est visible sur GitHub, mais l’installation automatique n’est pas prête car le Setup EXE ou la preuve SHA-256 est manquant.'
            )}
          </div>
        ` : ''}
      `,
      actions: `
        <button class="btn secondary" data-update-later>${tx('Later', 'Plus tard')}</button>
        ${update.release_url ? `<button class="btn secondary" data-update-release>${tx('View release', 'Voir la release')}</button>` : ''}
        ${installReady ? `<button class="btn gold" data-update-install>${tx('Download & install', 'Télécharger et installer')}</button>` : ''}
      `,
      wide: true
    });

    root?.classList.add('update-modal-root');

    $('[data-update-later]', root)?.addEventListener('click', closeJamModal);

    $('[data-update-release]', root)?.addEventListener('click', async () => {
      if (!update.release_url) return;
      try {
        await callApi('open_url', update.release_url);
      } catch (error) {
        window.toast?.(error.message, 'error');
      }
    });

    $('[data-update-install]', root)?.addEventListener('click', () => {
      beginDownload(update);
    });
  }

  function showProgressShell(version) {
    const root = openJamModal({
      kicker: 'JAM UPDATE',
      title: tx(`Updating to JAM ${version}`, `Mise à jour vers JAM ${version}`),
      body: `
        <div class="update-progress-shell">
          <div class="update-progress-logo">
            <img src="../assets/branding/jam_logo.png" alt="JAM">
          </div>

          <div class="update-progress-state" data-update-phase>
            ${tx('Preparing download…', 'Préparation du téléchargement…')}
          </div>

          <div class="update-progress-track" aria-hidden="true">
            <div class="update-progress-fill" data-update-progress-fill style="width:0%"></div>
          </div>

          <div class="update-progress-meta">
            <strong data-update-percent>0%</strong>
            <span data-update-bytes></span>
          </div>

          <div class="update-do-not-close">
            <strong>${tx('Keep JAM open during the download.', 'Gardez JAM ouvert pendant le téléchargement.')}</strong>
            <span data-update-warning>${tx('JAM will handle the installation and restart automatically.', 'JAM gérera l’installation et redémarrera automatiquement.')}</span>
          </div>
        </div>
      `
    });

    root?.classList.add('update-progress-root');
    $('[data-close-modal]', root)?.remove();
    $('[data-modal-backdrop]', root)?.removeAttribute('data-modal-backdrop');
    return root;
  }

  function updateProgressView(root, progress) {
    if (!root?.isConnected) return;

    const phase = String(progress?.phase || '');
    const percent = Math.max(0, Math.min(100, Number(progress?.percent || 0)));
    const fill = $('[data-update-progress-fill]', root);
    const percentNode = $('[data-update-percent]', root);
    const bytesNode = $('[data-update-bytes]', root);
    const phaseNode = $('[data-update-phase]', root);
    const warningNode = $('[data-update-warning]', root);

    if (phaseNode) {
      phaseNode.textContent = progress?.message || tx('Working…', 'Traitement…');
    }

    if (fill) {
      fill.style.width = `${percent}%`;
      fill.classList.toggle('indeterminate', phase === 'installing');
    }

    if (percentNode) {
      percentNode.textContent = phase === 'installing' ? tx('Installing', 'Installation') : `${Math.round(percent)}%`;
    }

    if (bytesNode) {
      const downloaded = Number(progress?.downloaded_bytes || 0);
      const total = Number(progress?.total_bytes || 0);
      bytesNode.textContent = total > 0
        ? `${formatBytes(downloaded)} / ${formatBytes(total)}`
        : (downloaded > 0 ? formatBytes(downloaded) : '');
    }

    if (warningNode && phase === 'installing') {
      warningNode.textContent = tx(
        'Do not close or reopen JAM manually. The installer will reopen the new version automatically.',
        'Ne fermez pas et ne relancez pas JAM manuellement. L’installateur rouvrira automatiquement la nouvelle version.'
      );
    }
  }

  async function beginDownload(update) {
    closeJamModal();
    const root = showProgressShell(update.latest);

    try {
      const start = await callApi('start_update_download');
      if (!start?.update?.ok) {
        closeJamModal();
        showCheckError(start?.update || {});
        return;
      }
    } catch (error) {
      closeJamModal();
      showSimpleInfo(
        tx('Update download failed', 'Échec du téléchargement'),
        `<p class="muted">${escapeHtml(error.message)}</p>`
      );
      return;
    }

    const poll = window.setInterval(async () => {
      try {
        const result = await callApi('get_update_progress');
        const progress = result?.progress || {};
        updateProgressView(root, progress);

        if (progress.phase === 'error') {
          window.clearInterval(poll);
          closeJamModal();
          showSimpleInfo(
            tx('Update failed', 'Échec de la mise à jour'),
            `<p class="muted">${escapeHtml(progress.message || progress.error || 'Unknown update error.')}</p>`
          );
          return;
        }

        if (progress.phase === 'ready') {
          window.clearInterval(poll);
          await beginInstall(root, progress);
        }
      } catch (error) {
        window.clearInterval(poll);
        closeJamModal();
        showSimpleInfo(
          tx('Update failed', 'Échec de la mise à jour'),
          `<p class="muted">${escapeHtml(error.message)}</p>`
        );
      }
    }, 300);
  }

  async function beginInstall(root, progress) {
    updateProgressView(root, {
      ...progress,
      phase: 'installing',
      percent: 100,
      message: tx('Starting the installer…', 'Démarrage de l’installateur…')
    });

    try {
      const result = await callApi('install_update');
      const update = result?.update || {};
      if (!update.ok) {
        closeJamModal();
        showSimpleInfo(
          tx('Installation cancelled', 'Installation annulée'),
          `<p class="muted">${escapeHtml(update.message || 'JAM could not start the installer.')}</p>`
        );
        return;
      }

      updateProgressView(root, {
        ...progress,
        phase: 'installing',
        percent: 100,
        message: tx('Installing update…', 'Installation de la mise à jour…')
      });
    } catch (error) {
      closeJamModal();
      showSimpleInfo(
        tx('Installation failed', 'Échec de l’installation'),
        `<p class="muted">${escapeHtml(error.message)}</p>`
      );
    }
  }

  function showCompletedUpdate(completed) {
    const items = Array.isArray(completed?.items) && completed.items.length
      ? completed.items
      : [tx('JAM was updated successfully.', 'JAM a été mis à jour avec succès.')];

    const root = openJamModal({
      kicker: 'JAM UPDATE',
      title: tx(
        `JAM ${completed.version} installed`,
        `JAM ${completed.version} installé`
      ),
      body: `
        <div class="update-complete-body">
          <div class="update-complete-icon">✓</div>
          <p>${tx('The new version is ready. Here is what was installed:', 'La nouvelle version est prête. Voici ce qui a été installé :')}</p>
          <div class="update-complete-list">
            ${items.map(item => `
              <div><span>✓</span><p>${escapeHtml(item)}</p></div>
            `).join('')}
          </div>
        </div>
      `,
      actions: `
        <button class="btn gold" data-update-complete-ok>${tx('Continue to JAM', 'Continuer vers JAM')}</button>
      `,
      wide: true
    });

    root?.classList.add('update-complete-root');

    $('[data-update-complete-ok]', root)?.addEventListener('click', async () => {
      try {
        await callApi('acknowledge_update_complete');
      } catch (_) {}
      closeJamModal();
    });
  }

  async function checkForUpdates(manual = false) {
    try {
      const result = await callApi('check_for_updates', Boolean(manual));
      const update = result?.update || {};

      if (!update.ok) {
        if (manual) showCheckError(update);
        return;
      }

      if (update.skipped && !manual) return;

      if (update.available) {
        showUpdateAvailable(update);
        return;
      }

      if (manual) showUpToDate(update);
    } catch (error) {
      if (manual) {
        showSimpleInfo(
          tx('Could not check for updates', 'Impossible de vérifier les mises à jour'),
          `<p class="muted">${escapeHtml(error.message)}</p>`
        );
      }
    }
  }

  function refreshUpdaterLabels() {
    const card = $('#jamUpdateSettingsCard');
    if (card) {
      $('[data-update-card-kicker]', card).textContent = 'JAM UPDATE';
      $('[data-update-card-title]', card).textContent = tx('Updates', 'Mises à jour');
      $('[data-update-card-copy]', card).textContent = tx(
        'JAM checks GitHub Releases automatically about once every 24 hours. You can also check manually at any time.',
        'JAM vérifie automatiquement les GitHub Releases environ une fois toutes les 24 heures. Vous pouvez aussi lancer une vérification manuelle à tout moment.'
      );
      $('[data-update-version-label]', card).textContent = tx('Installed version', 'Version installée');
      const button = $('#checkUpdatesBtn', card) || $('[data-check-updates]', card);
      if (button && !button.disabled) {
        button.textContent = tx('Check for Updates', 'Vérifier les mises à jour');
      }
    }
  }

  async function installSettingsCard() {
    let card = $('#jamUpdateSettingsCard');
    const grid = $('#settingsPage .settings-grid');
    if (!grid) return;

    if (!card) {
      card = document.createElement('article');
      card.id = 'jamUpdateSettingsCard';
      card.className = 'panel update-settings-panel';
      card.innerHTML = `
        <span class="eyebrow" data-update-card-kicker>JAM UPDATE</span>
        <h2 data-update-card-title>Updates</h2>
        <p class="muted" data-update-card-copy></p>
        <div class="update-settings-version">
          <span data-update-version-label>Installed version</span>
          <strong id="installedVersionText">…</strong>
        </div>
        <button id="checkUpdatesBtn" class="btn secondary" type="button">Check for Updates</button>
      `;

      const danger = $('.danger-panel', grid);
      if (danger) grid.insertBefore(card, danger);
      else grid.appendChild(card);
    }

    refreshUpdaterLabels();

    const button = $('#checkUpdatesBtn', card) || $('[data-check-updates]', card);
    if (button) {
      button.dataset.checkUpdates = '1';
    }
  }


  let settingsCheckRunning = false;

  async function runSettingsUpdateCheck(button) {
    if (!button || settingsCheckRunning) return;

    settingsCheckRunning = true;
    button.disabled = true;
    button.textContent = tx('Checking…', 'Vérification…');

    try {
      await checkForUpdates(true);
    } finally {
      settingsCheckRunning = false;
      button.disabled = false;
      refreshUpdaterLabels();
    }
  }

  function installSettingsUpdateClickHook() {
    if (document.documentElement.dataset.jamUpdaterSettingsHook === '1') return;
    document.documentElement.dataset.jamUpdaterSettingsHook = '1';

    // Capture phase makes the Settings button reliable even if another JAM
    // handler stops bubbling or the Settings card is recreated later.
    document.addEventListener('click', event => {
      const button = event.target?.closest?.('#checkUpdatesBtn, [data-check-updates]');
      if (!button || !button.closest('#jamUpdateSettingsCard')) return;

      event.preventDefault();
      event.stopPropagation();
      runSettingsUpdateCheck(button);
    }, true);
  }

  function injectAboutUpdateButton() {
    const root = $('#modalRoot');
    if (!root) return;

    const heading = root.querySelector('.modal-head h2')?.textContent || '';
    if (!heading.includes('JAM - Job Application Manager')) return;

    const actions = root.querySelector('.modal-actions');
    if (!actions || $('[data-about-update]', actions)) return;

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn secondary';
    button.dataset.aboutUpdate = '1';
    button.textContent = tx('Check for Updates', 'Vérifier les mises à jour');
    button.addEventListener('click', async () => {
      closeJamModal();
      await checkForUpdates(true);
    });
    actions.prepend(button);
  }

  function installAboutHook() {
    if (document.documentElement.dataset.jamUpdaterAboutHook === '1') return;
    document.documentElement.dataset.jamUpdaterAboutHook = '1';

    document.addEventListener('click', event => {
      const button = event.target?.closest?.('#aboutBtn');
      if (!button) return;
      window.setTimeout(injectAboutUpdateButton, 30);
    });

    const modalRoot = $('#modalRoot');
    if (modalRoot && typeof MutationObserver !== 'undefined') {
      const observer = new MutationObserver(() => injectAboutUpdateButton());
      observer.observe(modalRoot, { childList: true, subtree: true });
    }
  }

  async function showPostUpdateIfNeeded() {
    try {
      const result = await callApi('get_update_status');
      const completed = result?.updater?.completed_update;
      if (!completed) return false;
      showCompletedUpdate(completed);
      return true;
    } catch (_) {
      return false;
    }
  }

  async function autoCheckWhenTutorialIsDone() {
    // First-run tutorial owns the user's attention. Do not put an updater
    // window on top of it; wait until the guided tour is complete/stopped.
    if (document.body.classList.contains('jam-tutorial-active')) {
      window.setTimeout(autoCheckWhenTutorialIsDone, 1200);
      return;
    }

    const showedCompletion = await showPostUpdateIfNeeded();
    if (showedCompletion) return;

    await checkForUpdates(false);
  }

  let uiInitialized = false;
  let apiInitialized = false;
  let lastLanguage = null;

  function initializeUi() {
    if (!uiInitialized) {
      uiInitialized = true;
      installAboutHook();
      installSettingsUpdateClickHook();
      installSettingsCard();
      window.JAM_UPDATER = {
        check: () => checkForUpdates(true)
      };
    }

    const language = isFrench() ? 'fr' : 'en';
    if (language !== lastLanguage) {
      lastLanguage = language;
      refreshUpdaterLabels();
      injectAboutUpdateButton();
    }
  }

  async function initializeApi() {
    if (apiInitialized) return;

    const ready = typeof window.api === 'function' || Boolean(window.pywebview?.api);
    if (!ready) {
      window.setTimeout(initializeApi, 250);
      return;
    }

    apiInitialized = true;
    initializeUi();

    try {
      const status = await callApi('get_update_status');
      const version = status?.updater?.current_version || '';
      const node = $('#installedVersionText');
      if (node) node.textContent = version ? `v${version}` : '—';
    } catch (_) {
      const node = $('#installedVersionText');
      if (node) node.textContent = '—';
    }

    window.setTimeout(autoCheckWhenTutorialIsDone, 1800);
  }

  // The updater UI must exist even before the Python bridge is ready.
  // This prevents Settings/About controls from silently disappearing on
  // slower pywebview startup.
  initializeUi();
  initializeApi();

  window.addEventListener('pywebviewready', () => {
    initializeUi();
    initializeApi();
  });

  document.addEventListener('pywebviewready', () => {
    initializeUi();
    initializeApi();
  });

  window.addEventListener('DOMContentLoaded', () => {
    initializeUi();
    initializeApi();
  });

  // Keep EN/FR labels synchronized without depending on a specific i18n event.
  window.setInterval(() => {
    if (!document.hidden) initializeUi();
  }, 1000);
})();
