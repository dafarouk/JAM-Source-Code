(() => {
  'use strict';

  // ============================================================
  // JAM UI LANGUAGE LAYER
  // English stays JAM's canonical internal language.
  // Only user-visible content is translated.
  // ============================================================

  const LANGUAGE_SETTING_KEY = 'language';

  const SUPPORTED_LANGUAGES = new Set([
    'en',
    'fr'
  ]);

  let currentLanguage = 'en';
  let applyingTranslations = false;
  let initialized = false;

  const originalText = new WeakMap();
  const originalAttributes = new WeakMap();

  // ============================================================
  // FRENCH TRANSLATIONS
  // ============================================================

  const FR = {
    // ----------------------------------------------------------
    // Navigation
    // ----------------------------------------------------------

    'Dashboard': 'Tableau de bord',
    'Applications': 'Candidatures',
    'Pipeline': 'Pipeline',
    'Analyzer': 'Analyseur',
    'Exports': 'Exports',
    'Settings': 'Paramètres',
    'Guide': 'Guide',
    '▶ Play tutorial': '▶ Lire le tutoriel',
    'Recent Projects': 'Projets récents',
    'Contact': 'Contact',
    'About JAM': 'À propos de JAM',
    'Local-first • Private • Windows': 'Local • Privé • Windows',
    '♥ Support JAM': '♥ Soutenir JAM',
    'Import Excel': 'Importer Excel',
    'Open .jam': 'Ouvrir .jam',
    'Save .jam': 'Enregistrer .jam',
    'Capture Mode': 'Mode Capture',

    // ----------------------------------------------------------
    // Page headers
    // ----------------------------------------------------------

    'JOB SEARCH COMMAND CENTER': 'CENTRE DE PILOTAGE DE RECHERCHE D’EMPLOI',
    'TRACKING': 'SUIVI',
    'STATUS FLOW': 'FLUX DES STATUTS',
    'LOCAL CV MATCH': 'CORRESPONDANCE CV LOCALE',
    'FILES & HISTORY': 'FICHIERS ET HISTORIQUE',
    'PREFERENCES & DATA': 'PRÉFÉRENCES ET DONNÉES',
    'FAST CAPTURE': 'CAPTURE RAPIDE',
    'LOCAL MATCH ENGINE': 'MOTEUR DE CORRESPONDANCE LOCAL',
    'RECENT ACTIVITY': 'ACTIVITÉ RÉCENTE',
    'EXPORT HISTORY': 'HISTORIQUE DES EXPORTS',
    'CV SOURCE': 'SOURCE DU CV',
    'ANALYZER': 'ANALYSEUR',
    'DATA SAFETY': 'SÉCURITÉ DES DONNÉES',
    'DANGER ZONE': 'ZONE DANGEREUSE',
    'GUIDE': 'GUIDE',
    'APPLICATION TRENDS': 'TENDANCES DES CANDIDATURES',
    'Analytics': 'Statistiques',
    'Calendar': 'Calendrier',
    'Job search analytics': 'Statistiques de recherche',
    'See how your application activity changes over time using your own JAM data.':
      'Suivez l’évolution de vos candidatures à partir de vos propres données JAM.',
    'From': 'Du',
    'To': 'Au',
    'All data': 'Toutes les données',
    '30 days': '30 jours',
    '90 days': '90 jours',
    'Tracked': 'Suivies',
    'Saved in selected period': 'Enregistrées sur la période sélectionnée',
    'Analyzed jobs only': 'Offres analysées uniquement',
    'Active interviews': 'Entretiens actifs',
    'Current status': 'Statut actuel',
    'TREND': 'TENDANCE',
    'Applications over time': 'Candidatures dans le temps',
    'SOURCES': 'SOURCES',
    'Where applications come from': 'Origine des candidatures',
    'STATUS MIX': 'RÉPARTITION DES STATUTS',
    'Current application outcomes': 'État actuel des candidatures',
    'PLANNER': 'PLANNING',
    'Application calendar': 'Calendrier des candidatures',
    'See applications by date and keep interviews, follow-ups and deadlines in one place.':
      'Visualisez vos candidatures par date et centralisez entretiens, relances et échéances.',
    'Today': 'Aujourd’hui',
    '+ Add event': '+ Ajouter un événement',
    'SELECTED DAY': 'JOUR SÉLECTIONNÉ',
    'UPCOMING': 'À VENIR',
    'Next events': 'Prochains événements',
    'NOTIFICATIONS': 'NOTIFICATIONS',
    'Notification preferences': 'Préférences de notification',
    'Keep useful reminders on, or disable any notification type you do not want.':
      'Gardez les rappels utiles actifs ou désactivez les types de notification dont vous ne voulez pas.',
    'Enable JAM notifications': 'Activer les notifications JAM',
    'Master switch for reminder alerts and the notification badge.':
      'Interrupteur principal pour les rappels et le badge de notifications.',
    'Interview tomorrow': 'Entretien demain',
    'Remind me about interviews roughly one day ahead.':
      'Me rappeler les entretiens environ un jour à l’avance.',
    'Interview soon': 'Entretien bientôt',
    'Remind me when an interview is about one hour away.':
      'Me rappeler lorsqu’un entretien est prévu dans environ une heure.',
    'Follow-up due': 'Relance à faire',
    'Alert me when a follow-up event is due or recently overdue.':
      'M’alerter lorsqu’une relance est à faire ou récemment dépassée.',
    'Application needs attention': 'Candidature à vérifier',
    'Flag active applications not updated for 10 days.':
      'Signaler les candidatures actives non mises à jour depuis 10 jours.',
    'Deadline approaching': 'Échéance proche',
    'Alert me when a saved deadline is close.':
      'M’alerter lorsqu’une échéance enregistrée approche.',
    'Unanalyzed applications': 'Candidatures non analysées',
    'Show a reminder when saved jobs still have no Analyzer score.':
      'Afficher un rappel lorsque des offres enregistrées n’ont pas encore de score Analyseur.',
    'Backup reminder': 'Rappel de sauvegarde',
    'Warn me when no recent JAM backup exists.':
      'M’avertir lorsqu’aucune sauvegarde JAM récente n’existe.',
    'Upcoming week': 'Semaine à venir',
    'Summarize interviews, follow-ups and deadlines in the next 7 days.':
      'Résumer les entretiens, relances et échéances des 7 prochains jours.',
    'Search inactivity': 'Inactivité de recherche',
    'Remind me if no new application has been saved for 3 days.':
      'Me rappeler si aucune nouvelle candidature n’a été enregistrée depuis 3 jours.',
    'Save notification settings': 'Enregistrer les notifications',
    'Notifications': 'Notifications',
    'JAM UPDATE': 'MISE À JOUR JAM',
    'Updates': 'Mises à jour',
    'JAM checks GitHub Releases automatically about once every 24 hours. You can also check manually at any time.':
      'JAM vérifie automatiquement les GitHub Releases environ une fois toutes les 24 heures. Vous pouvez aussi vérifier manuellement à tout moment.',
    'Installed version': 'Version installée',
    'Check for Updates': 'Rechercher des mises à jour',

    // ----------------------------------------------------------
    // Dashboard
    // ----------------------------------------------------------

    'Track the next opportunity without breaking your flow.':
      'Suivez la prochaine opportunité sans interrompre votre rythme.',

    'Pin JAM over LinkedIn, Indeed or any job board, capture the role, save it, and move on.':
      'Épinglez JAM au-dessus de LinkedIn, Indeed ou de n’importe quel site d’emploi, capturez l’offre, enregistrez-la et continuez.',

    'Open Capture Mode': 'Ouvrir le mode Capture',
    'Add Job': 'Ajouter une offre',
    'Analyze when you need it.': 'Analysez quand vous en avez besoin.',

    'Compare the job against your selected CV. No cloud AI required.':
      'Comparez l’offre à votre CV sélectionné. Aucune IA cloud requise.',

    'Open Analyzer': 'Ouvrir l’analyseur',
    'Total tracked': 'Total suivi',
    'All opportunities saved in JAM': 'Toutes les opportunités enregistrées dans JAM',
    'Applied': 'Candidature envoyée',
    'Applications sent': 'Candidatures envoyées',
    'Interviewing': 'Entretien',
    'Currently active': 'Actuellement actives',
    'Offers / Accepted': 'Offres / Acceptées',
    'Positive outcomes': 'Résultats positifs',
    'Rejected': 'Refusée',
    'Closed applications': 'Candidatures clôturées',
    'Average / day': 'Moyenne / jour',
    'Tracking pace': 'Rythme de suivi',
    'Avg. match': 'Correspondance moy.',
    'Analyzed roles only': 'Offres analysées uniquement',
    'Latest opportunities': 'Dernières opportunités',
    'View all →': 'Tout voir →',

    'Nothing tracked yet. Add a job or open Capture Mode.':
      'Aucune candidature suivie pour le moment. Ajoutez une offre ou ouvrez le mode Capture.',

    // ----------------------------------------------------------
    // Applications
    // ----------------------------------------------------------

    '+ Add Job': '+ Ajouter une offre',
    'Delete selected': 'Supprimer la sélection',
    'Edit selected': 'Modifier la sélection',
    'Clear filters': 'Effacer les filtres',
    'Export Excel': 'Exporter Excel',
    'Export PDF': 'Exporter PDF',
    'COMPANY': 'ENTREPRISE',
    'JOB TITLE': 'POSTE',
    'STATUS': 'STATUT',
    'SCORE': 'SCORE',
    'LOCATION': 'LOCALISATION',
    'DATE SAVED': 'DATE D’ENREGISTREMENT',
    'SOURCE': 'SOURCE',
    'No jobs yet': 'Aucune offre pour le moment',

    'Add your first opportunity or use Capture Mode while browsing jobs.':
      'Ajoutez votre première opportunité ou utilisez le mode Capture pendant votre recherche.',

    'No jobs match the current filters':
      'Aucune offre ne correspond aux filtres actuels',

    'Change or clear the column filters to show more applications.':
      'Modifiez ou effacez les filtres de colonnes pour afficher plus de candidatures.',

    'All statuses': 'Tous les statuts',
    'Any score': 'Tous les scores',
    'Any date': 'Toutes les dates',
    'No rating': 'Aucune note',
    'No score': 'Aucun score',
    'None': 'Aucun',
    'Select all': 'Tout sélectionner',
    'Clear': 'Effacer',
    'Highest first': 'Plus élevé d’abord',
    'Lowest first': 'Plus faible d’abord',
    'Newest first': 'Plus récent d’abord',
    'Oldest first': 'Plus ancien d’abord',
    'A → Z': 'A → Z',
    'Z → A': 'Z → A',
    'Search values...': 'Rechercher des valeurs...',
    'No values yet.': 'Aucune valeur pour le moment.',
    'Company': 'Entreprise',
    'Job title': 'Poste',
    'Job Title': 'Poste',
    'Date Saved': 'Date d’enregistrement',
    'Add an opportunity, use Capture Mode, or clear the filters.':
      'Ajoutez une opportunité, utilisez le mode Capture ou effacez les filtres.',
    "A backup is a safety copy of JAM's local database. Use it if the database is damaged or you need a safe copy before major changes.":
      'Une sauvegarde est une copie de sécurité de la base locale de JAM. Utilisez-la si la base est endommagée ou avant une modification importante.',
    "Deletes JAM's internal tracked data and settings. Exported files already created on disk are not deleted.":
      'Supprime les données suivies et les paramètres internes de JAM. Les fichiers déjà exportés sur le disque ne sont pas supprimés.',
    'Status': 'Statut',
    'Score': 'Score',
    'Rating': 'Note',
    'Location': 'Localisation',
    'Date saved': 'Date d’enregistrement',
    'Source': 'Source',

    'Filter company': 'Filtrer l’entreprise',
    'Filter job title': 'Filtrer le poste',
    'Filter status': 'Filtrer le statut',
    'Filter score': 'Filtrer le score',
    'Filter rating': 'Filtrer la note',
    'Filter location': 'Filtrer la localisation',
    'Filter month': 'Filtrer le mois',
    'Filter source': 'Filtrer la source',

    // ----------------------------------------------------------
    // Statuses
    // ----------------------------------------------------------

    'Saved': 'Enregistrée',
    'To Review': 'À examiner',
    'Offer': 'Offre reçue',
    'Accepted': 'Acceptée',
    'Withdrawn': 'Retirée',
    'Archived': 'Archivée',

    // ----------------------------------------------------------
    // Add / Edit application
    // ----------------------------------------------------------

    'NEW OPPORTUNITY': 'NOUVELLE OPPORTUNITÉ',
    'EDIT APPLICATION': 'MODIFIER LA CANDIDATURE',
    'Work mode': 'Mode de travail',
    'Onsite': 'Sur site',
    'Hybrid': 'Hybride',
    'Remote': 'Télétravail',
    'Salary text': 'Salaire',
    'Job URL': 'URL de l’offre',
    'Contact name': 'Nom du contact',
    'Contact link': 'Lien du contact',
    'Description': 'Description',
    'Notes': 'Notes',
    'Cancel': 'Annuler',
    'Analyze': 'Analyser',
    'Save application': 'Enregistrer la candidature',
    'Save changes': 'Enregistrer les modifications',
    'CV Match analysis': 'Analyse de correspondance CV',
    'Not analyzed': 'Non analysée',
    'Not analyzed yet': 'Pas encore analysée',
    'No reliable score': 'Aucun score fiable',
    'Application saved.': 'Candidature enregistrée.',
    'Application updated.': 'Candidature mise à jour.',

    'Add at least a company or job title.':
      'Ajoutez au moins une entreprise ou un intitulé de poste.',

    // ----------------------------------------------------------
    // Delete
    // ----------------------------------------------------------

    'CONFIRMATION': 'CONFIRMATION',
    'Delete this job?': 'Supprimer cette candidature ?',
    'Delete selected jobs?': 'Supprimer les candidatures sélectionnées ?',
    'Delete': 'Supprimer',
    'Job deleted.': 'Candidature supprimée.',

    // ----------------------------------------------------------
    // Pipeline
    // ----------------------------------------------------------

    'PIPELINE': 'PIPELINE',
    'Your application flow': 'Votre flux de candidatures',

    'Hold the left mouse button and drag the board to move left, right, up or down.':
      'Maintenez le bouton gauche de la souris et faites glisser le tableau vers la gauche, la droite, le haut ou le bas.',

    'Click and drag to navigate': 'Cliquez et faites glisser pour naviguer',
    'No applications': 'Aucune candidature',

    // ----------------------------------------------------------
    // Analyzer
    // ----------------------------------------------------------

    'Selected CV': 'CV sélectionné',
    'No CV selected yet.': 'Aucun CV sélectionné pour le moment.',
    'No CV selected.': 'Aucun CV sélectionné.',
    'Choose CV': 'Choisir un CV',
    'Analyze a role': 'Analyser une offre',
    'Job description': 'Description de l’offre',
    'Analyze Job': 'Analyser l’offre',
    'JAM MATCH ENGINE': 'MOTEUR DE CORRESPONDANCE JAM',
    'JAM MATCH ENGINE v2': 'MOTEUR DE CORRESPONDANCE JAM v2',
    'Analyzing…': 'Analyse en cours…',
    'Analyzing job offer + CV': 'Analyse de l’offre + du CV',
    'Validating job offer…': 'Validation de l’offre…',
    'Validating job offer': 'Validation de l’offre',
    'Extracting job requirements…': 'Extraction des exigences de l’offre…',
    'Reading selected CV…': 'Lecture du CV sélectionné…',
    'Building CV evidence profile…': 'Construction du profil de preuves du CV…',
    'Comparing job and CV evidence…': 'Comparaison des preuves de l’offre et du CV…',
    'Calculating evidence-based score…': 'Calcul du score basé sur les preuves…',
    'Local analysis. No cloud AI call.': 'Analyse locale. Aucun appel à une IA cloud.',
    'CV MATCH RESULT': 'RÉSULTAT DE CORRESPONDANCE CV',
    'Evidence confidence': 'Confiance des preuves',
    'Evidence-based match': 'Correspondance basée sur les preuves',
    'Insufficient evidence': 'Preuves insuffisantes',
    'Matched skills & tools': 'Compétences et outils correspondants',
    'Missing required / not clearly found': 'Exigences manquantes / non clairement trouvées',
    'Experience': 'Expérience',
    'Languages': 'Langues',
    'Matched': 'Correspondances',
    'Missing / not found': 'Manquantes / non trouvées',
    'Responsibilities / domain evidence': 'Responsabilités / preuves métier',
    'Critical domain evidence': 'Preuves métier essentielles',
    'Salary detected': 'Salaire détecté',
    'Why JAM did not score this': 'Pourquoi JAM n’a pas attribué de score',
    'What to review': 'Points à revoir',
    'Done': 'Terminé',
    'None detected': 'Aucun élément détecté',
    'No explicit experience minimum detected.': 'Aucune expérience minimale explicite détectée.',
    'No reliable salary detected.': 'Aucun salaire fiable détecté.',
    'No specific changes suggested.': 'Aucune modification spécifique suggérée.',
    'Very strong evidence': 'Preuves très fortes',
    'Strong evidence': 'Preuves fortes',
    'Moderate evidence': 'Preuves modérées',
    'Partial evidence': 'Preuves partielles',
    'Low evidence': 'Preuves faibles',

    'The job offer is not detailed enough to score reliably.':
      'L’offre n’est pas assez détaillée pour calculer un score fiable.',

    'The CV could not be parsed reliably.':
      'Le CV n’a pas pu être analysé de manière fiable.',

    'Fewer than two reliable comparison dimensions were detected.':
      'Moins de deux dimensions de comparaison fiables ont été détectées.',

    'No positive match evidence was found between the job offer and the CV.':
      'Aucune preuve positive de correspondance n’a été trouvée entre l’offre et le CV.',

    'The evidence confidence is too low for a meaningful percentage score.':
      'La confiance des preuves est trop faible pour produire un pourcentage pertinent.',

    'No explicitly required skill was found in the CV.':
      'Aucune compétence explicitement requise n’a été trouvée dans le CV.',

    'Less than half of the explicitly required skills were found.':
      'Moins de la moitié des compétences explicitement requises ont été trouvées.',

    'Detected experience is well below the stated requirement.':
      'L’expérience détectée est nettement inférieure à l’exigence annoncée.',

    'Core profession-specific requirements from the job description are not evidenced in the CV.':
      'Les exigences essentielles propres au métier ne sont pas démontrées dans le CV.',

    'The target profession and its core domain evidence are both absent from the CV.':
      'Le métier ciblé et ses compétences métier essentielles sont absents du CV.',

    'Most profession-specific requirements are not evidenced in the CV.':
      'La plupart des exigences propres au métier ne sont pas démontrées dans le CV.',

    'Several profession-specific requirements are missing from the CV.':
      'Plusieurs exigences propres au métier sont absentes du CV.',

    'The target role is not strongly reflected in the CV headline/job-title evidence. If accurate, align the profile/headline with the target role rather than inventing experience.':
      'Le poste ciblé n’est pas clairement reflété dans le titre ou le profil du CV. Si cela correspond réellement à votre expérience, alignez le profil avec le poste ciblé sans inventer d’expérience.',

    'CV extraction confidence is limited. Check that the PDF/DOCX contains selectable text and that dates, skills and languages are written explicitly.':
      'La confiance d’extraction du CV est limitée. Vérifiez que le PDF/DOCX contient du texte sélectionnable et que les dates, compétences et langues sont indiquées explicitement.',

    'The detected requirements are well represented. Review each claim against your real experience before tailoring the CV.':
      'Les exigences détectées sont bien représentées. Vérifiez chaque élément par rapport à votre expérience réelle avant d’adapter le CV.',

    // ----------------------------------------------------------
    // Exports
    // ----------------------------------------------------------

    'Generated files': 'Fichiers générés',
    'Open export folder': 'Ouvrir le dossier des exports',
    'No exports yet.': 'Aucun export pour le moment.',
    'Open': 'Ouvrir',
    'EXPORT COMPLETE': 'EXPORT TERMINÉ',
    'Excel file created': 'Fichier Excel créé',
    'PDF file created': 'Fichier PDF créé',
    'Your JAM export is ready.': 'Votre export JAM est prêt.',
    'Close': 'Fermer',
    'Open folder': 'Ouvrir le dossier',
    'Open file now': 'Ouvrir le fichier',

    // ----------------------------------------------------------
    // Settings
    // ----------------------------------------------------------

    'CV & salary target': 'CV et objectif salarial',
    'Salary currency': 'Devise du salaire',
    'Target salary min': 'Salaire cible min.',
    'Target salary max': 'Salaire cible max.',
    'Annual gross target min': 'Objectif salaire brut annuel min.',
    'Annual gross target max': 'Objectif salaire brut annuel max.',
    'Salary converter': 'Convertisseur de salaire',
    'Real-time estimate': 'Estimation en temps réel',
    'Monthly net': 'Net mensuel',
    'Monthly gross': 'Brut mensuel',
    'Annual net': 'Net annuel',
    'Annual gross': 'Brut annuel',
    'Estimate only. JAM uses net ≈ 78% of gross for quick comparison. Actual gross/net amounts vary by country, contract, taxes and deductions.':
      'Estimation uniquement. JAM utilise net ≈ 78 % du brut pour une comparaison rapide. Les montants brut/net réels varient selon le pays, le contrat, les impôts et les cotisations.',
    'Save settings': 'Enregistrer les paramètres',
    'Backup & diagnostics': 'Sauvegarde et diagnostics',

    "A backup is a safety copy of JAM's local database. Use it if the database is damaged or you need a safe copy before major changes.":
      'Une sauvegarde est une copie de sécurité de la base locale de JAM. Utilisez-la si la base est endommagée ou avant une modification importante.',

    'Backup folder:': 'Dossier de sauvegarde :',
    'Windows local app data': 'Données locales de l’application Windows',
    'Create Backup': 'Créer une sauvegarde',
    'Open Backup Folder': 'Ouvrir le dossier des sauvegardes',
    'View Logs': 'Voir les journaux',
    'Reset JAM': 'Réinitialiser JAM',

    "Deletes JAM's internal tracked data and settings. Exported files already created on disk are not deleted.":
      'Supprime les données suivies et les paramètres internes de JAM. Les fichiers déjà exportés sur le disque ne sont pas supprimés.',

    'Reset all JAM data': 'Réinitialiser toutes les données JAM',
    'Settings saved.': 'Paramètres enregistrés.',

    // ----------------------------------------------------------
    // Language
    // ----------------------------------------------------------

    'LANGUAGE': 'LANGUE',
    'Language': 'Langue',

    'Choose the interface language. The change is applied immediately across JAM.':
      'Choisissez la langue de l’interface. Le changement est appliqué immédiatement dans tout JAM.',

    'English': 'English',
    'French': 'Français',
    'Français': 'Français',

    // ----------------------------------------------------------
    // Reset
    // ----------------------------------------------------------

    'Reset all JAM data?': 'Réinitialiser toutes les données JAM ?',

    "Are you sure? All tracked JAM applications, settings, recent-project history and export history inside JAM will be gone.":
      'Êtes-vous sûr ? Toutes les candidatures suivies, les paramètres, l’historique des projets récents et l’historique des exports de JAM seront supprimés.',

    "Yes, I'm sure": 'Oui, je suis sûr',
    'FINAL RESET WARNING': 'DERNIER AVERTISSEMENT',
    'Last chance to cancel': 'Dernière chance d’annuler',

    'JAM will reset automatically when the countdown reaches zero.':
      'JAM sera réinitialisé automatiquement lorsque le compte à rebours atteindra zéro.',

    'Cancel reset': 'Annuler la réinitialisation',
    'Reset cancelled.': 'Réinitialisation annulée.',
    'JAM data reset complete.': 'Réinitialisation des données JAM terminée.',

    // ----------------------------------------------------------
    // Projects
    // ----------------------------------------------------------

    'PROJECTS': 'PROJETS',
    'No recent .jam projects yet.': 'Aucun projet .jam récent.',
    'Open another JAM project?': 'Ouvrir un autre projet JAM ?',

    'Opening a .jam project replaces the current in-app dataset. Save the current project first if needed.':
      'L’ouverture d’un projet .jam remplace les données actuellement chargées. Enregistrez d’abord le projet actuel si nécessaire.',

    'Open project': 'Ouvrir le projet',
    'Replace current data?': 'Remplacer les données actuelles ?',

    'Opening this project replaces the current in-app dataset.':
      'L’ouverture de ce projet remplace les données actuellement chargées.',

    // ----------------------------------------------------------
    // Support / About / Contact
    // ----------------------------------------------------------

    'SUPPORT': 'SOUTIEN',
    'Support JAM': 'Soutenir JAM',

    'JAM is completely free. If the app helps you, any little support would be genuinely appreciated :)':
      'JAM est entièrement gratuit. Si l’application vous aide, le moindre soutien serait sincèrement apprécié :)',

    '✓ Always free to use': '✓ Toujours gratuit',
    'PayPal': 'PayPal',
    'Ko-fi': 'Ko-fi',
    'CONTACT DEVELOPER': 'CONTACTER LE DÉVELOPPEUR',

    'For feedback, bugs, ideas or project information, use the official website or developer GitHub.':
      'Pour vos retours, bugs, idées ou informations sur le projet, utilisez le site officiel ou le GitHub du développeur.',

    'Website': 'Site web',
    'ABOUT JAM': 'À PROPOS DE JAM',
    'MADE BY FAROUK': 'CRÉÉ PAR FAROUK',

    'A local-first Windows job application manager by Farouk.':
      'Un gestionnaire de candidatures Windows local-first créé par Farouk.',

    'Version': 'Version',

    'Track opportunities, capture jobs while browsing, manage your pipeline, export clean reports and compare roles with your CV locally.':
      'Suivez vos opportunités, capturez des offres pendant votre navigation, gérez votre pipeline, exportez des rapports propres et comparez localement les postes à votre CV.',

    // ----------------------------------------------------------
    // Logs
    // ----------------------------------------------------------

    'DIAGNOSTICS': 'DIAGNOSTICS',
    'JAM Logs': 'Journaux JAM',
    'Copy logs': 'Copier les journaux',
    'Logs copied.': 'Journaux copiés.',
    'Success': 'Succès',
    'Warning': 'Avertissement',
    'Error': 'Erreur',
    'Information': 'Information',

    // ----------------------------------------------------------
    // Guide
    // ----------------------------------------------------------

    'JAM Guide': 'Guide JAM',

    // ----------------------------------------------------------
    // Capture legacy web UI
    // ----------------------------------------------------------

    'QUICK CAPTURE': 'CAPTURE RAPIDE',
    '● PINNED': '● ÉPINGLÉ',
    'Top right': 'En haut à droite',
    'Top left': 'En haut à gauche',
    'Bottom right': 'En bas à droite',
    'Bottom left': 'En bas à gauche',
    'Save & Clear': 'Enregistrer et vider',
    'Quick note...': 'Note rapide...',
    'Paste job description...': 'Collez la description de l’offre...',
    'Paste the full job description...': 'Collez la description complète de l’offre...',

    // ----------------------------------------------------------
    // Foundation / safety (Batch 1)
    // ----------------------------------------------------------

    'Show archived': 'Afficher les archivées',
    'Hide archived': 'Masquer les archivées',
    'RECOVERY': 'RÉCUPÉRATION',
    'Unsaved job draft found': 'Brouillon d’offre non enregistré trouvé',
    'JAM recovered an unsaved Add Job form from your previous session.':
      'JAM a récupéré un formulaire d’ajout d’offre non enregistré depuis votre session précédente.',
    'Recovered': 'Récupéré',
    'Discard draft': 'Supprimer le brouillon',
    'Restore draft': 'Restaurer le brouillon',
    'UNSAVED PROJECT': 'PROJET NON ENREGISTRÉ',
    'Save .jam changes first?': 'Enregistrer d’abord les modifications .jam ?',
    'The active .jam project has changes that are not written to the project file yet.':
      'Le projet .jam actif contient des modifications qui ne sont pas encore enregistrées dans le fichier du projet.',
    'Continue without saving': 'Continuer sans enregistrer',
    'Save & continue': 'Enregistrer et continuer',
    'Project changes saved.': 'Modifications du projet enregistrées.',
    'PROJECT RECOVERY': 'RÉCUPÉRATION DU PROJET',
    'Recovered .jam changes found': 'Modifications .jam récupérées',
    'JAM found an autosaved recovery copy from an interrupted .jam project session.':
      'JAM a trouvé une copie de récupération enregistrée automatiquement après l’interruption d’une session de projet .jam.',
    'Project': 'Projet',
    'Discard recovery': 'Supprimer la récupération',
    'Restore recovered changes': 'Restaurer les modifications récupérées',
    'Recovered project changes restored.': 'Modifications récupérées du projet restaurées.',
    'BACKUP RESTORE': 'RESTAURATION DE SAUVEGARDE',
    'Restore a JAM backup': 'Restaurer une sauvegarde JAM',
    'Restore': 'Restaurer',
    'Restore Backup': 'Restaurer une sauvegarde',
    'No JAM backups are available yet.': 'Aucune sauvegarde JAM disponible pour le moment.',
    'Restore this backup?': 'Restaurer cette sauvegarde ?',
    'JAM will create a safety backup of the current database first, then replace the live database with the selected backup.':
      'JAM créera d’abord une sauvegarde de sécurité de la base actuelle, puis remplacera la base active par la sauvegarde sélectionnée.',
    'Restore backup': 'Restaurer la sauvegarde',
    'Backup restored.': 'Sauvegarde restaurée.',
    'DATA LOCATIONS': 'EMPLACEMENTS DES DONNÉES',
    'Where JAM stores your files': 'Où JAM stocke vos fichiers',
    'These locations are local to your PC. Click Open to jump directly to a folder.':
      'Ces emplacements sont locaux à votre PC. Cliquez sur Ouvrir pour accéder directement au dossier.',
    'For the best organization, keeping JAM data in the default locations is recommended, but you are free to choose a different folder for each item. Existing data is copied and the new path is used after restarting JAM.':
      'Pour une meilleure organisation, il est recommandé de conserver les emplacements par défaut de JAM, mais vous êtes libre de choisir un dossier différent pour chaque élément. Les données existantes sont copiées et le nouveau chemin est utilisé après le redémarrage de JAM.',
    'Edit': 'Modifier',
    'DATA LOCATION UPDATED': 'EMPLACEMENT MIS À JOUR',
    'Restart JAM to apply the new path': 'Redémarrez JAM pour appliquer le nouveau chemin',
    'JAM copied the existing data to the selected folder. The current session keeps using the old path; restart JAM to switch safely to the new location.':
      'JAM a copié les données existantes vers le dossier sélectionné. La session actuelle continue d’utiliser l’ancien chemin ; redémarrez JAM pour basculer en toute sécurité vers le nouvel emplacement.',
    'Database': 'Base de données',
    'Backups': 'Sauvegardes',
    'Projects': 'Projets',
    'Logs': 'Journaux',
    'Recovery': 'Récupération',
    'Run Diagnostics': 'Lancer les diagnostics',
    'JAM looks healthy': 'JAM fonctionne correctement',
    'JAM diagnostics found something to review': 'Les diagnostics JAM ont détecté un élément à vérifier',
    'Core checks passed': 'Vérifications principales réussies',
    'Review the checks below': 'Vérifiez les éléments ci-dessous',
    'errors': 'erreur(s)',
    'warnings': 'avertissement(s)',
    'Installed package versions': 'Versions des composants installés',
    'Copy diagnostics': 'Copier les diagnostics',
    'Diagnostics copied.': 'Diagnostics copiés.',
    'Local database': 'Base de données locale',
    'JAM data folder': 'Dossier de données JAM',
    'Exports folder': 'Dossier des exports',
    'Backups folder': 'Dossier des sauvegardes',
    'Projects folder': 'Dossier des projets',
    'Logs folder': 'Dossier des journaux',
    'Recovery folder': 'Dossier de récupération',
    'Offline currency flags': 'Drapeaux de devises hors ligne',
    'Selected CV': 'CV sélectionné',
    'Microsoft Edge WebView2 Runtime': 'Microsoft Edge WebView2 Runtime',
    'Python runtime': 'Environnement Python',
    'No CV selected. Tracking still works; analysis requires a CV.':
      'Aucun CV sélectionné. Le suivi fonctionne toujours ; l’analyse nécessite un CV.',
    'The saved CV path no longer exists.': 'Le chemin du CV enregistré n’existe plus.',
    'Windows-only check. It will be verified on the Windows PC running JAM.':
      'Vérification Windows uniquement. Elle sera effectuée sur le PC Windows exécutant JAM.',
    'Runtime version could not be read from the Windows registry. If JAM is open, WebView2 is already usable.':
      'La version du runtime n’a pas pu être lue dans le registre Windows. Si JAM est ouvert, WebView2 est déjà utilisable.',

    // ----------------------------------------------------------
    // Generic
    // ----------------------------------------------------------

    'Search': 'Rechercher',
    'Sort': 'Tri',
    'ascending': 'croissant',
    'descending': 'décroissant',
    'Manual selection': 'Sélection manuelle',

    'No filters applied — all visible applications.':
      'Aucun filtre appliqué — toutes les candidatures visibles.',

    'No filters applied — all visible applications were exported.':
      'Aucun filtre appliqué — toutes les candidatures visibles ont été exportées.'
,

    '(Blank)': '(Vide)',
    '(Unknown month)': '(Mois inconnu)',
    'Unknown company': 'Entreprise inconnue',
    'Untitled': 'Sans titre',
    'Untitled role': 'Poste sans titre',
    'Delete application': 'Supprimer la candidature',
    'EXCEL IMPORT': 'IMPORT EXCEL',
    'Import complete': 'Import terminé',
    'JAM Activity & Logs': 'Activité et journaux JAM',
    'Could not copy logs.': 'Impossible de copier les journaux.',
    'SUPPORT JAM': 'SOUTENIR JAM',
    'Support the project': 'Soutenir le projet',
    'WELCOME TO JAM': 'BIENVENUE DANS JAM',
    'Add your CV for matching': 'Ajoutez votre CV pour la correspondance',
    'Yes, continue': 'Oui, continuer',
    'JAM backend is not ready yet.': 'Le moteur JAM n’est pas encore prêt.',
    'Unknown JAM error.': 'Erreur JAM inconnue.',
    'The score is based only on comparison dimensions JAM could actually detect.':
      'Le score repose uniquement sur les dimensions de comparaison que JAM a réellement pu détecter.',
    'HELP & LEARNING': 'AIDE & APPRENTISSAGE',
    'Other': 'Autre',
    'Opened': 'Ouvert :',
    'Applications imported': 'Candidatures importées',
    'Rows skipped': 'Lignes ignorées',
    'Columns detected': 'Colonnes détectées',
    'JAM matched columns by their header names, so the Excel column order did not matter.':
      'JAM a associé les colonnes grâce à leurs en-têtes ; leur ordre dans Excel n’a donc pas d’importance.',
    'JAM is free to use. If it helps you, you can support future development directly.':
      'JAM est gratuit. S’il vous aide, vous pouvez soutenir directement son développement futur.',
    '✓ green means a normal successful action, ⚠ orange means something worth checking, and ✕ red means JAM recorded an error. Most users only need to look at red entries.':
      '✓ vert indique une action réussie, ⚠ orange signale un élément à vérifier et ✕ rouge indique qu’une erreur a été enregistrée. La plupart des utilisateurs n’ont besoin de regarder que les entrées rouges.',
    'No log entries yet. JAM is quiet.': 'Aucune entrée de journal pour le moment. Tout est calme.',
    'JAM works as a job tracker without a CV. Adding one now unlocks the optional local CV Match Analyzer.':
      'JAM fonctionne comme gestionnaire de candidatures même sans CV. En ajouter un active l’analyseur local optionnel de correspondance CV.',
    'Skip for now': 'Ignorer pour le moment',
    'Add CV': 'Ajouter un CV',
    'Company careers page': 'Page carrières de l’entreprise',
    'Recruiter / Agency': 'Recruteur / Agence',
    'Referral': 'Cooptation',
    'School / Alumni': 'École / Alumni'
,
    'Backup file does not exist.': 'Le fichier de sauvegarde n’existe pas.',
    'The selected file is not a readable SQLite database.': 'Le fichier sélectionné n’est pas une base SQLite lisible.',
    'JAM database does not exist yet.': 'La base de données JAM n’existe pas encore.',
    'JAM can only restore files from its backup folder.': 'JAM ne peut restaurer que des fichiers provenant de son dossier de sauvegardes.',
    'Application not found.': 'Candidature introuvable.',
    'JAM main window is not ready.': 'La fenêtre principale de JAM n’est pas encore prête.',
    'The selected CV file no longer exists.': 'Le fichier CV sélectionné n’existe plus.',
    'Add a job title or description before analyzing.': 'Ajoutez un poste ou une description avant de lancer l’analyse.',
    'Add a CV first from JAM settings or the analyzer.': 'Ajoutez d’abord un CV depuis les paramètres JAM ou l’analyseur.',
    'JAM could not extract readable text from the selected CV.': 'JAM n’a pas pu extraire de texte lisible du CV sélectionné.',
    'JAM could not identify enough known columns in this Excel file.': 'JAM n’a pas pu identifier suffisamment de colonnes connues dans ce fichier Excel.',
    'Excel file not found.': 'Fichier Excel introuvable.',
    'Invalid recovery draft name.': 'Nom de brouillon de récupération invalide.',
    'This file is not a valid JAM project.': 'Ce fichier n’est pas un projet JAM valide.',
    'No active .jam project to save.': 'Aucun projet .jam actif à enregistrer.',
    'No recovered .jam project changes were found.': 'Aucune modification .jam récupérée n’a été trouvée.',
    'The project recovery file is invalid.': 'Le fichier de récupération du projet est invalide.',

    'Preview CV': 'Prévisualiser le CV',
    'Save analysis': 'Enregistrer l’analyse',
    'ANALYSIS HISTORY': 'HISTORIQUE DES ANALYSES',
    'Saved analyses': 'Analyses enregistrées',
    'No saved analyses yet.': 'Aucune analyse enregistrée pour le moment.',
    'Untitled analysis': 'Analyse sans titre',
    'Open analysis': 'Ouvrir l’analyse',
    'Saved analysis deleted.': 'Analyse enregistrée supprimée.',
    'Analysis saved.': 'Analyse enregistrée.',
    'Analyze a role first.': 'Analysez d’abord une offre.',
    'CV PREVIEW': 'PRÉVISUALISATION DU CV',
    'Selected CV': 'CV sélectionné',
    'Page': 'Page',
    'Role / title alignment': 'Alignement poste / intitulé',
    'Score breakdown': 'Détail du score',
    'Score penalties / hard requirements': 'Pénalités du score / exigences bloquantes',
    'Maximum score after hard-fit checks:': 'Score maximal après vérification des exigences :',
    'CV evidence used': 'Preuves du CV utilisées',
    'Job': 'Offre',
    'CV evidence': 'Preuve du CV',
    'JAM v3 scores title/role fit first, then verifies skills, experience, responsibilities, education and languages against the selected CV.':
      'JAM v3 évalue d’abord l’adéquation du poste et de l’intitulé, puis vérifie les compétences, l’expérience, les responsabilités, la formation et les langues avec le CV sélectionné.',
    'No detailed score breakdown available.': 'Aucun détail du score disponible.',
    'No reliable role evidence detected.': 'Aucune preuve fiable d’alignement du poste détectée.',
    'Within salary target': 'Dans l’objectif salarial',
    'Outside salary target': 'Hors objectif salarial',
    'Job reference': 'Référence de l’offre',
    'Reference': 'Référence',
    'Reference copied.': 'Référence copiée.',
    'Copy': 'Copier',
    'Education': 'Formation',
    'Job requirement': 'Exigence de l’offre',
    'CV evidence': 'Preuve du CV',
    'No specific field detected': 'Aucun domaine d’études spécifique détecté',
    'No matching field found': 'Aucun domaine correspondant trouvé',
    'No explicit experience minimum detected.': 'Aucune expérience minimale explicite détectée.',
    'CV timeline estimate:': 'Estimation de la chronologie du CV :',
    'Required skills & tools': 'Compétences et outils requis',
    'Critical domain evidence': 'Preuves métier essentielles',
    'Relevant experience': 'Expérience pertinente',
    'Responsibilities / domain': 'Responsabilités / domaine',
    'Semantic requirement evidence': 'Preuves sémantiques des exigences',
    'Requirement coverage': 'Couverture des exigences',
    'Statistical role classification': 'Classification statistique du métier',
    'Local ML engine': 'Moteur ML local',
    'Local only — no CV/job text is sent to a cloud service.': 'Local uniquement — aucun texte du CV ou de l’offre n’est envoyé vers un service cloud.',
    'Best CV evidence': 'Meilleure preuve dans le CV',
    'Strong': 'Forte',
    'Partial': 'Partielle',
    'Weak': 'Faible',
    'Missing': 'Absente',
    'Not detected': 'Non détecté',
    'No semantic requirement evidence available.': 'Aucune preuve sémantique des exigences disponible.',
    'local TF-IDF requirement-to-CV evidence similarity': 'similarité TF-IDF locale entre les exigences et les preuves du CV',
    'Local semantic matching found no strong CV evidence for required statements such as:': 'La correspondance sémantique locale n’a trouvé aucune preuve forte dans le CV pour des exigences telles que :',
    'JAM v4 keeps the deterministic hard checks and adds local ML requirement-to-CV evidence matching plus statistical job-family classification.':
      'JAM v4 conserve les contrôles déterministes stricts et ajoute une correspondance ML locale entre exigences et preuves du CV, ainsi qu’une classification statistique de la famille de métier.',
    'JAM v3.2 verifies role fit, required competencies, relevant experience, education field/level, responsibilities and languages against the selected CV.':
      'JAM v3.2 vérifie l’adéquation du poste, les compétences requises, l’expérience pertinente, le domaine et le niveau de formation, les responsabilités et les langues par rapport au CV sélectionné.',
    'Analyzer PDF': 'PDF de l’analyseur',
    'Analyze a role before exporting the Analyzer PDF.': 'Analysez une offre avant d’exporter le PDF de l’analyseur.',
    'technical tools + profession-specific required competency coverage': 'couverture des outils techniques et des compétences métier spécifiques requises',
    'profession-specific evidence from the job description': 'preuves métier spécifiques issues de la description de l’offre',
    'responsibility/domain evidence': 'preuves liées aux responsabilités et au domaine',
    'degree requirement': 'exigence de formation',
    'language requirement': 'exigence linguistique',
    'The requested field of study is not evidenced by the CV education.': 'Le domaine d’études demandé n’est pas démontré par la formation du CV.',
    'Profession-specific job requirements not clearly found in the CV:': 'Exigences métier spécifiques non clairement trouvées dans le CV :',

    // ----------------------------------------------------------
    // Batch 2 — application management
    // ----------------------------------------------------------

    'Details': 'Détails',
    'Bulk update': 'Modification groupée',
    'Save view': 'Enregistrer la vue',
    'Saved views': 'Vues enregistrées',
    'Applied this week': 'Candidatures cette semaine',
    'Score ≥ 70': 'Score ≥ 70',
    '5 stars': '5 étoiles',
    'Not analyzed': 'Non analysées',
    'France': 'France',
    'Tunisia': 'Tunisie',
    'Clear preset': 'Effacer le raccourci',
    'STRUCTURED SALARY': 'SALAIRE STRUCTURÉ',
    'Minimum': 'Minimum',
    'Maximum': 'Maximum',
    'Currency': 'Devise',
    'Period': 'Période',
    'Basis': 'Base',
    'Annual': 'Annuel',
    'Monthly': 'Mensuel',
    'Hourly': 'Horaire',
    'Gross': 'Brut',
    'Net': 'Net',
    'Open job link': 'Ouvrir le lien de l’offre',
    'Open contact link': 'Ouvrir le lien du contact',
    'No link to open.': 'Aucun lien à ouvrir.',
    'POSSIBLE DUPLICATE': 'DOUBLON POSSIBLE',
    'This application may already be tracked.': 'Cette candidature semble déjà être suivie.',
    'possible matches found': 'correspondances possibles trouvées',
    'Open existing': 'Ouvrir l’existante',
    'Save anyway': 'Enregistrer quand même',
    'Salary': 'Salaire',
    'Date applied': 'Date de candidature',
    'Status history': 'Historique des statuts',
    'Analyzer score breakdown': 'Détail du score Analyzer',
    'No status history yet.': 'Aucun historique de statut pour le moment.',
    'No score breakdown saved.': 'Aucun détail de score enregistré.',
    'APPLICATION DETAILS': 'DÉTAILS DE LA CANDIDATURE',
    'Edit application': 'Modifier la candidature',
    'selected applications': 'candidatures sélectionnées',
    'Leave a field blank to keep its current value.': 'Laissez un champ vide pour conserver sa valeur actuelle.',
    'Apply changes': 'Appliquer les modifications',
    'Choose at least one change.': 'Choisissez au moins une modification.',
    'Selected applications updated.': 'Candidatures sélectionnées mises à jour.',
    'Save current view': 'Enregistrer la vue actuelle',
    'Rename saved view': 'Renommer la vue enregistrée',
    'Save': 'Enregistrer',
    'Rename': 'Renommer',
    'View saved.': 'Vue enregistrée.',
    'No saved views yet.': 'Aucune vue enregistrée pour le moment.',
    'SAVED VIEWS': 'VUES ENREGISTRÉES',
    'Rows detected': 'Lignes détectées',
    'Possible duplicates': 'Doublons possibles',
    'Column mapping': 'Correspondance des colonnes',
    'Preview': 'Aperçu',
    'Ignored': 'Ignorée',
    'Duplicate': 'Doublon',
    'Import possible duplicates too': 'Importer aussi les doublons possibles',
    'Excel import preview': 'Aperçu de l’import Excel',
    'Import': 'Importer',
    'Import complete': 'Import terminé',
    'Imported': 'Importées',
    'Blank rows skipped': 'Lignes vides ignorées',
    'Duplicates skipped': 'Doublons ignorés',
    'Rows failed': 'Lignes en échec',
    'Import errors': 'Erreurs d’import',
    'Row': 'Ligne',
    'row(s)': 'ligne(s)',
    'Open folder': 'Ouvrir le dossier',
    'Remove from history': 'Retirer de l’historique',
    'jobs': 'candidatures',
    'Opened': 'Ouvert',
    'Modified': 'Modifié',
    'Available': 'Disponible',
    'Missing file': 'Fichier introuvable',
    'Remove from recent': 'Retirer des récents',
    'Search logs...': 'Rechercher dans les journaux...',
    'All': 'Tous',
    'Info': 'Info',
    'No matching log entries.': 'Aucune entrée de journal correspondante.',
    'JAM Activity & Logs': 'Activité et journaux JAM',
    'Could not copy logs.': 'Impossible de copier les journaux.',

    // ----------------------------------------------------------
    // Batch 3 — richer tracking / capture
    // ----------------------------------------------------------
    'Tracking': 'Suivi enrichi',
    'TRACKING & HISTORY': 'SUIVI & HISTORIQUE',
    'Contacts, notes & attachments': 'Contacts, notes & pièces jointes',
    'Keep multiple contacts, note history and application files together.': 'Gardez plusieurs contacts, l’historique des notes et les fichiers de candidature au même endroit.',
    'Save this application first, then reopen it to add multiple contacts, note history and attachments.': 'Enregistrez d’abord cette candidature, puis rouvrez-la pour ajouter plusieurs contacts, l’historique des notes et des pièces jointes.',
    'Open full tracking': 'Ouvrir le suivi complet',
    'Loading tracking data...': 'Chargement des données de suivi...',
    'Contact added.': 'Contact ajouté.',
    'Contact updated.': 'Contact mis à jour.',
    'Note added.': 'Note ajoutée.',
    'Note updated.': 'Note mise à jour.',
    'APPLICATION TRACKING': 'SUIVI DE CANDIDATURE',
    'CONTACTS': 'CONTACTS',
    'Contacts': 'Contacts',
    'Add contact': 'Ajouter un contact',
    'Edit contact': 'Modifier le contact',
    'Unnamed contact': 'Contact sans nom',
    'No extra contact details': 'Aucune information supplémentaire',
    'Imported primary contact': 'Contact principal importé',
    'Name': 'Nom',
    'Role': 'Fonction',
    'Email': 'E-mail',
    'Phone': 'Téléphone',
    'Link': 'Lien',
    'Note': 'Note',
    'Remove': 'Supprimer',
    'No contacts yet.': 'Aucun contact pour le moment.',
    'NOTES HISTORY': 'HISTORIQUE DES NOTES',
    'Notes history': 'Historique des notes',
    'Add note': 'Ajouter une note',
    'Edit note': 'Modifier la note',
    'Edited': 'Modifiée',
    'No notes yet.': 'Aucune note pour le moment.',
    'ATTACHMENTS': 'PIÈCES JOINTES',
    'Attachments': 'Pièces jointes',
    'Attachment': 'Pièce jointe',
    'Add file': 'Ajouter un fichier',
    'Cover letter': 'Lettre de motivation',
    'Screenshot': 'Capture d’écran',
    'Other': 'Autre',
    'Folder': 'Dossier',
    'File missing': 'Fichier introuvable',
    'No attachments yet.': 'Aucune pièce jointe pour le moment.',
    'Attachments are copied into JAM local storage.': 'Les pièces jointes sont copiées dans le stockage local de JAM.',
    'Attachment added.': 'Pièce jointe ajoutée.',
    'ACTIVITY': 'ACTIVITÉ',
    'CAPTURE MODE': 'MODE CAPTURE',
    'Position, size & shortcuts': 'Position, taille et raccourcis',
    'Capture remembers its exact window position and size on this PC.': 'Capture mémorise sa position et sa taille exactes sur ce PC.',
    'Default position': 'Position par défaut',
    'Top left': 'En haut à gauche',
    'Top right': 'En haut à droite',
    'Bottom left': 'En bas à gauche',
    'Bottom right': 'En bas à droite',
    'Remember exact position and size': 'Mémoriser la position et la taille exactes',
    'Reset saved position & size': 'Réinitialiser la position et la taille enregistrées',
    'Add job': 'Ajouter une offre',
    'Search applications': 'Rechercher les candidatures',
    'Save project': 'Enregistrer le projet',
    'Run Analyzer': 'Lancer l’analyseur',
    'Close dialog': 'Fermer la fenêtre',
    'Keyboard shortcuts work while JAM is focused.': 'Les raccourcis clavier fonctionnent lorsque JAM est actif.',
    'Default Capture position saved.': 'Position par défaut de Capture enregistrée.',
    'Capture preference saved.': 'Préférence Capture enregistrée.',
    'Saved Capture position and size cleared.': 'Position et taille enregistrées de Capture réinitialisées.',
    'Project saved.': 'Projet enregistré.'

  };

  // ============================================================
  // PLACEHOLDERS
  // ============================================================

  const FR_PLACEHOLDERS = {
    'Search company, role, location, source...':
      'Rechercher entreprise, poste, localisation, source...',

    'Search Tunisia, TND, Euro, Dollar...':
      'Rechercher Tunisie, TND, euro, dollar...',

    'Data Analyst':
      'Data Analyst',

    'LinkedIn, Keejob, Welcome to the Jungle...':
      'LinkedIn, Keejob, Welcome to the Jungle...',

    '45k–55k / 3000 TND / etc.':
      '45k–55k / 3000 TND / etc.',

    'Company':
      'Entreprise',

    'Job title':
      'Poste',

    'Paris':
      'Paris',

    'LinkedIn':
      'LinkedIn',

    'https://...':
      'https://...'
  };

  // ============================================================
  // CURRENCIES
  // ============================================================

  const CURRENCY_FR = {
    EUR: {
      name: 'Euro',
      aliases: 'euro euros zone euro france français europe européen'
    },

    USD: {
      name: 'Dollar américain',
      aliases: 'dollar dollars américain etats unis états-unis usa amerique amérique'
    },

    TND: {
      name: 'Dinar tunisien',
      aliases: 'tunisie tunis tunisien tunisienne dinar tunisien'
    },

    MAD: {
      name: 'Dirham marocain',
      aliases: 'maroc marocain marocaine dirham marocain'
    },

    DZD: {
      name: 'Dinar algérien',
      aliases: 'algerie algérie algerien algérien algérienne dinar algérien'
    },

    LYD: {
      name: 'Dinar libyen',
      aliases: 'libye libyen libyenne dinar libyen'
    },

    EGP: {
      name: 'Livre égyptienne',
      aliases: 'egypte égypte egyptien égyptien livre égyptienne'
    },

    SAR: {
      name: 'Riyal saoudien',
      aliases: 'arabie saoudite saoudien riyal saoudien'
    },

    AED: {
      name: 'Dirham des Émirats',
      aliases: 'emirats émirats emirats arabes unis émirats arabes unis eau dubai abu dhabi'
    },

    QAR: {
      name: 'Riyal qatari',
      aliases: 'qatar qatari riyal qatari'
    },

    KWD: {
      name: 'Dinar koweïtien',
      aliases: 'koweit koweït koweitien koweïtien dinar'
    },

    BHD: {
      name: 'Dinar bahreïni',
      aliases: 'bahrein bahreïn bahreini bahreïni dinar'
    },

    OMR: {
      name: 'Rial omanais',
      aliases: 'oman omanais rial'
    },

    JOD: {
      name: 'Dinar jordanien',
      aliases: 'jordanie jordanien dinar'
    },

    LBP: {
      name: 'Livre libanaise',
      aliases: 'liban libanais livre'
    },

    IQD: {
      name: 'Dinar irakien',
      aliases: 'irak iraq irakien dinar'
    },

    TRY: {
      name: 'Livre turque',
      aliases: 'turquie turc turque livre'
    },

    GBP: {
      name: 'Livre sterling',
      aliases: 'royaume uni angleterre britannique livre sterling uk'
    },

    CAD: {
      name: 'Dollar canadien',
      aliases: 'canada canadien dollar canadien'
    },

    CHF: {
      name: 'Franc suisse',
      aliases: 'suisse swiss franc suisse'
    }
  };

  // ============================================================
  // DYNAMIC TRANSLATION RULES
  // ============================================================

  const REGEX_TRANSLATIONS = [
    [
      /^(\d+) selected$/,
      match =>
        `${match[1]} sélectionnée${
          match[1] === '1'
            ? ''
            : 's'
        }`
    ],

    [
      /^(\d+) application\(s\)$/,
      match =>
        `${match[1]} candidature(s)`
    ],

    [
      /^(\d+) row\(s\)$/,
      match =>
        `${match[1]} ligne(s)`
    ],

    [
      /^(\d+) job\(s\) deleted\.$/,
      match =>
        `${match[1]} candidature(s) supprimée(s).`
    ],

    [
      /^CV selected:\s*(.+)$/,
      match =>
        `CV sélectionné : ${match[1]}`
    ],

    [
      /^Backup created:\s*(.+)$/,
      match =>
        `Sauvegarde créée : ${match[1]}`
    ],

    [
      /^Saved\s+(.+)$/,
      match =>
        `Enregistré : ${match[1]}`
    ],

    [
      /^Opened\s+(.+)$/,
      match =>
        `Ouvert : ${match[1]}`
    ],

    [
      /^Excel export created:\s*(.+)$/,
      match =>
        `Export Excel créé : ${match[1]}`
    ],

    [
      /^PDF export created:\s*(.+)$/,
      match =>
        `Export PDF créé : ${match[1]}`
    ],

    [
      /^Filter\s+(.+)$/,
      match =>
        `Filtrer ${translateExact(match[1])}`
    ],

    [
      /^Required tools\/skills not clearly found in the CV:\s*(.+)\.\s*Only add them if they are genuinely part of your experience\.$/,
      match =>
        `Outils/compétences requis non clairement trouvés dans le CV : ${match[1]}. Ajoutez-les uniquement s’ils font réellement partie de votre expérience.`
    ],

    [
      /^Job skills not clearly found in the CV:\s*(.+)\.$/,
      match =>
        `Compétences de l’offre non clairement trouvées dans le CV : ${match[1]}.`
    ],

    [
      /^Requested languages not clearly found in the CV:\s*(.+)\.$/,
      match =>
        `Langues demandées non clairement trouvées dans le CV : ${match[1]}.`
    ],

    [
      /^Responsibilities\/domain concepts not clearly evidenced in the CV:\s*(.+)\.$/,
      match =>
        `Responsabilités/concepts métier non clairement démontrés dans le CV : ${match[1]}.`
    ],

    [
      /^Profession-specific job requirements not clearly found in the CV:\s*(.+)\.$/,
      match =>
        `Exigences propres au métier non clairement trouvées dans le CV : ${match[1]}.`
    ],

    [
      /^The job asks for about\s*(.+)\+\s*years,\s*but JAM could not reliably calculate years of experience from the CV timeline\.$/,
      match =>
        `L’offre demande environ ${match[1]}+ ans, mais JAM n’a pas pu calculer de manière fiable l’expérience à partir de la chronologie du CV.`
    ],

    [
      /^The job asks for about\s*(.+)\+\s*years;\s*JAM detected about\s*(.+)\s*years from the CV timeline\/text\.$/,
      match =>
        `L’offre demande environ ${match[1]}+ ans ; JAM a détecté environ ${match[2]} ans à partir de la chronologie/du texte du CV.`
    ],

    [
      /^Job requirement:\s*about\s*(.+)\+\s*year\(s\)\.$/,
      match =>
        `Exigence de l’offre : environ ${match[1]}+ an(s).`
    ],

    [
      /^CV timeline estimate:\s*(.+)\s*year\(s\)\.$/,
      match =>
        `Estimation de la chronologie du CV : ${match[1]} an(s).`
    ],

    [
      /^Education requirement detected:\s*(.+)$/,
      match =>
        `Exigence de formation détectée : ${match[1]}`
    ]
  ];

  // ============================================================
  // TRANSLATION HELPERS
  // ============================================================

  function translateExact(text) {
    if (currentLanguage !== 'fr') {
      return text;
    }

    if (
      Object.prototype
        .hasOwnProperty
        .call(
          FR,
          text
        )
    ) {
      return FR[text];
    }

    for (
      const [
        pattern,
        replacer
      ]
      of REGEX_TRANSLATIONS
    ) {
      const match =
        text.match(pattern);

      if (match) {
        return replacer(match);
      }
    }

    return text;
  }

  function translatePlaceholder(text) {
    if (currentLanguage !== 'fr') {
      return text;
    }

    return (
      FR_PLACEHOLDERS[text] ||
      translateExact(text)
    );
  }

  function isIgnoredNode(node) {
    const parent =
      node.parentElement;

    return Boolean(
      parent &&
      (
        parent.closest(
          'script, style, code, pre'
        ) ||
        parent.hasAttribute(
          'data-i18n-ignore'
        )
      )
    );
  }

  // ============================================================
  // TEXT NODES
  // ============================================================

  function translateTextNode(
    node,
    forceOriginalUpdate = false
  ) {
    if (
      node.nodeType !==
        Node.TEXT_NODE ||
      isIgnoredNode(node)
    ) {
      return;
    }

    if (
      forceOriginalUpdate ||
      !originalText.has(node)
    ) {
      originalText.set(
        node,
        node.nodeValue
      );
    }

    const original =
      originalText.get(node) ??
      node.nodeValue;

    const trimmed =
      original.trim();

    if (!trimmed) {
      return;
    }

    const translated =
      translateExact(trimmed);

    const leading =
      original.match(
        /^\s*/
      )?.[0] || '';

    const trailing =
      original.match(
        /\s*$/
      )?.[0] || '';

    const next =
      currentLanguage === 'fr'
        ? `${leading}${translated}${trailing}`
        : original;

    if (
      node.nodeValue !== next
    ) {
      applyingTranslations =
        true;

      node.nodeValue =
        next;

      applyingTranslations =
        false;
    }
  }

  // ============================================================
  // ATTRIBUTES
  // ============================================================

  function translateElementAttributes(
    element,
    forceOriginalUpdate = false
  ) {
    if (
      !(element instanceof Element)
    ) {
      return;
    }

    if (
      forceOriginalUpdate ||
      !originalAttributes.has(
        element
      )
    ) {
      originalAttributes.set(
        element,
        {
          placeholder:
            element.getAttribute(
              'placeholder'
            ),

          title:
            element.getAttribute(
              'title'
            ),

          ariaLabel:
            element.getAttribute(
              'aria-label'
            )
        }
      );
    }

    const originals =
      originalAttributes.get(
        element
      );

    applyingTranslations =
      true;

    if (
      originals.placeholder !== null
    ) {
      element.setAttribute(
        'placeholder',
        currentLanguage === 'fr'
          ? translatePlaceholder(
              originals.placeholder
            )
          : originals.placeholder
      );
    }

    if (
      originals.title !== null
    ) {
      element.setAttribute(
        'title',
        currentLanguage === 'fr'
          ? translateExact(
              originals.title
            )
          : originals.title
      );
    }

    if (
      originals.ariaLabel !== null
    ) {
      element.setAttribute(
        'aria-label',
        currentLanguage === 'fr'
          ? translateExact(
              originals.ariaLabel
            )
          : originals.ariaLabel
      );
    }

    applyingTranslations =
      false;
  }

  // ============================================================
  // WALK DOM
  // ============================================================

  function translateTree(root) {
    if (!root) {
      return;
    }

    if (
      root.nodeType ===
      Node.TEXT_NODE
    ) {
      translateTextNode(root);
      return;
    }

    if (
      !(root instanceof Element) &&
      root !== document
    ) {
      return;
    }

    if (
      root instanceof Element
    ) {
      translateElementAttributes(
        root
      );
    }

    const walker =
      document.createTreeWalker(
        root,
        NodeFilter.SHOW_TEXT |
        NodeFilter.SHOW_ELEMENT
      );

    let node;

    while (
      (
        node =
          walker.nextNode()
      )
    ) {
      if (
        node.nodeType ===
        Node.TEXT_NODE
      ) {
        translateTextNode(
          node
        );
      } else if (
        node instanceof Element
      ) {
        translateElementAttributes(
          node
        );
      }
    }

    localizeSpecialControls();
  }

  // ============================================================
  // SPECIAL CONTROLS
  // ============================================================

  function localizeSpecialControls() {
    const languagePanel =
      document.getElementById(
        'languageSettingsPanel'
      );

    if (languagePanel) {
      languagePanel
        .querySelectorAll(
          '[data-lang-choice]'
        )
        .forEach(
          button => {
            button.classList.toggle(
              'gold',
              button.dataset.langChoice ===
                currentLanguage
            );

            button.classList.toggle(
              'secondary',
              button.dataset.langChoice !==
                currentLanguage
            );
          }
        );
    }

    const currencyCode =
      document.getElementById(
        'salaryCurrency'
      )?.value;

    const currencySearch =
      document.getElementById(
        'salaryCurrencySearch'
      );

    if (
      currencyCode &&
      currencySearch &&
      document.activeElement !==
        currencySearch
    ) {
      const currency =
        typeof window.currencyByCode ===
          'function'
          ? window.currencyByCode(
              currencyCode
            )
          : null;

      if (currency) {
        currencySearch.value =
          currentLanguage === 'fr'
            ? `${currency.code} — ${
                CURRENCY_FR[
                  currency.code
                ]?.name ||
                currency.name
              }`
            : `${currency.code} — ${currency.name}`;
      }
    }
  }

  // ============================================================
  // SAFE MUTATION OBSERVER
  // ============================================================
  // IMPORTANT:
  // Only watch for newly inserted DOM nodes.
  // Do NOT watch characterData/attributes here, otherwise
  // translations can trigger the observer repeatedly and freeze JAM.
  // ============================================================

  function installMutationObserver() {
    const observer =
      new MutationObserver(
        mutations => {
          if (applyingTranslations) {
            return;
          }

          for (
            const mutation
            of mutations
          ) {
            if (
              mutation.type !==
              'childList'
            ) {
              continue;
            }

            for (
              const added
              of mutation.addedNodes
            ) {
              if (
                added.nodeType ===
                  Node.TEXT_NODE ||
                added.nodeType ===
                  Node.ELEMENT_NODE
              ) {
                translateTree(
                  added
                );
              }
            }
          }
        }
      );

    observer.observe(
      document.body,
      {
        childList: true,
        subtree: true
      }
    );
  }

  // ============================================================
  // OVERRIDE EXISTING JAM HELPERS
  // ============================================================

  function installFunctionOverrides() {
    // --------------------------------------------------------
    // Dates
    // --------------------------------------------------------

    if (
      typeof window.formatDate ===
      'function'
    ) {
      window.formatDate =
        function(value) {
          if (!value) {
            return '—';
          }

          const date =
            new Date(value);

          if (
            Number.isNaN(
              date.getTime()
            )
          ) {
            return String(value)
              .slice(
                0,
                10
              );
          }

          return date.toLocaleDateString(
            currentLanguage === 'fr'
              ? 'fr-FR'
              : 'en-GB',
            {
              year:
                'numeric',

              month:
                'short',

              day:
                '2-digit'
            }
          );
        };
    }

    if (
      typeof window.monthLabel ===
      'function'
    ) {
      window.monthLabel =
        function(key) {
          if (
            key ===
            '(Unknown month)'
          ) {
            return (
              currentLanguage ===
              'fr'
                ? '(Mois inconnu)'
                : key
            );
          }

          const [
            year,
            month
          ] =
            key
              .split('-')
              .map(Number);

          const date =
            new Date(
              year,
              month - 1,
              1
            );

          return date.toLocaleDateString(
            currentLanguage === 'fr'
              ? 'fr-FR'
              : 'en-GB',
            {
              month:
                'long',

              year:
                'numeric'
            }
          );
        };
    }

    // --------------------------------------------------------
    // Currency search
    // --------------------------------------------------------

    const originalCurrencyMatches =
      typeof window.currencyMatches ===
        'function'
        ? window.currencyMatches
        : null;

    if (
      originalCurrencyMatches
    ) {
      window.currencyMatches =
        function(query) {
          if (
            currentLanguage !==
            'fr'
          ) {
            return originalCurrencyMatches(
              query
            );
          }

          const needle =
            String(
              query || ''
            )
              .trim()
              .toLocaleLowerCase(
                'fr-FR'
              );

          const all =
            originalCurrencyMatches(
              ''
            );

          if (!needle) {
            return all;
          }

          return all.filter(
            currency => {
              const french =
                CURRENCY_FR[
                  currency.code
                ];

              const haystack = [
                currency.code,
                currency.name,
                currency.countries,
                french?.name || '',
                french?.aliases || ''
              ]
                .join(' ')
                .toLocaleLowerCase(
                  'fr-FR'
                );

              return haystack.includes(
                needle
              );
            }
          );
        };
    }

    // --------------------------------------------------------
    // Currency selected label
    // --------------------------------------------------------

    if (
      typeof window.currencyDisplay ===
      'function'
    ) {
      window.currencyDisplay =
        function(currency) {
          if (
            currentLanguage === 'fr' &&
            CURRENCY_FR[
              currency.code
            ]
          ) {
            return (
              `${currency.code} — ` +
              CURRENCY_FR[
                currency.code
              ].name
            );
          }

          return (
            `${currency.code} — ` +
            currency.name
          );
        };
    }
  }

  // ============================================================
  // LANGUAGE SETTINGS PANEL
  // ============================================================

  function injectLanguageSettingsPanel() {
    if (
      document.getElementById(
        'languageSettingsPanel'
      )
    ) {
      return;
    }

    const grid =
      document.querySelector(
        '#settingsPage .settings-grid'
      );

    if (!grid) {
      return;
    }

    const panel =
      document.createElement(
        'article'
      );

    panel.id =
      'languageSettingsPanel';

    panel.className =
      'panel language-settings-panel';

    panel.innerHTML = `
      <span class="eyebrow">
        LANGUAGE
      </span>

      <h2>
        Language
      </h2>

      <p class="muted">
        Choose the interface language. The change is applied immediately across JAM.
      </p>

      <div class="button-row">
        <button
          type="button"
          class="btn secondary language-choice-btn"
          data-lang-choice="en"
        >
          <img src="../assets/flags/gb.png" alt="">
          <span>English</span>
        </button>

        <button
          type="button"
          class="btn secondary language-choice-btn"
          data-lang-choice="fr"
        >
          <img src="../assets/flags/fr.png" alt="">
          <span>Français</span>
        </button>
      </div>
    `;

    const safetyPanel =
      document.querySelector(
        '#settingsPage .backup-actions'
      )?.closest('article.panel');

    if (safetyPanel) {
      const stack =
        document.createElement('div');

      stack.className =
        'settings-left-stack';

      grid.prepend(stack);
      stack.appendChild(panel);
      stack.appendChild(safetyPanel);
    } else {
      grid.prepend(panel);
    }

    panel
      .querySelectorAll(
        '[data-lang-choice]'
      )
      .forEach(
        button => {
          button.addEventListener(
            'click',
            () => {
              setLanguage(
                button.dataset
                  .langChoice,
                true
              );
            }
          );
        }
      );

    translateTree(
      panel
    );
  }

  // ============================================================
  // SAVE LANGUAGE
  // ============================================================

  async function persistLanguage(
    language
  ) {
    try {
      if (
        window.pywebview?.api
          ?.save_setting
      ) {
        await window.pywebview
          .api
          .save_setting(
            LANGUAGE_SETTING_KEY,
            language
          );
      }
    } catch (error) {
      console.error(
        'Could not save JAM language setting.',
        error
      );
    }
  }

  // ============================================================
  // RE-RENDER DYNAMIC PAGES
  // ============================================================

  function rerenderApplicationViews() {
    const functions = [
      'renderStats',
      'renderRecentApplications',
      'renderTable',
      'renderPipeline',
      'renderExportHistory',
      'renderSettings'
    ];

    for (
      const name
      of functions
    ) {
      try {
        if (
          typeof window[name] ===
          'function'
        ) {
          window[name]();
        }
      } catch (error) {
        console.debug(
          `JAM i18n: ${name} refresh skipped`,
          error
        );
      }
    }
  }

  // ============================================================
  // CHANGE LANGUAGE
  // ============================================================

  async function setLanguage(
    language,
    persist = false
  ) {
    const normalized =
      SUPPORTED_LANGUAGES
        .has(language)
        ? language
        : 'en';

    currentLanguage =
      normalized;

    document.documentElement.lang =
      normalized === 'fr'
        ? 'fr'
        : 'en';

    if (persist) {
      await persistLanguage(
        normalized
      );
    }

    rerenderApplicationViews();

    translateTree(
      document.body
    );

    localizeSpecialControls();
  }

  // ============================================================
  // LOAD SAVED LANGUAGE
  // ============================================================

  async function loadSavedLanguage() {
    try {
      if (
        !window.pywebview?.api
          ?.bootstrap
      ) {
        return 'en';
      }

      const result =
        await window.pywebview
          .api
          .bootstrap();

      if (
        result?.ok &&
        SUPPORTED_LANGUAGES.has(
          result.settings?.language
        )
      ) {
        return (
          result.settings
            .language
        );
      }
    } catch (error) {
      console.error(
        'Could not load JAM language setting.',
        error
      );
    }

    return 'en';
  }

  // ============================================================
  // INIT
  // ============================================================

  async function init() {
    if (initialized) {
      return;
    }

    initialized =
      true;

    installFunctionOverrides();

    injectLanguageSettingsPanel();

    // Load + translate existing UI BEFORE starting observer.
    // This avoids the translation observer reacting to the initial pass.
    const saved =
      await loadSavedLanguage();

    await setLanguage(
      saved,
      false
    );

    installMutationObserver();
  }

  // ============================================================
  // PUBLIC API
  // ============================================================

  window.JAM_I18N = {
    get language() {
      return currentLanguage;
    },

    setLanguage,

    translate:
      text =>
        translateExact(
          String(
            text ?? ''
          )
        )
  };

  // ============================================================
  // START
  // ============================================================

  document.addEventListener(
    'pywebviewready',
    init
  );

  window.setTimeout(
    () => {
      if (
        !initialized &&
        window.pywebview?.api
      ) {
        init();
      }
    },
    100
  );
})();
