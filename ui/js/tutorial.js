(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const sleep = ms => new Promise(resolve => window.setTimeout(resolve, ms));

  let active = false;
  let stepIndex = 0;
  let root = null;
  let captureClickTarget = null;
  let captureClickHandler = null;
  let resizeTimer = null;

  const text = (en, fr) => (
    window.JAM_I18N?.language === 'fr' ? fr : en
  );

  const STEPS = [
    {
      id: 'capture',
      page: 'dashboard',
      target: '#captureBtn',
      title: ['Capture Mode', 'Mode Capture'],
      body: [
        'Start here. Click Capture Mode to open JAM’s lightweight pinned window. It stays above job boards while you apply, so you can save an opportunity without leaving the page.',
        'Commencez ici. Cliquez sur Mode Capture pour ouvrir la fenêtre légère et épinglée de JAM. Elle reste au-dessus des sites d’emploi pendant vos candidatures afin d’enregistrer une offre sans quitter la page.'
      ],
      requireCaptureClick: true
    },
    {
      id: 'dashboard',
      page: 'dashboard',
      target: '#dashboardPage .dashboard-grid',
      title: ['Dashboard', 'Tableau de bord'],
      body: [
        'Your command center. See your latest opportunities, quick stats, fast Capture access and the local CV Analyzer shortcut.',
        'Votre centre de commande. Retrouvez vos dernières opportunités, statistiques rapides, l’accès au Mode Capture et le raccourci vers l’Analyseur local.'
      ]
    },
    {
      id: 'top-actions',
      page: 'dashboard',
      target: '.topbar-actions',
      title: ['Project controls & notifications', 'Contrôles du projet et notifications'],
      body: [
        'Use the top bar for notifications, Support JAM, Excel import, opening or saving .jam project snapshots, and Capture Mode.',
        'Utilisez la barre supérieure pour les notifications, Support JAM, l’import Excel, l’ouverture ou l’enregistrement des projets .jam et le Mode Capture.'
      ]
    },
    {
      id: 'applications',
      page: 'applications',
      target: '#addJobBtn',
      title: ['Applications', 'Candidatures'],
      body: [
        'This is the main tracking table. Add jobs, search, filter, sort, edit, archive, bulk-update and export your opportunities from here.',
        'C’est le tableau principal de suivi. Ajoutez des offres, recherchez, filtrez, triez, modifiez, archivez, mettez à jour en masse et exportez vos opportunités ici.'
      ]
    },
    {
      id: 'pipeline',
      page: 'pipeline',
      target: '#pipelineBoard',
      title: ['Pipeline', 'Pipeline'],
      body: [
        'See your application flow by status, from Saved and To Review through Applied, Interviewing, Offer and final outcomes.',
        'Visualisez votre parcours de candidature par statut, de Enregistrée et À examiner jusqu’à Candidature envoyée, Entretien, Offre et résultat final.'
      ]
    },
    {
      id: 'analytics',
      page: 'analytics',
      target: '#analyticsTrendChart',
      title: ['Analytics', 'Statistiques'],
      body: [
        'Follow your application trend over time. Change the date range and review tracked applications, applications sent, scores, sources and status distribution.',
        'Suivez l’évolution de vos candidatures dans le temps. Modifiez la période et consultez les offres suivies, candidatures envoyées, scores, sources et statuts.'
      ]
    },
    {
      id: 'calendar',
      page: 'calendar',
      target: '#calendarGrid',
      title: ['Calendar', 'Calendrier'],
      body: [
        'Applications appear on their dates, and you can add interviews, follow-ups, deadlines and reminders linked to a tracked job.',
        'Les candidatures apparaissent à leurs dates et vous pouvez ajouter des entretiens, relances, échéances et rappels liés à une offre suivie.'
      ]
    },
    {
      id: 'analyzer',
      page: 'analyzer',
      target: '#runAnalyzerBtn',
      title: ['Analyzer', 'Analyseur'],
      body: [
        'Paste a job description and compare it with your selected CV. JAM performs the multilingual analysis locally and shows the evidence behind the score.',
        'Collez une description de poste et comparez-la à votre CV sélectionné. JAM effectue l’analyse multilingue localement et affiche les preuves derrière le score.'
      ]
    },
    {
      id: 'exports',
      page: 'exports',
      target: '#exportHistory',
      title: ['Exports', 'Exports'],
      body: [
        'Your generated Excel and PDF files are tracked here. Open a file, open its folder, or remove only the history entry.',
        'Vos fichiers Excel et PDF générés sont suivis ici. Ouvrez un fichier, son dossier ou retirez uniquement l’entrée de l’historique.'
      ]
    },
    {
      id: 'settings',
      page: 'settings',
      target: '#settingsPage .settings-grid',
      title: ['Settings', 'Paramètres'],
      body: [
        'Configure language, CV and salary targets, backups, data locations, Capture behavior, notifications, diagnostics and other JAM preferences.',
        'Configurez la langue, le CV et les objectifs salariaux, les sauvegardes, emplacements de données, le Mode Capture, les notifications, diagnostics et autres préférences JAM.'
      ]
    },
    {
      id: 'guide',
      page: 'guide',
      target: '#guideSearch',
      title: ['Guide & knowledge base', 'Guide et base de connaissances'],
      body: [
        'The Guide contains JAM’s searchable knowledge base. Search with live typo-tolerant results, browse A–Z, or open detailed tutorials and explanations.',
        'Le Guide contient la base de connaissances de JAM. Recherchez avec des résultats instantanés tolérant les fautes, parcourez A–Z ou ouvrez les tutoriels détaillés.'
      ]
    },
    {
      id: 'replay',
      page: 'guide',
      target: '#guideTutorialBtn',
      title: ['Replay this tutorial anytime', 'Rejouez ce tutoriel à tout moment'],
      body: [
        'Use this Play tutorial button whenever you want to run the full guided tour again. You can also stop the tour at any time without losing this option.',
        'Utilisez ce bouton Lire le tutoriel chaque fois que vous souhaitez relancer la visite guidée complète. Vous pouvez aussi arrêter le tutoriel à tout moment sans perdre cette option.'
      ],
      finish: true
    },
    {
      id: 'footer-links',
      page: 'guide',
      target: '.sidebar-links',
      title: ['More JAM tools', 'Autres outils JAM'],
      body: [
        'Recent Projects, Contact and About JAM live at the bottom of the sidebar. That is the full tour. You are ready to use JAM.',
        'Projets récents, Contact et À propos de JAM se trouvent en bas de la barre latérale. La visite est terminée. Vous êtes prêt à utiliser JAM.'
      ],
      finish: true
    }
  ];

  async function callApi(method, ...args) {
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
  }

  function buildRoot() {
    if (root?.isConnected) return root;

    root = document.createElement('div');
    root.id = 'jamTutorialRoot';
    root.className = 'jam-tutorial-root';
    root.hidden = true;
    root.innerHTML = `
      <div class="jam-tutorial-mask jam-tutorial-mask-top"></div>
      <div class="jam-tutorial-mask jam-tutorial-mask-bottom"></div>
      <div class="jam-tutorial-mask jam-tutorial-mask-left"></div>
      <div class="jam-tutorial-mask jam-tutorial-mask-right"></div>
      <div class="jam-tutorial-spotlight" aria-hidden="true"></div>
      <div class="jam-tutorial-arrow" aria-hidden="true">➜</div>
      <section class="jam-tutorial-card" role="dialog" aria-modal="true" aria-label="JAM guided tutorial">
        <div class="jam-tutorial-card-head">
          <span class="jam-tutorial-kicker">JAM GUIDED TOUR</span>
          <span class="jam-tutorial-progress"></span>
        </div>
        <h2 class="jam-tutorial-title"></h2>
        <p class="jam-tutorial-copy"></p>
        <div class="jam-tutorial-actions">
          <button type="button" class="btn secondary jam-tutorial-stop">Stop tutorial</button>
          <button type="button" class="btn gold jam-tutorial-next">Next →</button>
        </div>
      </section>
    `;

    document.body.appendChild(root);

    $('.jam-tutorial-stop', root).addEventListener('click', () => finishTutorial(false));
    $('.jam-tutorial-next', root).addEventListener('click', () => advance());

    return root;
  }

  function setMasks(rect) {
    const padding = 7;
    const width = window.innerWidth;
    const height = window.innerHeight;
    const left = Math.max(0, rect.left - padding);
    const top = Math.max(0, rect.top - padding);
    const right = Math.min(width, rect.right + padding);
    const bottom = Math.min(height, rect.bottom + padding);

    const topMask = $('.jam-tutorial-mask-top', root);
    const bottomMask = $('.jam-tutorial-mask-bottom', root);
    const leftMask = $('.jam-tutorial-mask-left', root);
    const rightMask = $('.jam-tutorial-mask-right', root);

    Object.assign(topMask.style, { left: '0px', top: '0px', width: `${width}px`, height: `${top}px` });
    Object.assign(bottomMask.style, { left: '0px', top: `${bottom}px`, width: `${width}px`, height: `${Math.max(0, height - bottom)}px` });
    Object.assign(leftMask.style, { left: '0px', top: `${top}px`, width: `${left}px`, height: `${Math.max(0, bottom - top)}px` });
    Object.assign(rightMask.style, { left: `${right}px`, top: `${top}px`, width: `${Math.max(0, width - right)}px`, height: `${Math.max(0, bottom - top)}px` });

    const spotlight = $('.jam-tutorial-spotlight', root);
    Object.assign(spotlight.style, {
      left: `${left}px`,
      top: `${top}px`,
      width: `${Math.max(1, right - left)}px`,
      height: `${Math.max(1, bottom - top)}px`
    });
  }

  function positionCard(target) {
    if (!root || !target) return;

    const rect = target.getBoundingClientRect();
    const card = $('.jam-tutorial-card', root);
    const arrow = $('.jam-tutorial-arrow', root);
    const margin = 22;

    card.style.left = '20px';
    card.style.top = '20px';
    card.style.visibility = 'hidden';
    card.style.maxWidth = `${Math.max(300, Math.min(410, window.innerWidth - 40))}px`;

    const cardWidth = card.offsetWidth || 390;
    const cardHeight = card.offsetHeight || 210;

    let placement = 'right';
    let x = rect.right + margin;
    let y = rect.top + (rect.height - cardHeight) / 2;

    if (x + cardWidth > window.innerWidth - 18) {
      placement = 'left';
      x = rect.left - cardWidth - margin;
    }

    if (x < 18) {
      placement = 'bottom';
      x = rect.left + (rect.width - cardWidth) / 2;
      y = rect.bottom + margin;
    }

    if (placement === 'bottom' && y + cardHeight > window.innerHeight - 18) {
      placement = 'top';
      y = rect.top - cardHeight - margin;
    }

    x = Math.max(18, Math.min(x, window.innerWidth - cardWidth - 18));
    y = Math.max(18, Math.min(y, window.innerHeight - cardHeight - 18));

    card.style.left = `${Math.round(x)}px`;
    card.style.top = `${Math.round(y)}px`;
    card.style.visibility = 'visible';

    let ax = rect.left + rect.width / 2;
    let ay = rect.top + rect.height / 2;
    let rotation = 0;

    if (placement === 'right') {
      ax = rect.right + 5;
      ay = rect.top + rect.height / 2 - 14;
      rotation = 0;
    } else if (placement === 'left') {
      ax = rect.left - 37;
      ay = rect.top + rect.height / 2 - 14;
      rotation = 180;
    } else if (placement === 'bottom') {
      ax = rect.left + rect.width / 2 - 14;
      ay = rect.bottom + 5;
      rotation = 90;
    } else {
      ax = rect.left + rect.width / 2 - 14;
      ay = rect.top - 37;
      rotation = -90;
    }

    arrow.style.left = `${Math.round(ax)}px`;
    arrow.style.top = `${Math.round(ay)}px`;
    arrow.style.transform = `rotate(${rotation}deg)`;
  }

  function currentTarget(step) {
    return step?.target ? document.querySelector(step.target) : null;
  }

  function resetChromeScroll() {
    const workspace = document.querySelector('.workspace');
    if (workspace) {
      workspace.scrollTop = 0;
      workspace.scrollLeft = 0;
    }

    const sidebar = document.querySelector('.sidebar');
    if (sidebar) {
      sidebar.scrollTop = 0;
      sidebar.scrollLeft = 0;
    }
  }

  function scrollTargetInsidePage(target) {
    if (!target) return;

    // Never use scrollIntoView here. It can programmatically scroll JAM's
    // overflow-hidden workspace and leave the top bar clipped after the tour.
    const page = target.closest('.page');
    if (!page || !page.classList.contains('active')) return;

    const pageRect = page.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    const currentTop = page.scrollTop || 0;
    const desiredTop = currentTop
      + (targetRect.top - pageRect.top)
      - Math.max(0, (page.clientHeight - targetRect.height) / 2);

    const maxTop = Math.max(0, page.scrollHeight - page.clientHeight);
    const top = Math.min(maxTop, Math.max(0, desiredTop));

    if (Math.abs(top - currentTop) < 2) return;

    try {
      page.scrollTo({ top, behavior: 'smooth' });
    } catch (_) {
      page.scrollTop = top;
    }
  }

  async function prepareStep(step) {
    resetChromeScroll();

    if (step.page && typeof window.navigate === 'function') {
      window.navigate(step.page);
    }

    await sleep(80);
    resetChromeScroll();

    const target = currentTarget(step);
    if (target) {
      scrollTargetInsidePage(target);
      await sleep(260);
      resetChromeScroll();
    }

    return currentTarget(step);
  }

  function clearCaptureClickBinding() {
    if (captureClickTarget && captureClickHandler) {
      captureClickTarget.removeEventListener('click', captureClickHandler, true);
    }
    captureClickTarget = null;
    captureClickHandler = null;
  }

  function bindCaptureClick(target) {
    clearCaptureClickBinding();
    if (!target) return;

    captureClickTarget = target;
    captureClickHandler = event => {
      if (!active || stepIndex !== 0) return;
      event.preventDefault();
      event.stopPropagation();
      event.stopImmediatePropagation();
      clearCaptureClickBinding();
      launchTutorialCapture();
    };

    target.addEventListener('click', captureClickHandler, true);
  }

  async function renderStep() {
    if (!active) return;

    const step = STEPS[stepIndex];
    if (!step) {
      await finishTutorial(true);
      return;
    }

    buildRoot();
    root.hidden = false;
    document.body.classList.add('jam-tutorial-active');

    clearCaptureClickBinding();

    const target = await prepareStep(step);
    if (!active) return;

    const titleNode = $('.jam-tutorial-title', root);
    const copyNode = $('.jam-tutorial-copy', root);
    const progressNode = $('.jam-tutorial-progress', root);
    const kickerNode = $('.jam-tutorial-kicker', root);
    const stopButton = $('.jam-tutorial-stop', root);
    const nextButton = $('.jam-tutorial-next', root);
    const card = $('.jam-tutorial-card', root);

    kickerNode.textContent = text('JAM GUIDED TOUR', 'TUTORIEL GUIDÉ JAM');
    titleNode.textContent = text(step.title[0], step.title[1]);
    copyNode.textContent = text(step.body[0], step.body[1]);
    progressNode.textContent = `${stepIndex + 1} / ${STEPS.length}`;
    stopButton.textContent = text('Stop tutorial', 'Arrêter le tutoriel');

    if (step.requireCaptureClick) {
      nextButton.hidden = true;
      bindCaptureClick(target);
    } else {
      nextButton.hidden = false;
      nextButton.textContent = stepIndex === STEPS.length - 1
        ? text('Finish ✓', 'Terminer ✓')
        : text('Next →', 'Suivant →');
    }

    card.classList.remove('jam-tutorial-card-enter');
    void card.offsetWidth;
    card.classList.add('jam-tutorial-card-enter');

    if (target) {
      const rect = target.getBoundingClientRect();
      setMasks(rect);
      positionCard(target);
    } else {
      setMasks({ left: window.innerWidth / 2 - 1, right: window.innerWidth / 2 + 1, top: window.innerHeight / 2 - 1, bottom: window.innerHeight / 2 + 1 });
      card.style.left = '50%';
      card.style.top = '50%';
      card.style.transform = 'translate(-50%, -50%)';
      $('.jam-tutorial-arrow', root).style.display = 'none';
    }

    if (target) {
      card.style.transform = '';
      $('.jam-tutorial-arrow', root).style.display = '';
    }
  }

  async function launchTutorialCapture() {
    if (!active) return;

    root.hidden = true;
    document.body.classList.remove('jam-tutorial-active');

    try {
      await callApi('open_capture_window', 'top-right', true);

      // Wait until Capture has been closed with Return to JAM.
      for (;;) {
        await sleep(650);
        const status = await callApi('capture_window_status');
        if (!status?.open) break;
      }

      await sleep(650);
      if (!active) return;
      stepIndex = 1;
      await renderStep();
    } catch (error) {
      console.error('JAM tutorial Capture step failed.', error);
      root.hidden = false;
      document.body.classList.add('jam-tutorial-active');
      if (typeof window.toast === 'function') {
        window.toast(error.message || 'Could not open Capture Mode.', 'error');
      }
      bindCaptureClick(currentTarget(STEPS[0]));
    }
  }

  async function advance() {
    if (!active) return;
    if (stepIndex >= STEPS.length - 1) {
      await finishTutorial(true);
      return;
    }
    stepIndex += 1;
    await renderStep();
  }

  function cleanup() {
    clearCaptureClickBinding();
    active = false;
    document.body.classList.remove('jam-tutorial-active');
    if (root) root.hidden = true;
    resetChromeScroll();
  }

  async function persistCompleted() {
    try {
      await callApi('save_setting', 'tutorial_completed', '1');
    } catch (error) {
      console.error('Could not save JAM tutorial completion state.', error);
    }
  }

  function showCompletionModal(completed) {
    const isFrench = window.JAM_I18N?.language === 'fr';
    const title = completed
      ? (isFrench ? 'Tutoriel terminé' : 'Tutorial complete')
      : (isFrench ? 'Tutoriel arrêté' : 'Tutorial stopped');

    const body = completed
      ? (isFrench
        ? '😊 Je suis content que vous essayiez mon tutoriel. Vous pouvez rejouer cette visite guidée à tout moment depuis la section Guide dans le menu de gauche, avec le bouton ▶ Lire le tutoriel.'
        : '😊 I’m happy you’re trying out my tutorial. You can replay this guided tour anytime from the Guide section in the left menu using the ▶ Play tutorial button.')
      : (isFrench
        ? 'Vous pouvez rejouer cette visite guidée à tout moment depuis la section Guide dans le menu de gauche, avec le bouton ▶ Lire le tutoriel.'
        : 'You can replay this guided tour anytime from the Guide section in the left menu using the ▶ Play tutorial button.');

    if (typeof window.openModal === 'function') {
      const modal = window.openModal({
        kicker: isFrench ? 'TUTORIEL JAM' : 'JAM TUTORIAL',
        title,
        body: `
          <div class="tutorial-finish-body">
            <div class="tutorial-finish-check">${completed ? '✓' : '↻'}</div>
            <p class="muted">${body}</p>
          </div>
        `,
        actions: `
          <button class="btn gold" data-tutorial-done>
            ${isFrench ? 'Compris' : 'Got it'}
          </button>
        `
      });

      $('[data-tutorial-done]', modal)?.addEventListener('click', () => {
        window.closeModal?.();
        window.maybeShowOnboarding?.();
      });
      return;
    }

    window.alert(`${title}\n\n${body}`);
    window.maybeShowOnboarding?.();
  }

  async function finishTutorial(completed) {
    if (!active) return;
    cleanup();
    await persistCompleted();
    showCompletionModal(completed);
  }

  function start(options = {}) {
    if (active) return false;

    // Close ordinary overlays/modals before the guided tour begins.
    try { window.closeModal?.(); } catch (_) {}
    try { window.closeAnalysisOverlay?.(); } catch (_) {}

    active = true;
    stepIndex = 0;

    if (typeof window.navigate === 'function') {
      window.navigate('dashboard');
    }
    resetChromeScroll();

    window.setTimeout(() => renderStep(), options.auto ? 500 : 180);
    return true;
  }

  function autoStart(settings = {}) {
    const completed = String(settings.tutorial_completed || '').trim().toLowerCase();
    if (['1', 'true', 'yes', 'on'].includes(completed)) {
      return false;
    }
    return start({ auto: true });
  }

  function bindGuideReplay() {
    const button = $('#guideTutorialBtn');
    if (!button || button.dataset.tutorialBound === '1') return;
    button.dataset.tutorialBound = '1';
    button.addEventListener('click', () => start({ replay: true }));
  }

  function refreshPlacement() {
    if (!active || root?.hidden) return;
    window.clearTimeout(resizeTimer);
    resizeTimer = window.setTimeout(() => {
      const step = STEPS[stepIndex];
      const target = currentTarget(step);
      if (!target) return;
      setMasks(target.getBoundingClientRect());
      positionCard(target);
    }, 80);
  }

  window.addEventListener('resize', refreshPlacement);
  window.addEventListener('scroll', refreshPlacement, true);

  bindGuideReplay();

  window.JAM_TUTORIAL = {
    start,
    autoStart,
    isActive: () => active,
    stop: () => finishTutorial(false)
  };
})();
