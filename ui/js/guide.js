(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

  const PAGE_SIZE = 10;
  let currentPage = 1;
  let currentQuery = '';
  let currentArticleId = null;

  const tx = (en, fr) => ({ en, fr: fr || en });
  const lang = () => window.JAM_I18N?.language === 'fr' ? 'fr' : 'en';
  const categoryLabel = value => {
    if (lang() !== 'fr') return value;
    return ({
      About: 'À propos',
      Analyzer: 'Analyseur',
      Applications: 'Candidatures',
      Capture: 'Capture',
      Exports: 'Exports',
      FAQ: 'FAQ',
      Files: 'Fichiers',
      Guide: 'Guide',
      Imports: 'Imports',
      Pipeline: 'Pipeline',
      Privacy: 'Confidentialité',
      Safety: 'Sécurité',
      Settings: 'Paramètres',
      Shortcuts: 'Raccourcis',
      Support: 'Support',
      Tracking: 'Suivi',
      Tutorial: 'Tutoriel'
    })[value] || value;
  };
  const local = value => {
    if (value && typeof value === 'object' && ('en' in value || 'fr' in value)) {
      return value[lang()] || value.en || value.fr || '';
    }
    return String(value ?? '');
  };

  const article = (id, titleEn, titleFr, summaryEn, summaryFr, keywords, blocks, category = 'Guide') => ({
    id,
    title: tx(titleEn, titleFr),
    summary: tx(summaryEn, summaryFr),
    keywords,
    blocks,
    category
  });

  const p = (en, fr) => ({ type: 'p', text: tx(en, fr) });
  const note = (en, fr) => ({ type: 'note', text: tx(en, fr) });
  const bullets = (titleEn, titleFr, items) => ({ type: 'bullets', title: tx(titleEn, titleFr), items });
  const steps = (titleEn, titleFr, items) => ({ type: 'steps', title: tx(titleEn, titleFr), items });
  const table = (titleEn, titleFr, headers, rows) => ({ type: 'table', title: tx(titleEn, titleFr), headers, rows });
  const timeline = (titleEn, titleFr, items) => ({ type: 'timeline', title: tx(titleEn, titleFr), items });
  const bars = (titleEn, titleFr, items) => ({ type: 'bars', title: tx(titleEn, titleFr), items });

  const KB = [
    article('about-jam', 'About JAM', 'À propos de JAM',
      'What JAM is, who made it, and what the app is designed to do.',
      'Ce qu’est JAM, qui l’a créé et à quoi sert l’application.',
      ['about', 'developer', 'farouk', 'job application manager', 'windows', 'offline', 'local'], [
        p('JAM means Job Application Manager. It is a Windows desktop app built by Farouk to track job opportunities, applications, analysis, files, contacts, notes and exports in one local workspace.',
          'JAM signifie Job Application Manager. C’est une application Windows créée par Farouk pour centraliser les offres, candidatures, analyses, fichiers, contacts, notes et exports dans un espace local.'),
        bullets('Core principles', 'Principes clés', [
          tx('Local-first and privacy-focused.', 'Local-first et axé sur la confidentialité.'),
          tx('Dark premium JAM interface with gold accents.', 'Interface JAM sombre et premium avec accents dorés.'),
          tx('JAM and CV Maker (CVM) are separate applications.', 'JAM et CV Maker (CVM) restent deux applications séparées.'),
          tx('Native JAM project format: .jam.', 'Format de projet natif JAM : .jam.')
        ]),
        note('Developer: Farouk. Use Contact from the left sidebar for official links and feedback options.',
          'Développeur : Farouk. Utilisez Contact dans la barre latérale pour les liens officiels et les retours.')
      ], 'About'),

    article('add-job', 'Add a Job', 'Ajouter une offre',
      'Create a new application manually from the Applications page or Dashboard.',
      'Créer manuellement une nouvelle candidature depuis Applications ou le Tableau de bord.',
      ['add job', 'new opportunity', 'application', 'company', 'job title', 'manual'], [
        steps('Add an application', 'Ajouter une candidature', [
          tx('Open Applications and click + Add Job.', 'Ouvrez Candidatures et cliquez sur + Ajouter une offre.'),
          tx('Fill the company, title and any useful details such as link, salary, source, status, location and description.', 'Renseignez l’entreprise, le poste et les informations utiles : lien, salaire, source, statut, localisation et description.'),
          tx('Optionally click Analyze to compare the role with the selected CV.', 'Cliquez éventuellement sur Analyser pour comparer l’offre au CV sélectionné.'),
          tx('Click Save application.', 'Cliquez sur Enregistrer la candidature.')
        ]),
        note('JAM requires at least a company or a job title before saving.', 'JAM exige au moins une entreprise ou un intitulé de poste avant l’enregistrement.')
      ], 'Applications'),

    article('analyzer', 'Analyzer', 'Analyseur',
      'How JAM compares a job description with your selected CV locally.',
      'Comment JAM compare localement une offre avec votre CV sélectionné.',
      ['analyzer', 'analysis', 'cv match', 'score', 'semantic', 'multilingual', 'ai', 'local'], [
        p('The Analyzer combines deterministic checks with local multilingual semantic matching. It reads the job description, extracts requirements and looks for evidence in the selected CV.',
          'L’Analyseur combine des vérifications déterministes avec une correspondance sémantique multilingue locale. Il lit l’offre, extrait les exigences et recherche des preuves dans le CV sélectionné.'),
        bullets('What it checks', 'Ce qu’il vérifie', [
          tx('Role and job-family alignment.', 'Alignement du rôle et de la famille de métiers.'),
          tx('Skills, tools and requirements.', 'Compétences, outils et exigences.'),
          tx('Experience and responsibilities.', 'Expérience et responsabilités.'),
          tx('Education and languages.', 'Formation et langues.'),
          tx('Multilingual CV evidence, including French ↔ English matching.', 'Preuves multilingues dans le CV, notamment français ↔ anglais.')
        ]),
        note('The Analyzer is evidence-based and can make mistakes. Always review the detailed evidence instead of treating the percentage as an absolute truth.',
          'L’Analyseur est fondé sur des preuves et peut se tromper. Vérifiez toujours les détails au lieu de considérer le pourcentage comme une vérité absolue.')
      ], 'Analyzer'),

    article('analyzer-first-run', 'Analyzer: First Run and Speed', 'Analyseur : premier lancement et vitesse',
      'Why the first analysis can take longer and what normal behavior looks like.',
      'Pourquoi la première analyse peut être plus longue et quel comportement est normal.',
      ['analyzer slow', 'loading weights', 'huggingface', 'model', 'speed', 'first analysis', 'sentence transformer'], [
        p('JAM uses a local multilingual sentence model. The first use may require model setup/download and can take longer. After that, the model is cached locally.',
          'JAM utilise un modèle de phrases multilingue local. La première utilisation peut nécessiter une installation ou un téléchargement du modèle et prendre plus de temps. Ensuite, le modèle est mis en cache localement.'),
        bullets('Normal behavior', 'Comportement normal', [
          tx('JAM and Capture Mode should open without loading the heavy Analyzer model.', 'JAM et le Mode Capture doivent s’ouvrir sans charger le modèle lourd de l’Analyseur.'),
          tx('The model loads only when Analyze is requested.', 'Le modèle se charge uniquement lorsqu’une analyse est demandée.'),
          tx('Later analyses in the same process are usually faster.', 'Les analyses suivantes dans le même processus sont généralement plus rapides.')
        ])
      ], 'Analyzer'),

    article('analyzer-evidence', 'Analyzer Evidence and Score', 'Preuves et score de l’Analyseur',
      'Understand matched requirements, missing evidence, score breakdown and hard role checks.',
      'Comprendre les exigences trouvées, les manques, le détail du score et les vérifications de rôle.',
      ['evidence', 'score breakdown', 'matched', 'missing', 'strong', 'partial', 'weak', 'requirement coverage'], [
        p('JAM does not score only by keyword overlap. It tries to match each requirement with concrete CV evidence while preserving strict role/domain checks.',
          'JAM ne calcule pas le score uniquement avec des mots-clés. Il tente d’associer chaque exigence à une preuve concrète dans le CV tout en conservant des contrôles stricts de rôle et de domaine.'),
        table('Evidence labels', 'Niveaux de preuve',
          [tx('Label', 'Niveau'), tx('Meaning', 'Signification')], [
            [tx('Strong', 'Fort'), tx('Clear and relevant CV evidence.', 'Preuve CV claire et pertinente.')],
            [tx('Partial', 'Partiel'), tx('Some evidence exists but does not fully cover the requirement.', 'Une preuve existe mais ne couvre pas entièrement l’exigence.')],
            [tx('Weak', 'Faible'), tx('Related evidence exists but confidence is limited.', 'Une preuve liée existe mais la confiance reste limitée.')],
            [tx('Missing', 'Absent'), tx('No reliable evidence was found.', 'Aucune preuve fiable n’a été trouvée.')]
          ]),
        note('A high semantic similarity cannot override a serious profession/domain mismatch.', 'Une forte similarité sémantique ne peut pas annuler une incompatibilité importante de métier ou de domaine.')
      ], 'Analyzer'),

    article('analyzer-history', 'Analyzer History', 'Historique de l’Analyseur',
      'Save and reopen useful Analyzer results.',
      'Enregistrer et rouvrir les résultats utiles de l’Analyseur.',
      ['analysis history', 'save analysis', 'saved analysis'], [
        p('From the main Analyzer page, a completed result can be saved to Analyzer History. Saved entries keep the job title, description and analysis result so you can reopen them later.',
          'Depuis la page principale de l’Analyseur, un résultat terminé peut être enregistré dans l’historique. Les entrées conservent le poste, la description et le résultat pour pouvoir les rouvrir plus tard.')
      ], 'Analyzer'),

    article('analyzer-pdf', 'Analyzer PDF Report', 'Rapport PDF de l’Analyseur',
      'Export a detailed analysis report with evidence and the original job description.',
      'Exporter un rapport détaillé avec les preuves et la description originale de l’offre.',
      ['analyzer pdf', 'report', 'export analysis', 'pdf'], [
        bullets('The report includes', 'Le rapport contient', [
          tx('JAM branding and job title.', 'Identité JAM et intitulé du poste.'),
          tx('Full job description and detected reference when available.', 'Description complète de l’offre et référence détectée si disponible.'),
          tx('Overall score and score breakdown.', 'Score global et détail du score.'),
          tx('Experience, education, salary, languages and requirement evidence.', 'Expérience, formation, salaire, langues et preuves des exigences.'),
          tx('A disclaimer reminding you to verify the result.', 'Un avertissement rappelant de vérifier le résultat.')
        ])
      ], 'Analyzer'),

    article('applications', 'Applications Page', 'Page Candidatures',
      'The main table used to manage every tracked opportunity.',
      'Le tableau principal pour gérer toutes les opportunités suivies.',
      ['applications', 'table', 'jobs', 'tracking', 'rows'], [
        p('Applications is JAM’s main management table. It supports search, sorting, column filters, quick filters, saved views, row selection, bulk actions, edit, delete, archive and export workflows.',
          'Candidatures est le tableau principal de gestion de JAM. Il prend en charge la recherche, le tri, les filtres de colonnes, les filtres rapides, les vues enregistrées, la sélection, les actions groupées, la modification, la suppression, l’archivage et les exports.'),
        note('Double-clicking or editing a selected application opens the full Add/Edit Job view.', 'Un double-clic ou la modification d’une candidature sélectionnée ouvre la vue complète Ajouter/Modifier.')
      ], 'Applications'),

    article('archive', 'Archive Applications', 'Archiver des candidatures',
      'Hide closed opportunities without deleting them.',
      'Masquer les opportunités closes sans les supprimer.',
      ['archive', 'archived', 'hide archived', 'show archived'], [
        p('Archived applications stay in JAM but are hidden by default. Use the archived visibility control when you need to search or review them.',
          'Les candidatures archivées restent dans JAM mais sont masquées par défaut. Utilisez le contrôle d’affichage des archives pour les rechercher ou les consulter.')
      ], 'Applications'),

    article('attachments', 'Attachments', 'Pièces jointes',
      'Store CVs, cover letters, screenshots and other files with an application.',
      'Associer des CV, lettres de motivation, captures et autres fichiers à une candidature.',
      ['attachments', 'cv', 'cover letter', 'screenshot', 'file', 'open folder'], [
        bullets('Attachment categories', 'Catégories de pièces jointes', [
          tx('CV', 'CV'), tx('Cover Letter', 'Lettre de motivation'), tx('Screenshot', 'Capture d’écran'), tx('Other', 'Autre')
        ]),
        p('Files are copied into JAM’s local attachment storage. You can open the file, open its folder or remove the attachment record from the application.',
          'Les fichiers sont copiés dans le stockage local des pièces jointes de JAM. Vous pouvez ouvrir le fichier, ouvrir son dossier ou supprimer la pièce jointe de la candidature.'),
        note('A .jam project stores attachment metadata, not the full attachment bytes. Physical files remain in JAM’s local attachment storage.',
          'Un projet .jam stocke les métadonnées des pièces jointes, pas les octets complets. Les fichiers physiques restent dans le stockage local de JAM.')
      ], 'Tracking'),

    article('autosave-recovery', 'Autosave and Recovery', 'Sauvegarde automatique et récupération',
      'How JAM protects drafts and recovers from interrupted sessions.',
      'Comment JAM protège les brouillons et récupère après une interruption.',
      ['autosave', 'recovery', 'crash', 'draft', 'unsaved'], [
        p('JAM includes recovery protection for important unsaved work, including Add Job drafts, Capture drafts and project recovery snapshots.',
          'JAM inclut une protection de récupération pour les travaux non enregistrés importants, notamment les brouillons Ajouter une offre, Capture et les instantanés de récupération de projet.'),
        note('When JAM detects a recoverable draft, it can offer to restore or discard it.', 'Lorsque JAM détecte un brouillon récupérable, il peut proposer de le restaurer ou de le supprimer.')
      ], 'Safety'),

    article('backups', 'Backups', 'Sauvegardes',
      'Create a safety copy of JAM’s local database and restore it when needed.',
      'Créer une copie de sécurité de la base locale JAM et la restaurer si nécessaire.',
      ['backup', 'restore backup', 'database', 'safety'], [
        p('Use Settings → Data Safety to create backups, open the backup folder and restore data. JAM creates a safety backup before a restore operation.',
          'Utilisez Paramètres → Sécurité des données pour créer des sauvegardes, ouvrir leur dossier et restaurer les données. JAM crée une sauvegarde de sécurité avant une restauration.'),
        note('A database backup is different from a portable .jam project snapshot.', 'Une sauvegarde de base de données est différente d’un instantané de projet .jam portable.')
      ], 'Safety'),

    article('bulk-actions', 'Bulk Actions', 'Actions groupées',
      'Apply changes to several selected applications at once.',
      'Appliquer des modifications à plusieurs candidatures sélectionnées en une fois.',
      ['bulk actions', 'multi select', 'selected jobs', 'status', 'rating', 'source'], [
        p('Select multiple rows in Applications to access supported bulk actions such as changing common fields or deleting selected applications.',
          'Sélectionnez plusieurs lignes dans Candidatures pour accéder aux actions groupées prises en charge, comme modifier certains champs communs ou supprimer la sélection.')
      ], 'Applications'),

    article('capture-mode', 'Capture Mode', 'Mode Capture',
      'A lightweight pinned window for saving jobs while browsing job boards.',
      'Une fenêtre légère et épinglée pour enregistrer des offres pendant la navigation.',
      ['capture', 'pinned', 'top right', 'top left', 'quick capture', 'linkedin'], [
        p('Capture Mode is a separate lightweight window designed to stay out of the way while you browse LinkedIn, Indeed or other job boards. The main JAM window hides/minimizes while Capture is open and returns when Capture closes.',
          'Le Mode Capture est une fenêtre légère séparée conçue pour rester discrète pendant votre navigation sur LinkedIn, Indeed ou d’autres sites d’emploi. La fenêtre principale JAM se masque ou se réduit pendant Capture et revient à sa fermeture.'),
        bullets('Capture can remember', 'Capture peut mémoriser', [
          tx('Default corner.', 'Coin par défaut.'),
          tx('Exact position and size when enabled.', 'Position et taille exactes si l’option est activée.'),
          tx('A recoverable draft if the session is interrupted.', 'Un brouillon récupérable si la session est interrompue.')
        ]),
        note('The heavy Analyzer model is not loaded just to open Capture. It loads only when Analyze is clicked.', 'Le modèle lourd de l’Analyseur n’est pas chargé à l’ouverture de Capture. Il se charge uniquement lorsque vous cliquez sur Analyser.')
      ], 'Capture'),

    article('contacts', 'Contacts', 'Contacts',
      'Keep one or more recruiters, hiring managers or other contacts per application.',
      'Conserver un ou plusieurs recruteurs, managers ou autres contacts par candidature.',
      ['contacts', 'recruiter', 'email', 'phone', 'contact link', 'multiple contacts'], [
        p('Each saved application can hold multiple contacts with name, role, email, phone, link and note fields.',
          'Chaque candidature enregistrée peut contenir plusieurs contacts avec nom, rôle, e-mail, téléphone, lien et note.'),
        note('The main Contact Name and Contact Link fields remain visible in Add/Edit Job, while richer contact history is available in Tracking & History.', 'Les champs principaux Nom du contact et Lien du contact restent visibles dans Ajouter/Modifier, tandis que l’historique enrichi est disponible dans Suivi et historique.')
      ], 'Tracking'),

    article('currency', 'Currencies and Salary Converter', 'Devises et convertisseur de salaire',
      'Salary currencies, target salary settings and quick gross/net conversion.',
      'Devises salariales, objectifs de salaire et conversion rapide brut/net.',
      ['currency', 'eur', 'usd', 'tnd', 'salary converter', 'gross', 'net', 'monthly', 'annual'], [
        p('JAM supports structured salary information and a salary target in Settings. Common currencies include EUR, USD and TND, with additional currencies available in the picker.',
          'JAM prend en charge un salaire structuré et un objectif salarial dans Paramètres. Les devises courantes incluent EUR, USD et TND, avec d’autres devises disponibles.'),
        table('Quick converter fields', 'Champs du convertisseur', [tx('Field', 'Champ'), tx('Example use', 'Utilisation')], [
          [tx('Monthly net', 'Net mensuel'), tx('Take-home monthly estimate.', 'Estimation mensuelle nette.')],
          [tx('Monthly gross', 'Brut mensuel'), tx('Monthly gross estimate.', 'Estimation mensuelle brute.')],
          [tx('Annual net', 'Net annuel'), tx('Annual net estimate.', 'Estimation annuelle nette.')],
          [tx('Annual gross', 'Brut annuel'), tx('Annual gross target/comparison.', 'Objectif/comparaison annuelle brute.')]
        ]),
        note('The quick converter currently estimates net at about 78% of gross. Real values vary by country, taxes, contract and deductions.', 'Le convertisseur rapide estime actuellement le net à environ 78 % du brut. Les valeurs réelles varient selon le pays, les impôts, le contrat et les cotisations.')
      ], 'Settings'),

    article('cv-files', 'CV Files and Selection', 'Fichiers CV et sélection',
      'Select the CV used by the Analyzer and understand supported formats.',
      'Sélectionner le CV utilisé par l’Analyseur et connaître les formats pris en charge.',
      ['cv file', 'choose cv', 'pdf', 'docx', 'txt', 'md', 'cvm', 'preview cv'], [
        p('Choose the CV from the Analyzer or Settings. JAM extracts readable text locally and uses that evidence for analysis.', 'Choisissez le CV depuis l’Analyseur ou Paramètres. JAM extrait le texte lisible localement et utilise ces preuves pour l’analyse.'),
        table('Supported Analyzer CV formats', 'Formats CV pris en charge', [tx('Format', 'Format'), tx('Notes', 'Notes')], [
          ['PDF', tx('Best when text is selectable.', 'Idéal lorsque le texte est sélectionnable.')],
          ['DOCX', tx('Paragraphs and tables can be read.', 'Les paragraphes et tableaux peuvent être lus.')],
          ['TXT / MD', tx('Plain readable text.', 'Texte brut lisible.')],
          ['.cvm', tx('Readable CV Maker project content when supported.', 'Contenu lisible d’un projet CV Maker lorsque pris en charge.')]
        ]),
        note('Use Preview CV to verify exactly which CV JAM is reading.', 'Utilisez Aperçu du CV pour vérifier exactement quel CV JAM lit.')
      ], 'Analyzer'),

    article('cvm', 'CV Maker (CVM) and JAM', 'CV Maker (CVM) et JAM',
      'How JAM relates to Farouk’s separate CV Maker application.',
      'Relation entre JAM et l’application CV Maker séparée de Farouk.',
      ['cvm', 'cv maker', 'cvm file', 'separate app'], [
        p('JAM and CV Maker are separate Windows applications. JAM manages the job-search pipeline; CV Maker is focused on creating CVs.', 'JAM et CV Maker sont deux applications Windows séparées. JAM gère le pipeline de recherche d’emploi ; CV Maker est centré sur la création de CV.'),
        note('JAM can read supported .cvm content for Analyzer purposes, but a .cvm file is not the same thing as a .jam project.', 'JAM peut lire le contenu .cvm pris en charge pour l’Analyseur, mais un fichier .cvm n’est pas un projet .jam.')
      ], 'Files'),

    article('data-locations', 'Data Locations', 'Emplacements des données',
      'Where JAM stores its database, backups, exports, projects, logs, recovery and attachments.',
      'Où JAM stocke sa base, ses sauvegardes, exports, projets, journaux, récupération et pièces jointes.',
      ['data locations', 'folders', 'localappdata', 'documents', 'exports folder', 'attachments'], [
        table('Default locations', 'Emplacements par défaut', [tx('Data', 'Donnée'), tx('Default location', 'Emplacement par défaut')], [
          [tx('Database', 'Base de données'), '%LOCALAPPDATA%\\Farouk\\JAM\\database'],
          [tx('Backups', 'Sauvegardes'), '%LOCALAPPDATA%\\Farouk\\JAM\\backups'],
          [tx('Logs', 'Journaux'), '%LOCALAPPDATA%\\Farouk\\JAM\\logs'],
          [tx('Recovery', 'Récupération'), '%LOCALAPPDATA%\\Farouk\\JAM\\recovery'],
          [tx('Attachments', 'Pièces jointes'), '%LOCALAPPDATA%\\Farouk\\JAM\\attachments'],
          [tx('Exports', 'Exports'), 'Documents\\JAM Exports'],
          [tx('Projects', 'Projets'), 'Documents\\JAM Projects']
        ]),
        note('Some data locations can be changed from Settings. A new location can require an app restart before becoming active.', 'Certains emplacements peuvent être modifiés depuis Paramètres. Un redémarrage peut être nécessaire avant activation.')
      ], 'Settings'),

    article('privacy', 'Data Privacy and Local-First', 'Confidentialité et fonctionnement local',
      'What stays on your computer and how the Analyzer handles CV/job text.',
      'Ce qui reste sur votre ordinateur et comment l’Analyseur traite le CV et l’offre.',
      ['privacy', 'offline', 'local first', 'cloud', 'cv data', 'job description'], [
        p('JAM is designed as a local-first desktop application. Application data, local database content, Analyzer evidence and most working files stay on your computer.', 'JAM est conçu comme une application desktop local-first. Les candidatures, la base locale, les preuves de l’Analyseur et la plupart des fichiers de travail restent sur votre ordinateur.'),
        note('The multilingual Analyzer runs locally. CV and job-description text are not sent to a cloud AI API for scoring.', 'L’Analyseur multilingue fonctionne localement. Le texte du CV et de l’offre n’est pas envoyé à une API d’IA cloud pour le scoring.')
      ], 'Privacy'),

    article('dates', 'Dates and Date Applied', 'Dates et date de candidature',
      'How JAM tracks when an opportunity was saved, updated and first applied.',
      'Comment JAM suit l’enregistrement, la mise à jour et la première candidature.',
      ['date saved', 'date updated', 'date applied', 'applied date'], [
        p('JAM tracks saved and updated timestamps. The first time an application enters Applied or a later stage, JAM can automatically record date_applied.', 'JAM suit les dates d’enregistrement et de mise à jour. La première fois qu’une candidature passe à Envoyée ou à une étape ultérieure, JAM peut enregistrer automatiquement date_applied.')
      ], 'Applications'),

    article('diagnostics', 'Diagnostics', 'Diagnostics',
      'Check JAM health, paths and common runtime issues from Settings.',
      'Vérifier l’état de JAM, les chemins et les problèmes courants depuis Paramètres.',
      ['diagnostics', 'health check', 'green', 'warning', 'error'], [
        p('Diagnostics displays checks using success, warning and error states. Use it when a folder, database, runtime component or other local resource appears unavailable.', 'Diagnostics affiche des contrôles avec états succès, avertissement et erreur. Utilisez-le lorsqu’un dossier, une base, un composant ou une ressource locale semble indisponible.'),
        table('Status icons', 'Icônes d’état', [tx('Icon', 'Icône'), tx('Meaning', 'Signification')], [
          ['✓', tx('Check passed.', 'Contrôle réussi.')],
          ['⚠', tx('Attention or non-blocking issue.', 'Attention ou problème non bloquant.')],
          ['✕', tx('Check failed or resource unavailable.', 'Échec du contrôle ou ressource indisponible.')]
        ])
      ], 'Settings'),

    article('duplicates', 'Duplicate Detection', 'Détection des doublons',
      'How JAM warns before saving the same opportunity more than once.',
      'Comment JAM avertit avant d’enregistrer plusieurs fois la même opportunité.',
      ['duplicate', 'same job', 'company title url', 'save anyway'], [
        p('JAM checks likely duplicates using Company + Job Title + URL. When a match is found, you can open the existing application, save anyway, or cancel.', 'JAM détecte les doublons probables avec Entreprise + Poste + URL. Lorsqu’une correspondance est trouvée, vous pouvez ouvrir l’existante, enregistrer quand même ou annuler.')
      ], 'Applications'),

    article('editing', 'Editing an Application', 'Modifier une candidature',
      'Open an existing application and update its fields, analysis or tracking data.',
      'Ouvrir une candidature existante et mettre à jour ses champs, son analyse ou son suivi.',
      ['edit job', 'edit selected', 'double click', 'save changes'], [
        steps('Edit a saved application', 'Modifier une candidature enregistrée', [
          tx('Select exactly one row and click Edit selected, or use the supported row-opening action.', 'Sélectionnez exactement une ligne et cliquez sur Modifier la sélection, ou utilisez l’action d’ouverture disponible.'),
          tx('Update the fields you need.', 'Modifiez les champs nécessaires.'),
          tx('Use Analyze if you want to refresh the CV Match result.', 'Utilisez Analyser si vous souhaitez actualiser le résultat CV Match.'),
          tx('Click Save changes.', 'Cliquez sur Enregistrer les modifications.')
        ])
      ], 'Applications'),

    article('excel-export', 'Excel Export', 'Export Excel',
      'Export selected or visible application data to a polished Excel workbook.',
      'Exporter les candidatures sélectionnées ou visibles vers un classeur Excel soigné.',
      ['excel export', 'xlsx', 'export selected', 'spreadsheet'], [
        p('Excel export creates a formatted workbook with real Excel date values, filters and JAM styling. If rows are selected, JAM exports the selection; otherwise the current visible/filtered set is used where supported.', 'L’export Excel crée un classeur formaté avec de vraies dates Excel, des filtres et le style JAM. Si des lignes sont sélectionnées, JAM exporte la sélection ; sinon l’ensemble visible/filtré est utilisé lorsque cela s’applique.'),
        note('The export intentionally avoids an Excel structured table because that previously caused repair warnings when combined with AutoFilter.', 'L’export évite volontairement les tableaux structurés Excel car ils provoquaient auparavant des avertissements de réparation avec AutoFilter.')
      ], 'Exports'),

    article('excel-import', 'Excel Import', 'Import Excel',
      'Preview and merge job rows from an Excel file into the current JAM database.',
      'Prévisualiser et fusionner des lignes Excel dans la base JAM actuelle.',
      ['excel import', 'xlsx import', 'merge', 'mapping', 'invalid rows', 'duplicates'], [
        p('Excel Import merges valid rows into the current Applications data. It does not replace the entire database.', 'L’Import Excel fusionne les lignes valides dans les données Candidatures actuelles. Il ne remplace pas toute la base.'),
        bullets('Import workflow', 'Fonctionnement de l’import', [
          tx('Preview before writing.', 'Prévisualisation avant écriture.'),
          tx('Column mapping.', 'Correspondance des colonnes.'),
          tx('Duplicate information.', 'Informations sur les doublons.'),
          tx('Invalid-row reasons and row numbers.', 'Raisons des lignes invalides et numéros de ligne.'),
          tx('Valid rows can still import even if some rows fail.', 'Les lignes valides peuvent être importées même si certaines échouent.')
        ])
      ], 'Imports'),

    article('export-history', 'Export History', 'Historique des exports',
      'Reopen exported files and folders without hunting through Windows Explorer.',
      'Rouvrir les fichiers et dossiers exportés sans les rechercher dans l’Explorateur Windows.',
      ['export history', 'open file', 'open folder', 'remove history'], [
        p('JAM records export history so you can Open, Open Folder or Remove from history.', 'JAM enregistre l’historique des exports afin de pouvoir Ouvrir, Ouvrir le dossier ou Retirer de l’historique.'),
        note('Removing an export from JAM history does not delete the exported file from disk.', 'Retirer un export de l’historique JAM ne supprime pas le fichier exporté du disque.')
      ], 'Exports'),

    article('faq', 'Frequently Asked Questions', 'Questions fréquentes',
      'Quick answers to common JAM questions.',
      'Réponses rapides aux questions courantes sur JAM.',
      ['faq', 'questions', 'help', 'is jam online', 'delete history', 'cloud ai'], [
        table('FAQ', 'FAQ', [tx('Question', 'Question'), tx('Answer', 'Réponse')], [
          [tx('Does JAM need cloud AI to analyze?', 'JAM a-t-il besoin d’une IA cloud pour analyser ?'), tx('No. The Analyzer runs locally.', 'Non. L’Analyseur fonctionne localement.')],
          [tx('Does Excel Import replace my database?', 'L’Import Excel remplace-t-il ma base ?'), tx('No. Valid rows are merged into the current data.', 'Non. Les lignes valides sont fusionnées avec les données actuelles.')],
          [tx('Does removing Export History delete the file?', 'Retirer un élément de l’historique supprime-t-il le fichier ?'), tx('No. It only removes the history entry.', 'Non. Cela retire uniquement l’entrée de l’historique.')],
          [tx('Are .jam attachments embedded inside the project?', 'Les pièces jointes sont-elles intégrées au fichier .jam ?'), tx('No. Attachment metadata is stored; physical files stay in local attachment storage.', 'Non. Les métadonnées sont stockées ; les fichiers physiques restent dans le stockage local.')],
          [tx('Why can the first analysis take longer?', 'Pourquoi la première analyse peut-elle être plus longue ?'), tx('The local multilingual model may need initial setup/loading.', 'Le modèle multilingue local peut nécessiter une initialisation ou un chargement initial.')]
        ])
      ], 'FAQ'),

    article('filters-sorting', 'Filters and Sorting', 'Filtres et tri',
      'Find the exact applications you need in the main table.',
      'Trouver précisément les candidatures voulues dans le tableau principal.',
      ['filter', 'sort', 'column', 'a z', 'highest first', 'search values'], [
        p('Applications supports Excel-like column filters and sorting. Depending on the column, you can search values, select values, sort A→Z/Z→A, sort scores, dates and other fields.', 'Candidatures prend en charge des filtres et tris de colonnes inspirés d’Excel. Selon la colonne, vous pouvez rechercher des valeurs, les sélectionner, trier A→Z/Z→A, les scores, les dates et d’autres champs.'),
        note('Use Clear filters to return to the unfiltered table.', 'Utilisez Effacer les filtres pour revenir au tableau non filtré.')
      ], 'Applications'),

    article('language', 'French and English Interface', 'Interface française et anglaise',
      'Switch JAM’s interface language from Settings.',
      'Changer la langue de l’interface JAM depuis Paramètres.',
      ['french', 'english', 'language', 'français', 'anglais', 'translation'], [
        p('JAM supports English and French. Open Settings → Language and choose the interface language. The change is applied across JAM and saved for later sessions.', 'JAM prend en charge l’anglais et le français. Ouvrez Paramètres → Langue et choisissez la langue de l’interface. Le changement s’applique dans JAM et est enregistré pour les sessions suivantes.')
      ], 'Settings'),

    article('getting-started', 'Getting Started', 'Bien démarrer',
      'A short first-use workflow for a new JAM user.',
      'Un parcours rapide pour commencer avec JAM.',
      ['getting started', 'tutorial', 'first use', 'start', 'how to use'], [
        steps('First 5 minutes', 'Les 5 premières minutes', [
          tx('Choose your CV from Analyzer or Settings if you want CV matching.', 'Choisissez votre CV depuis l’Analyseur ou Paramètres si vous souhaitez utiliser le matching CV.'),
          tx('Add one job manually or open Capture Mode while browsing a job board.', 'Ajoutez une offre manuellement ou ouvrez le Mode Capture pendant votre navigation.'),
          tx('Set the correct status and source.', 'Définissez le bon statut et la bonne source.'),
          tx('Use Analyze when you want evidence-based CV matching.', 'Utilisez Analyser lorsque vous souhaitez une comparaison CV fondée sur des preuves.'),
          tx('Review Applications and Pipeline to manage progress.', 'Consultez Candidatures et Pipeline pour gérer la progression.'),
          tx('Save a .jam snapshot when you want a portable project copy.', 'Enregistrez un instantané .jam lorsque vous souhaitez une copie portable du projet.')
        ])
      ], 'Tutorial'),

    article('interactive-tutorial', 'Interactive Guided Tutorial', 'Tutoriel guidé interactif',
      'Replay the first-run walkthrough that introduces Capture Mode and every main JAM section.',
      'Rejouer le parcours de première utilisation qui présente le Mode Capture et chaque section principale de JAM.',
      ['tutorial', 'guided tour', 'onboarding', 'first launch', 'replay tutorial', 'walkthrough', 'capture mode'], [
        p('On the first launch, JAM can guide you through the interface with a darkened screen, animated spotlight, arrows and short explanations. The tour starts with Capture Mode, then continues through the main JAM pages.',
          'Au premier lancement, JAM peut vous guider dans l’interface avec un écran assombri, un projecteur animé, des flèches et de courtes explications. Le tutoriel commence par le Mode Capture puis parcourt les principales pages de JAM.'),
        steps('What the tour covers', 'Ce que couvre le tutoriel', [
          tx('Open Capture Mode and learn why it stays pinned while you apply.', 'Ouvrir le Mode Capture et comprendre pourquoi il reste épinglé pendant vos candidatures.'),
          tx('Return to JAM and tour the Dashboard and top project controls.', 'Revenir à JAM et parcourir le Tableau de bord ainsi que les contrôles de projet.'),
          tx('Review Applications, Pipeline, Analytics, Calendar, Analyzer, Exports and Settings.', 'Découvrir Candidatures, Pipeline, Statistiques, Calendrier, Analyseur, Exports et Paramètres.'),
          tx('Finish on the Guide and learn where to replay the tour later.', 'Terminer sur le Guide et apprendre où rejouer le tutoriel plus tard.')
        ]),
        note('Use the ▶ Play tutorial button in the top-right corner of the Guide at any time. Stopping the tour early does not remove this replay option.',
          'Utilisez à tout moment le bouton ▶ Lire le tutoriel en haut à droite du Guide. Arrêter le tutoriel avant la fin ne supprime pas cette option de replay.')
      ], 'Tutorial'),

    article('guide-search', 'Guide Search', 'Recherche dans le Guide',
      'How the built-in knowledge-base search works.',
      'Comment fonctionne la recherche intégrée de la base de connaissances.',
      ['guide search', 'typo', 'fuzzy', 'live suggestions', 'knowledge base'], [
        p('Guide search updates the result list instantly while you type. It searches titles, summaries, keywords and article content.', 'La recherche du Guide met à jour la liste des résultats instantanément pendant la saisie. Elle recherche dans les titres, résumés, mots-clés et contenus.'),
        note('The search is typo-tolerant. Close spellings can still return relevant articles, and matching text is highlighted in result titles.', 'La recherche tolère les fautes de frappe. Des orthographes proches peuvent tout de même retourner les bons articles et le texte correspondant est surligné dans les titres.')
      ], 'Guide'),

    article('jam-files', '.jam Project Files', 'Fichiers projet .jam',
      'Save and reopen portable JAM project snapshots.',
      'Enregistrer et rouvrir des instantanés de projet JAM portables.',
      ['jam file', '.jam', 'project', 'open project', 'save project', 'snapshot'], [
        p('The .jam format is JAM’s native portable project format. Use Open .jam and Save .jam from the top actions.', 'Le format .jam est le format de projet portable natif de JAM. Utilisez Ouvrir .jam et Enregistrer .jam dans les actions supérieures.'),
        p('New snapshots use a timestamped filename such as JAM_23092026_1333.jam so repeated saves do not automatically overwrite older snapshots.', 'Les nouveaux instantanés utilisent un nom horodaté comme JAM_23092026_1333.jam afin de ne pas écraser automatiquement les précédents.'),
        note('Opening a .jam project can replace the in-app dataset. JAM uses dirty-state protection to warn about unsaved project changes.', 'L’ouverture d’un projet .jam peut remplacer les données chargées. JAM utilise une protection contre les modifications non enregistrées.')
      ], 'Files'),

    article('job-boards', 'Job Boards, LinkedIn and Source', 'Sites d’emploi, LinkedIn et source',
      'Track where each opportunity came from and use Capture while browsing.',
      'Suivre l’origine de chaque opportunité et utiliser Capture pendant la navigation.',
      ['linkedin', 'indeed', 'welcome to the jungle', 'jobteaser', 'source', 'job board'], [
        p('The Source field records where you found the opportunity, for example LinkedIn, Welcome to the Jungle, JobTeaser, Indeed or another platform.', 'Le champ Source indique où vous avez trouvé l’opportunité, par exemple LinkedIn, Welcome to the Jungle, JobTeaser, Indeed ou une autre plateforme.'),
        steps('Fast LinkedIn-to-JAM workflow', 'Flux rapide LinkedIn vers JAM', [
          tx('Open Capture Mode.', 'Ouvrez le Mode Capture.'),
          tx('Copy the company, title, URL and job description from the job board.', 'Copiez l’entreprise, le poste, l’URL et la description depuis le site d’emploi.'),
          tx('Set Source to LinkedIn or the relevant platform.', 'Définissez Source sur LinkedIn ou la plateforme concernée.'),
          tx('Save & Clear, then continue browsing.', 'Cliquez sur Enregistrer et vider, puis continuez votre navigation.')
        ])
      ], 'Capture'),

    article('keyboard-shortcuts', 'Keyboard Shortcuts', 'Raccourcis clavier',
      'Use JAM faster with built-in keyboard shortcuts.',
      'Utiliser JAM plus rapidement avec les raccourcis intégrés.',
      ['keyboard shortcuts', 'ctrl n', 'ctrl k', 'ctrl shift c', 'ctrl s', 'ctrl enter', 'esc'], [
        table('Shortcuts', 'Raccourcis', [tx('Shortcut', 'Raccourci'), tx('Action', 'Action')], [
          ['Ctrl+N', tx('Add Job', 'Ajouter une offre')],
          ['Ctrl+K', tx('Focus Applications search', 'Placer le focus sur la recherche Candidatures')],
          ['Ctrl+Shift+C', tx('Open Capture Mode', 'Ouvrir le Mode Capture')],
          ['Ctrl+S', tx('Save the current .jam project', 'Enregistrer le projet .jam actuel')],
          ['Ctrl+Enter', tx('Analyze when Analyzer is open', 'Analyser lorsque l’Analyseur est ouvert')],
          ['Esc', tx('Close the active dialog', 'Fermer la boîte de dialogue active')]
        ])
      ], 'Shortcuts'),

    article('links-urls', 'Links and URLs', 'Liens et URL',
      'Job and contact links are clickable where relevant.',
      'Les liens d’offres et de contacts sont cliquables lorsque cela est pertinent.',
      ['url', 'links', 'job link', 'contact link', 'open link'], [
        p('JAM normalizes common URLs and exposes clickable job/contact links in the relevant views. Use Open Contact Link from Add/Edit Job for the primary contact link.', 'JAM normalise les URL courantes et affiche des liens d’offres/contacts cliquables dans les vues pertinentes. Utilisez Ouvrir le lien du contact depuis Ajouter/Modifier pour le contact principal.')
      ], 'Applications'),

    article('logs', 'Logs', 'Journaux',
      'Review JAM activity and errors when troubleshooting.',
      'Consulter l’activité JAM et les erreurs pour le dépannage.',
      ['logs', 'activity', 'info', 'success', 'warning', 'error', 'copy logs'], [
        p('JAM Logs can be opened from Settings. Use level filters such as All, Info, Success, Warning and Error, plus search when available.', 'Les Journaux JAM sont accessibles depuis Paramètres. Utilisez les filtres All, Info, Success, Warning et Error, ainsi que la recherche lorsqu’elle est disponible.'),
        note('Logs are useful when reporting a bug because they can show the action that failed and the related error message.', 'Les journaux sont utiles pour signaler un bug car ils peuvent montrer l’action qui a échoué et le message associé.')
      ], 'Support'),

    article('notes-history', 'Notes History', 'Historique des notes',
      'Keep timestamped notes instead of overwriting one static note.',
      'Conserver des notes horodatées au lieu d’écraser une note unique.',
      ['notes history', 'notes', 'timestamp', 'edit note', 'remove note'], [
        p('Saved applications can keep multiple timestamped notes. You can add, edit and remove notes while preserving the richer tracking history.', 'Les candidatures enregistrées peuvent conserver plusieurs notes horodatées. Vous pouvez ajouter, modifier et supprimer des notes tout en gardant un historique de suivi plus riche.')
      ], 'Tracking'),

    article('pipeline', 'Pipeline', 'Pipeline',
      'Visualize applications by status and move through the hiring flow.',
      'Visualiser les candidatures par statut et suivre le processus de recrutement.',
      ['pipeline', 'status flow', 'board', 'drag'], [
        p('Pipeline groups applications by status. The board is designed for direct visual tracking and supports drag-style navigation across the board.', 'Pipeline regroupe les candidatures par statut. Le tableau est conçu pour un suivi visuel direct et permet de naviguer par glissement.'),
        timeline('Typical hiring flow', 'Flux de recrutement typique', [
          tx('Saved / To Review', 'Enregistrée / À examiner'),
          tx('Applied', 'Candidature envoyée'),
          tx('Interviewing', 'Entretien'),
          tx('Offer', 'Offre reçue'),
          tx('Accepted / Rejected / Withdrawn', 'Acceptée / Refusée / Retirée')
        ])
      ], 'Pipeline'),

    article('recent-projects', 'Recent Projects', 'Projets récents',
      'Quickly reopen .jam projects you used recently.',
      'Rouvrir rapidement les projets .jam utilisés récemment.',
      ['recent projects', 'project history', 'last opened', 'job count'], [
        p('Recent Projects stores useful metadata such as project name, last opened/modified information and job count where available.', 'Projets récents conserve des métadonnées utiles comme le nom du projet, les informations de dernière ouverture/modification et le nombre d’offres lorsque disponible.'),
        note('Removing an item from Recent Projects does not delete the .jam file itself.', 'Retirer un élément de Projets récents ne supprime pas le fichier .jam lui-même.')
      ], 'Files'),

    article('quick-filters', 'Quick Filters', 'Filtres rapides',
      'One-click presets for common application views.',
      'Préréglages en un clic pour les vues courantes.',
      ['quick filters', 'applied this week', 'interviewing', 'score 70', '5 stars', 'not analyzed'], [
        bullets('Examples', 'Exemples', [
          tx('Applied this week', 'Candidatures envoyées cette semaine'),
          tx('Interviewing', 'Entretien'),
          tx('Score ≥ 70', 'Score ≥ 70'),
          tx('5 stars', '5 étoiles'),
          tx('Not analyzed', 'Non analysées'),
          tx('France / Tunisia', 'France / Tunisie')
        ])
      ], 'Applications'),

    article('ratings', 'Ratings / Stars', 'Notes / Étoiles',
      'Rate an opportunity from 1 to 5 stars for your own prioritization.',
      'Noter une opportunité de 1 à 5 étoiles pour votre propre priorisation.',
      ['rating', 'stars', '5 stars', 'priority'], [
        p('Stars are your manual preference signal. They are separate from the Analyzer score, which is evidence-based.', 'Les étoiles représentent votre préférence manuelle. Elles sont indépendantes du score de l’Analyseur, qui est fondé sur des preuves.')
      ], 'Applications'),

    article('reset-jam', 'Reset JAM', 'Réinitialiser JAM',
      'Delete JAM’s internal tracked data and settings through the protected Danger Zone flow.',
      'Supprimer les données internes et paramètres JAM via la procédure protégée de la Zone dangereuse.',
      ['reset', 'danger zone', 'delete all data', 'countdown'], [
        p('Reset JAM is intentionally protected by confirmation steps and a final countdown. Use it only when you really want to clear JAM’s internal tracked data and settings.', 'La réinitialisation JAM est volontairement protégée par plusieurs confirmations et un compte à rebours final. Utilisez-la uniquement si vous souhaitez réellement effacer les données suivies et paramètres internes.'),
        note('Files already exported to disk are not deleted by the JAM reset flow.', 'Les fichiers déjà exportés sur le disque ne sont pas supprimés par la réinitialisation JAM.')
      ], 'Safety'),

    article('salary-fields', 'Salary Fields', 'Champs de salaire',
      'Store the original salary text plus structured min/max, currency, period and gross/net basis.',
      'Conserver le texte salarial original ainsi que min/max, devise, période et base brut/net.',
      ['salary', 'min max', 'gross net', 'annual', 'monthly', 'currency'], [
        bullets('Structured salary data', 'Données salariales structurées', [
          tx('Minimum and maximum.', 'Minimum et maximum.'),
          tx('Currency.', 'Devise.'),
          tx('Monthly or annual period.', 'Période mensuelle ou annuelle.'),
          tx('Gross or net basis.', 'Base brute ou nette.'),
          tx('Original salary text retained for traceability.', 'Texte salarial original conservé pour traçabilité.')
        ])
      ], 'Applications'),

    article('saved-views', 'Saved Views', 'Vues enregistrées',
      'Save a useful filter/sort state and reopen it later.',
      'Enregistrer un état de filtres/tri utile et le rouvrir plus tard.',
      ['saved views', 'save filter', 'rename view', 'delete view'], [
        p('Saved Views lets you save a useful Applications filter state, reopen it later, rename it or delete it.', 'Vues enregistrées permet de sauvegarder un état utile des filtres Candidatures, de le rouvrir, le renommer ou le supprimer.')
      ], 'Applications'),

    article('search-applications', 'Search Applications', 'Rechercher des candidatures',
      'Search the main Applications data quickly.',
      'Rechercher rapidement dans les données Candidatures.',
      ['application search', 'ctrl k', 'find job', 'search jobs'], [
        p('Use the Applications search field to narrow the table quickly. Ctrl+K focuses the search box.', 'Utilisez le champ de recherche Candidatures pour réduire rapidement le tableau. Ctrl+K place le focus sur la recherche.')
      ], 'Applications'),

    article('settings', 'Settings', 'Paramètres',
      'Configure language, CV, salary targets, Capture, backups, paths, diagnostics and reset options.',
      'Configurer la langue, le CV, les objectifs salariaux, Capture, les sauvegardes, chemins, diagnostics et réinitialisation.',
      ['settings', 'preferences', 'data safety', 'capture preferences', 'salary target', 'language'], [
        bullets('Settings areas', 'Zones des Paramètres', [
          tx('Language.', 'Langue.'),
          tx('CV and salary preferences.', 'Préférences CV et salaire.'),
          tx('Salary converter.', 'Convertisseur de salaire.'),
          tx('Data Safety and backups.', 'Sécurité des données et sauvegardes.'),
          tx('Data Locations.', 'Emplacements des données.'),
          tx('Capture Mode preferences.', 'Préférences du Mode Capture.'),
          tx('Diagnostics and logs.', 'Diagnostics et journaux.'),
          tx('Danger Zone / Reset JAM.', 'Zone dangereuse / Réinitialiser JAM.')
        ])
      ], 'Settings'),

    article('sources', 'Sources', 'Sources',
      'Record the website or channel where a job opportunity came from.',
      'Enregistrer le site ou canal d’origine d’une opportunité.',
      ['source', 'platform', 'linkedin', 'indeed', 'jobteaser', 'apec'], [
        p('Source is useful for remembering where an application came from and for later analytics. The field provides suggestions for common job platforms while still allowing other values.', 'Source permet de mémoriser l’origine d’une candidature et servira aux analyses. Le champ propose des plateformes courantes tout en permettant d’autres valeurs.')
      ], 'Applications'),

    article('statuses', 'Statuses', 'Statuts',
      'Understand JAM application statuses and the status-history timeline.',
      'Comprendre les statuts JAM et la chronologie de l’historique.',
      ['status', 'saved', 'to review', 'applied', 'interviewing', 'offer', 'accepted', 'rejected', 'withdrawn', 'archived'], [
        table('Application statuses', 'Statuts de candidature', [tx('Status', 'Statut'), tx('Typical meaning', 'Signification typique')], [
          [tx('Saved', 'Enregistrée'), tx('Opportunity saved but not yet applied.', 'Opportunité enregistrée mais candidature non envoyée.')],
          [tx('To Review', 'À examiner'), tx('Needs review before deciding what to do.', 'À examiner avant décision.')],
          [tx('Applied', 'Candidature envoyée'), tx('Application sent.', 'Candidature envoyée.')],
          [tx('Interviewing', 'Entretien'), tx('Interview process is active.', 'Processus d’entretien en cours.')],
          [tx('Offer', 'Offre reçue'), tx('An offer was received.', 'Une offre a été reçue.')],
          [tx('Accepted', 'Acceptée'), tx('Offer accepted.', 'Offre acceptée.')],
          [tx('Rejected', 'Refusée'), tx('Application ended with rejection.', 'Candidature terminée par un refus.')],
          [tx('Withdrawn', 'Retirée'), tx('You withdrew from the process.', 'Vous vous êtes retiré du processus.')],
          [tx('Archived', 'Archivée'), tx('Hidden from the default active view.', 'Masquée de la vue active par défaut.')]
        ])
      ], 'Applications'),

    article('support-contact', 'Support, Contact and Developer', 'Support, contact et développeur',
      'Where to find developer information, official links and support options.',
      'Où trouver les informations du développeur, les liens officiels et les options de soutien.',
      ['support jam', 'contact', 'developer', 'farouk', 'website', 'github', 'paypal', 'ko-fi'], [
        p('Use Contact and About JAM from the left sidebar for official developer information and project links. Support JAM provides optional support links while JAM remains free to use.', 'Utilisez Contact et À propos de JAM dans la barre latérale pour les informations officielles du développeur et les liens du projet. Soutenir JAM propose des liens facultatifs, JAM restant gratuit.')
      ], 'About'),

    article('tracking-history', 'Tracking and History', 'Suivi et historique',
      'Contacts, notes, attachments and status history attached to a saved application.',
      'Contacts, notes, pièces jointes et historique de statut associés à une candidature enregistrée.',
      ['tracking', 'history', 'contacts', 'notes', 'attachments', 'status timeline'], [
        p('For an existing application, Add/Edit Job exposes Tracking & History so you can work with richer contacts, notes and attachments without leaving the editor. Open Full Tracking is available for the dedicated view.', 'Pour une candidature existante, Ajouter/Modifier affiche Suivi et historique afin de gérer les contacts enrichis, notes et pièces jointes sans quitter l’éditeur. Ouvrir le suivi complet reste disponible pour la vue dédiée.'),
        note('A brand-new unsaved application must be saved before JAM can attach richer child records such as multiple contacts or attachments.', 'Une nouvelle candidature non enregistrée doit d’abord être sauvegardée avant de pouvoir recevoir des éléments enrichis comme plusieurs contacts ou des pièces jointes.')
      ], 'Tracking'),

    article('troubleshooting', 'Troubleshooting', 'Dépannage',
      'What to check when JAM, Capture, files or the Analyzer do not behave as expected.',
      'Que vérifier lorsque JAM, Capture, les fichiers ou l’Analyseur ne se comportent pas comme prévu.',
      ['troubleshooting', 'problem', 'bug', 'slow', 'crash', 'diagnostics', 'logs'], [
        steps('Basic checks', 'Vérifications de base', [
          tx('Open Diagnostics in Settings and check for warnings/errors.', 'Ouvrez Diagnostics dans Paramètres et vérifiez les avertissements/erreurs.'),
          tx('Open JAM Logs and look at the latest Error or Warning entries.', 'Ouvrez les Journaux JAM et consultez les dernières entrées Error ou Warning.'),
          tx('Confirm that configured data folders still exist and are writable.', 'Vérifiez que les dossiers configurés existent toujours et sont accessibles en écriture.'),
          tx('For Analyzer problems, confirm the selected CV still exists and contains readable/selectable text.', 'Pour l’Analyseur, vérifiez que le CV sélectionné existe encore et contient du texte lisible/sélectionnable.'),
          tx('If reporting a bug, include what you clicked, what happened and the relevant log message.', 'Pour signaler un bug, indiquez l’action effectuée, le résultat obtenu et le message de journal pertinent.')
        ])
      ], 'Support'),

    article('work-mode', 'Work Mode', 'Mode de travail',
      'Track whether a role is onsite, hybrid or remote.',
      'Indiquer si un poste est sur site, hybride ou en télétravail.',
      ['work mode', 'onsite', 'hybrid', 'remote', 'telework'], [
        table('Work modes', 'Modes de travail', [tx('Mode', 'Mode'), tx('Meaning', 'Signification')], [
          [tx('Onsite', 'Sur site'), tx('Primarily at the employer location.', 'Principalement dans les locaux de l’employeur.')],
          [tx('Hybrid', 'Hybride'), tx('Mix of onsite and remote work.', 'Mélange de travail sur site et à distance.')],
          [tx('Remote', 'Télétravail'), tx('Primarily remote.', 'Principalement à distance.')]
        ])
      ], 'Applications'),

    article('workflow-overview', 'Workflow Overview', 'Vue d’ensemble du flux',
      'A visual summary of how a job moves through JAM.',
      'Résumé visuel du parcours d’une offre dans JAM.',
      ['workflow', 'process', 'capture analyze apply interview offer'], [
        timeline('From discovery to outcome', 'De la découverte au résultat', [
          tx('Discover a role on a job board', 'Découvrir une offre sur un site d’emploi'),
          tx('Capture or Add Job', 'Capturer ou Ajouter une offre'),
          tx('Review / Analyze against CV', 'Examiner / Analyser par rapport au CV'),
          tx('Apply and update status', 'Postuler et mettre à jour le statut'),
          tx('Track contacts, notes and attachments', 'Suivre contacts, notes et pièces jointes'),
          tx('Interview / Offer / Final outcome', 'Entretien / Offre / Résultat final')
        ]),
        bars('JAM areas involved', 'Zones JAM impliquées', [
          { label: tx('Capture / Add', 'Capture / Ajout'), value: 35 },
          { label: tx('Analyze / Review', 'Analyse / Revue'), value: 55 },
          { label: tx('Applications / Pipeline', 'Candidatures / Pipeline'), value: 80 },
          { label: tx('Tracking / Exports', 'Suivi / Exports'), value: 100 }
        ])
      ], 'Tutorial'),

    article('analytics-trends', 'Analytics and Application Trends', 'Statistiques et tendances des candidatures',
      'Use JAM Analytics to visualize application activity over time and understand your sources and status mix.',
      'Utilisez les statistiques JAM pour visualiser l’activité dans le temps et comprendre vos sources et statuts.',
      ['analytics', 'trend', 'curve', 'chart', 'applications over time', 'sources', 'statistics', '30 days', '90 days'], [
        p('Analytics uses only the applications already stored in JAM. By default, the trend starts from the earliest saved application and runs to today.', 'Les statistiques utilisent uniquement les candidatures déjà enregistrées dans JAM. Par défaut, la tendance commence à la première candidature enregistrée et va jusqu’à aujourd’hui.'),
        bullets('What you can see', 'Ce que vous pouvez voir', [
          tx('Tracked and applied activity over time.', 'Activité des offres suivies et candidatures envoyées dans le temps.'),
          tx('A custom From / To date range plus All data, 30-day and 90-day shortcuts.', 'Une période personnalisée De / À ainsi que des raccourcis Toutes les données, 30 jours et 90 jours.'),
          tx('Average Analyzer score for jobs saved in the selected period.', 'Score moyen de l’Analyseur pour les offres de la période sélectionnée.'),
          tx('Top application sources and current status distribution.', 'Principales sources de candidatures et répartition actuelle des statuts.')
        ]),
        note('Analytics never invents missing history. It calculates the charts from the dates and fields that exist in your JAM database.', 'Les statistiques n’inventent jamais l’historique manquant. Les graphiques sont calculés à partir des dates et champs réellement présents dans votre base JAM.')
      ], 'Tracking'),

    article('calendar-planner', 'Calendar and Interviews', 'Calendrier et entretiens',
      'View applications by date and schedule interviews, follow-ups, deadlines and reminders.',
      'Visualisez les candidatures par date et planifiez entretiens, relances, échéances et rappels.',
      ['calendar', 'interview', 'follow-up', 'deadline', 'reminder', 'schedule', 'planner', 'event'], [
        steps('Plan an interview or reminder', 'Planifier un entretien ou un rappel', [
          tx('Open Calendar from the left sidebar.', 'Ouvrez Calendrier depuis la barre latérale.'),
          tx('Select a day and click + Add event.', 'Sélectionnez un jour puis cliquez sur + Ajouter un événement.'),
          tx('Choose Interview, Follow-up, Deadline, Reminder or Other.', 'Choisissez Entretien, Relance, Échéance, Rappel ou Autre.'),
          tx('Optionally link the event to an existing JAM application and add a location/link or notes.', 'Vous pouvez lier l’événement à une candidature JAM existante et ajouter un lieu/lien ou des notes.'),
          tx('Saved events appear in the month calendar, selected-day panel and upcoming list.', 'Les événements enregistrés apparaissent dans le calendrier, le panneau du jour sélectionné et la liste des événements à venir.')
        ]),
        p('Applications also appear automatically on the calendar using date_applied when available, otherwise date_saved.', 'Les candidatures apparaissent aussi automatiquement dans le calendrier en utilisant date_applied lorsqu’elle existe, sinon date_saved.')
      ], 'Tracking'),

    article('notifications', 'Notifications and Reminders', 'Notifications et rappels',
      'Control JAM reminder categories from Settings and review active reminders from the notification bell.',
      'Contrôlez les catégories de rappels depuis Paramètres et consultez-les avec la cloche de notifications.',
      ['notifications', 'reminders', 'bell', 'disable', 'interview tomorrow', 'backup reminder', 'inactivity', 'stale application'], [
        p('JAM builds reminders from your local application, calendar and backup data. The notification badge shows the reminders that currently need attention.', 'JAM crée les rappels à partir de vos données locales de candidatures, calendrier et sauvegardes. Le badge de notifications indique les rappels qui demandent votre attention.'),
        table('Notification controls', 'Contrôles des notifications', [tx('Type', 'Type'), tx('Purpose', 'Utilité')], [
          [tx('Interview tomorrow / soon', 'Entretien demain / bientôt'), tx('Prepare before a scheduled interview.', 'Préparer un entretien planifié.')],
          [tx('Follow-up due', 'Relance à faire'), tx('Do not miss a planned recruiter follow-up.', 'Ne pas oublier une relance recruteur.')],
          [tx('Application needs attention', 'Candidature à vérifier'), tx('Flags active applications not updated for 10 days.', 'Signale les candidatures actives non mises à jour depuis 10 jours.')],
          [tx('Deadline approaching', 'Échéance proche'), tx('Warns when a calendar deadline is close.', 'Avertit lorsqu’une échéance du calendrier approche.')],
          [tx('Unanalyzed applications', 'Candidatures non analysées'), tx('Reminds you about jobs without an Analyzer score.', 'Rappelle les offres sans score Analyseur.')],
          [tx('Backup reminder', 'Rappel de sauvegarde'), tx('Warns when no recent JAM backup exists.', 'Avertit lorsqu’aucune sauvegarde récente n’existe.')],
          [tx('Upcoming week', 'Semaine à venir'), tx('Summarizes calendar events in the next seven days.', 'Résume les événements des sept prochains jours.')],
          [tx('Search inactivity', 'Inactivité de recherche'), tx('Reminds you when no new application has been saved for three days.', 'Rappelle lorsqu’aucune nouvelle candidature n’a été enregistrée depuis trois jours.')]
        ]),
        note('Every notification type can be switched off individually. The master switch disables all JAM reminders without deleting calendar events or application data.', 'Chaque type de notification peut être désactivé séparément. L’interrupteur principal désactive tous les rappels JAM sans supprimer les événements ni les candidatures.')
      ], 'Settings'),

    article('updates', 'Updates and GitHub Releases', 'Mises à jour et GitHub Releases',
      'How JAM checks for new public versions, downloads verified updates and restarts itself safely.',
      'Comment JAM vérifie les nouvelles versions publiques, télécharge les mises à jour vérifiées et redémarre en sécurité.',
      ['update', 'updates', 'github release', 'new version', 'patch notes', 'sha256', 'installer', 'restart', 'check for updates'], [
        p('JAM checks the official GitHub Releases page automatically about once every 24 hours. A normal Git commit or README change does not count as an app update; JAM looks for a newer tagged GitHub Release.',
          'JAM vérifie automatiquement la page officielle GitHub Releases environ une fois toutes les 24 heures. Un simple commit Git ou une modification du README ne constitue pas une mise à jour de l’application ; JAM recherche une GitHub Release taguée plus récente.'),
        steps('When an update is available', 'Lorsqu’une mise à jour est disponible', [
          tx('JAM shows the new version and its patch notes.', 'JAM affiche la nouvelle version et ses notes de mise à jour.'),
          tx('Choose Download & install to start the verified download.', 'Choisissez Télécharger et installer pour démarrer le téléchargement vérifié.'),
          tx('JAM downloads the Setup EXE with a real progress percentage and verifies its SHA-256 checksum.', 'JAM télécharge le Setup EXE avec un pourcentage réel puis vérifie son empreinte SHA-256.'),
          tx('JAM starts the installer, closes itself and must not be reopened manually while installation is running.', 'JAM démarre l’installateur, se ferme et ne doit pas être relancé manuellement pendant l’installation.'),
          tx('The installer relaunches JAM automatically. The new version then shows a green-check list of what was installed.', 'L’installateur relance automatiquement JAM. La nouvelle version affiche ensuite une liste avec coches vertes des éléments installés.')
        ]),
        note('You can also run a manual check from Settings or About JAM. Automatic installation requires the official JAM Setup EXE and SHA256.txt to be attached to the GitHub Release.',
          'Vous pouvez aussi lancer une vérification manuelle depuis Paramètres ou À propos de JAM. L’installation automatique nécessite le Setup EXE officiel de JAM et le fichier SHA256.txt joints à la GitHub Release.')
      ], 'Settings')
  ];

  function normalize(value) {
    return String(value ?? '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .replace(/[^a-z0-9+#.]+/g, ' ')
      .trim();
  }

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function levenshtein(a, b) {
    if (a === b) return 0;
    if (!a.length) return b.length;
    if (!b.length) return a.length;

    const prev = Array.from({ length: b.length + 1 }, (_, index) => index);
    const next = new Array(b.length + 1);

    for (let i = 1; i <= a.length; i += 1) {
      next[0] = i;
      for (let j = 1; j <= b.length; j += 1) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        next[j] = Math.min(
          next[j - 1] + 1,
          prev[j] + 1,
          prev[j - 1] + cost
        );
      }
      for (let j = 0; j <= b.length; j += 1) prev[j] = next[j];
    }

    return prev[b.length];
  }

  function flattenBlock(block) {
    const chunks = [];
    if (block.title) chunks.push(local(block.title));
    if (block.text) chunks.push(local(block.text));
    if (Array.isArray(block.items)) {
      for (const item of block.items) {
        if (item && typeof item === 'object' && 'label' in item) {
          chunks.push(local(item.label), String(item.value ?? ''));
        } else {
          chunks.push(local(item));
        }
      }
    }
    if (Array.isArray(block.headers)) chunks.push(...block.headers.map(local));
    if (Array.isArray(block.rows)) {
      for (const row of block.rows) chunks.push(...row.map(local));
    }
    return chunks.join(' ');
  }

  function searchText(entry) {
    return normalize([
      local(entry.title),
      local(entry.summary),
      entry.category,
      ...(entry.keywords || []),
      ...(entry.blocks || []).map(flattenBlock)
    ].join(' '));
  }

  function tokenScore(token, haystack, words) {
    if (!token) return 0;
    if (haystack === token) return 120;
    if (haystack.startsWith(token)) return 105;
    if (haystack.includes(` ${token} `) || haystack.endsWith(` ${token}`)) return 95;
    if (haystack.includes(token)) return 80;

    let best = 0;
    for (const word of words) {
      if (!word) continue;
      if (word.startsWith(token) || token.startsWith(word)) best = Math.max(best, 72);
      const limit = token.length <= 4 ? 1 : token.length <= 8 ? 2 : 3;
      const distance = levenshtein(token, word);
      if (distance <= limit) {
        const similarity = 1 - distance / Math.max(token.length, word.length, 1);
        best = Math.max(best, 48 + similarity * 24);
      }
    }
    return best;
  }

  function rankEntry(entry, query) {
    const q = normalize(query);
    if (!q) return 1;

    const title = normalize(local(entry.title));
    const summary = normalize(local(entry.summary));
    const haystack = searchText(entry);
    const words = [...new Set(haystack.split(' ').filter(Boolean))];
    const tokens = q.split(' ').filter(Boolean);

    let score = 0;
    if (title === q) score += 500;
    else if (title.startsWith(q)) score += 320;
    else if (title.includes(q)) score += 230;
    else if (summary.includes(q)) score += 110;

    for (const token of tokens) {
      const tokenBest = tokenScore(token, haystack, words);
      if (!tokenBest) return 0;
      score += tokenBest;
      if (title.split(' ').some(word => word.startsWith(token))) score += 38;
    }

    return score;
  }

  function getResults() {
    const collator = new Intl.Collator(lang() === 'fr' ? 'fr' : 'en', { sensitivity: 'base' });
    const query = currentQuery.trim();

    if (!query) {
      return KB.slice().sort((a, b) => collator.compare(local(a.title), local(b.title)));
    }

    return KB
      .map(entry => ({ entry, score: rankEntry(entry, query) }))
      .filter(item => item.score > 0)
      .sort((a, b) => b.score - a.score || collator.compare(local(a.entry.title), local(b.entry.title)))
      .map(item => item.entry);
  }

  function highlightTitle(title, query) {
    const safeTitle = escapeHtml(title);
    const qTokens = normalize(query).split(' ').filter(Boolean);
    if (!qTokens.length) return safeTitle;

    const rawWords = title.split(/(\s+|[-/.()])/);
    return rawWords.map(part => {
      const normalizedPart = normalize(part);
      if (!normalizedPart) return escapeHtml(part);

      let hit = false;
      for (const token of qTokens) {
        if (normalizedPart.includes(token) || token.includes(normalizedPart)) {
          hit = true;
          break;
        }
        const limit = token.length <= 4 ? 1 : token.length <= 8 ? 2 : 3;
        if (levenshtein(token, normalizedPart) <= limit) {
          hit = true;
          break;
        }
      }
      return hit ? `<mark>${escapeHtml(part)}</mark>` : escapeHtml(part);
    }).join('');
  }

  function renderBlock(block) {
    if (block.type === 'p') {
      return `<p class="guide-article-paragraph">${escapeHtml(local(block.text))}</p>`;
    }

    if (block.type === 'note') {
      return `<div class="guide-note"><span>i</span><p>${escapeHtml(local(block.text))}</p></div>`;
    }

    if (block.type === 'bullets') {
      return `
        <section class="guide-content-block">
          <h3>${escapeHtml(local(block.title))}</h3>
          <ul class="guide-bullets">
            ${(block.items || []).map(item => `<li>${escapeHtml(local(item))}</li>`).join('')}
          </ul>
        </section>`;
    }

    if (block.type === 'steps') {
      return `
        <section class="guide-content-block">
          <h3>${escapeHtml(local(block.title))}</h3>
          <ol class="guide-steps">
            ${(block.items || []).map((item, index) => `
              <li><span>${index + 1}</span><p>${escapeHtml(local(item))}</p></li>`).join('')}
          </ol>
        </section>`;
    }

    if (block.type === 'table') {
      return `
        <section class="guide-content-block">
          <h3>${escapeHtml(local(block.title))}</h3>
          <div class="guide-table-wrap">
            <table class="guide-table">
              <thead><tr>${(block.headers || []).map(cell => `<th>${escapeHtml(local(cell))}</th>`).join('')}</tr></thead>
              <tbody>${(block.rows || []).map(row => `<tr>${row.map(cell => `<td>${escapeHtml(local(cell))}</td>`).join('')}</tr>`).join('')}</tbody>
            </table>
          </div>
        </section>`;
    }

    if (block.type === 'timeline') {
      return `
        <section class="guide-content-block">
          <h3>${escapeHtml(local(block.title))}</h3>
          <div class="guide-timeline">
            ${(block.items || []).map((item, index) => `
              <div class="guide-timeline-item">
                <span>${index + 1}</span>
                <div>${escapeHtml(local(item))}</div>
              </div>`).join('')}
          </div>
        </section>`;
    }

    if (block.type === 'bars') {
      return `
        <section class="guide-content-block">
          <h3>${escapeHtml(local(block.title))}</h3>
          <div class="guide-bars">
            ${(block.items || []).map(item => `
              <div class="guide-bar-row">
                <span>${escapeHtml(local(item.label))}</span>
                <div class="guide-bar-track"><i style="width:${Math.max(0, Math.min(100, Number(item.value) || 0))}%"></i></div>
              </div>`).join('')}
          </div>
        </section>`;
    }

    return '';
  }

  function renderArticle(entry) {
    const listView = $('#guideListView');
    const articleView = $('#guideArticleView');
    if (!listView || !articleView) return;

    currentArticleId = entry.id;
    listView.hidden = true;
    articleView.hidden = false;

    articleView.innerHTML = `
      <button type="button" class="guide-back-btn" data-guide-back>← ${lang() === 'fr' ? 'Retour au guide' : 'Back to Guide'}</button>
      <div class="guide-article-card">
        <div class="guide-article-kicker">${escapeHtml(categoryLabel(entry.category))}</div>
        <h2>${escapeHtml(local(entry.title))}</h2>
        <p class="guide-article-summary">${escapeHtml(local(entry.summary))}</p>
        <div class="guide-article-content">
          ${(entry.blocks || []).map(renderBlock).join('')}
        </div>
      </div>`;

    $('[data-guide-back]', articleView)?.addEventListener('click', () => {
      currentArticleId = null;
      articleView.hidden = true;
      listView.hidden = false;
      $('#guideSearch')?.focus();
    });

    articleView.scrollTop = 0;
  }

  function paginationHtml(totalPages) {
    if (totalPages <= 1) return '';

    const buttons = [];
    for (let page = 1; page <= totalPages; page += 1) {
      buttons.push(`<button type="button" class="guide-page-btn ${page === currentPage ? 'active' : ''}" data-guide-page="${page}">${page}</button>`);
    }

    return `
      <button type="button" class="guide-page-btn" data-guide-page="${Math.max(1, currentPage - 1)}" ${currentPage === 1 ? 'disabled' : ''}>‹</button>
      ${buttons.join('')}
      <button type="button" class="guide-page-btn" data-guide-page="${Math.min(totalPages, currentPage + 1)}" ${currentPage === totalPages ? 'disabled' : ''}>›</button>`;
  }

  function renderResults() {
    const resultsRoot = $('#guideResults');
    const pagination = $('#guidePagination');
    const resultCount = $('#guideResultCount');
    const searchHint = $('#guideSearchHint');
    const clearButton = $('#guideClearSearch');
    const articleCount = $('#guideArticleCount');
    const intro = $('#guideIntro');
    const input = $('#guideSearch');
    if (!resultsRoot || !pagination || !resultCount) return;

    if (input) {
      input.placeholder = lang() === 'fr'
        ? 'Rechercher dans le Guide JAM...'
        : 'Search the JAM Guide...';
    }

    if (intro) {
      intro.textContent = lang() === 'fr'
        ? 'Recherchez des fonctions, flux, fichiers, paramètres, solutions et questions fréquentes.'
        : 'Search features, workflows, files, settings, troubleshooting and common questions.';
    }

    const results = getResults();
    const totalPages = Math.max(1, Math.ceil(results.length / PAGE_SIZE));
    currentPage = Math.min(Math.max(1, currentPage), totalPages);
    const start = (currentPage - 1) * PAGE_SIZE;
    const visible = results.slice(start, start + PAGE_SIZE);

    if (articleCount) {
      articleCount.textContent = `${KB.length} ${lang() === 'fr' ? 'articles' : 'articles'}`;
    }

    if (clearButton) clearButton.hidden = !currentQuery;

    resultCount.textContent = currentQuery
      ? `${results.length} ${lang() === 'fr' ? 'résultat(s)' : 'result(s)'} ${lang() === 'fr' ? 'pour' : 'for'} “${currentQuery}”`
      : `${KB.length} ${lang() === 'fr' ? 'articles de A à Z' : 'articles A–Z'}`;

    if (searchHint) {
      searchHint.textContent = currentQuery
        ? (lang() === 'fr' ? 'Recherche instantanée avec tolérance aux fautes de frappe.' : 'Live typo-tolerant search across the JAM knowledge base.')
        : (lang() === 'fr' ? 'Recherchez une fonction, une question, un fichier, un réglage ou une action.' : 'Search a feature, question, file type, setting or action.');
    }

    if (!visible.length) {
      resultsRoot.innerHTML = `
        <div class="guide-no-results">
          <strong>${lang() === 'fr' ? 'Aucun résultat' : 'No results found'}</strong>
          <p>${lang() === 'fr' ? 'Essayez un mot plus court ou une autre formulation. La recherche accepte aussi les fautes proches.' : 'Try a shorter word or another phrase. Close typos are accepted too.'}</p>
        </div>`;
      pagination.innerHTML = '';
      return;
    }

    resultsRoot.innerHTML = visible.map(entry => `
      <button type="button" class="guide-result" data-guide-article="${escapeHtml(entry.id)}">
        <span class="guide-result-title">${highlightTitle(local(entry.title), currentQuery)}</span>
        <span class="guide-result-summary">${escapeHtml(local(entry.summary))}</span>
        <span class="guide-result-meta">${escapeHtml(categoryLabel(entry.category))} · ${lang() === 'fr' ? 'Ouvrir l’article' : 'Open article'} →</span>
      </button>`).join('');

    pagination.innerHTML = paginationHtml(totalPages);

    $$('[data-guide-article]', resultsRoot).forEach(button => {
      button.addEventListener('click', () => {
        const entry = KB.find(item => item.id === button.dataset.guideArticle);
        if (entry) renderArticle(entry);
      });
    });

    $$('[data-guide-page]', pagination).forEach(button => {
      button.addEventListener('click', () => {
        const page = Number(button.dataset.guidePage || 1);
        if (!Number.isFinite(page)) return;
        currentPage = page;
        renderResults();
        $('#guideListView')?.scrollTo({ top: 0, behavior: 'smooth' });
      });
    });
  }

  function renderGuide() {
    const page = $('#guidePage');
    if (!page) return;

    const tutorialButton = $('#guideTutorialBtn');
    if (tutorialButton) {
      tutorialButton.textContent = lang() === 'fr'
        ? '▶ Lire le tutoriel'
        : '▶ Play tutorial';
    }

    const input = $('#guideSearch');
    if (input && input.value !== currentQuery) input.value = currentQuery;

    const articleView = $('#guideArticleView');
    const listView = $('#guideListView');
    if (currentArticleId) {
      const entry = KB.find(item => item.id === currentArticleId);
      if (entry) {
        renderArticle(entry);
        return;
      }
    }

    if (articleView) articleView.hidden = true;
    if (listView) listView.hidden = false;
    renderResults();
  }

  function bindGuide() {
    const input = $('#guideSearch');
    const clearButton = $('#guideClearSearch');
    if (!input || input.dataset.guideBound === '1') return;

    input.dataset.guideBound = '1';
    input.addEventListener('input', () => {
      currentQuery = input.value;
      currentPage = 1;
      currentArticleId = null;
      $('#guideArticleView').hidden = true;
      $('#guideListView').hidden = false;
      renderResults();
    });

    input.addEventListener('keydown', event => {
      if (event.key === 'Escape' && input.value) {
        input.value = '';
        currentQuery = '';
        currentPage = 1;
        renderResults();
      }

      if (event.key === 'Enter') {
        const first = $('#guideResults [data-guide-article]');
        first?.click();
      }
    });

    clearButton?.addEventListener('click', () => {
      input.value = '';
      currentQuery = '';
      currentPage = 1;
      currentArticleId = null;
      renderResults();
      input.focus();
    });
  }

  function patchNavigation() {
    if (typeof window.navigate !== 'function' || window.navigate.__jamGuidePatched) return;

    const original = window.navigate;
    const patched = function (page) {
      const result = original(page);
      if (page === 'guide') {
        bindGuide();
        renderGuide();
      }
      return result;
    };

    patched.__jamGuidePatched = true;
    window.navigate = patched;
    try { navigate = patched; } catch (_) {}
  }

  function init() {
    bindGuide();
    patchNavigation();

    document.querySelector('[data-page="guide"]')?.addEventListener('click', () => {
      window.setTimeout(() => {
        bindGuide();
        renderGuide();
      }, 0);
    });

    renderGuide();
  }

  // Keep the Guide synchronized when JAM switches between English and French.
  const languageObserver = new MutationObserver(() => {
    currentPage = 1;
    renderGuide();
  });
  languageObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['lang']
  });

  window.renderGuide = renderGuide;
  window.JAM_GUIDE = {
    articleCount: KB.length,
    render: renderGuide
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
