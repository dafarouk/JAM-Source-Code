#define MyAppName "JAM - Job Application Manager"
#ifndef MyAppVersion
#define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "Farouk"
#define MyAppURL "https://www.damergi.com"
#define MyAppExeName "JAM.exe"
#define MyProjectProgId "JAM.Project"

[Setup]
AppId={{9E18E729-1B2A-4CF0-9C79-5DB93CB9B765}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName=JAM {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL=https://github.com/dafarouk/JAM/issues
AppUpdatesURL=https://github.com/dafarouk/JAM/releases
DefaultDirName={autopf}\JAM
DefaultGroupName=JAM
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir=installer
OutputBaseFilename=JAM-Setup-{#MyAppVersion}
SetupIconFile=..\assets\branding\jam_runtime.ico
WizardImageFile=..\assets\setup\jam_setup_wizard.bmp
WizardSmallImageFile=..\assets\setup\jam_setup_small.bmp
WizardImageBackColor=$111827
WizardSmallImageBackColor=$111827
WizardStyle=modern
WizardResizable=yes
WizardSizePercent=110
Compression=lzma2/ultra64
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName=JAM - Job Application Manager
CloseApplications=yes
RestartApplications=no
SetupLogging=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "README-FIRST.en.txt"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"; InfoBeforeFile: "README-FIRST.fr.txt"

[Messages]
english.WelcomeLabel1=Welcome to JAM Setup
english.WelcomeLabel2=JAM by Farouk helps you manage applications, analyze job matches, track interviews and keep your job search organized.%n%nJAM is local-first and keeps your job-search data on your computer by default.%n%nClick Next to continue.
french.WelcomeLabel1=Bienvenue dans l'installation de JAM
french.WelcomeLabel2=JAM par Farouk vous aide à gérer vos candidatures, analyser les offres, suivre vos entretiens et organiser votre recherche d'emploi.%n%nJAM est local-first et conserve vos données de recherche d'emploi sur votre ordinateur par défaut.%n%nCliquez sur Suivant pour continuer.

[CustomMessages]
english.AdditionalTasks=Additional options:
french.AdditionalTasks=Options supplémentaires :
english.CreateStartMenuIcon=Create a &Start Menu shortcut
french.CreateStartMenuIcon=Créer un raccourci dans le menu &Démarrer
english.AssociateJam=&Associate .jam project files with JAM
french.AssociateJam=&Associer les fichiers projet .jam à JAM

[Tasks]
Name: "startmenuicon"; Description: "{cm:CreateStartMenuIcon}"; GroupDescription: "{cm:AdditionalTasks}"
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalTasks}"
Name: "fileassoc"; Description: "{cm:AssociateJam}"; GroupDescription: "{cm:AdditionalTasks}"

[Dirs]
Name: "{localappdata}\Farouk\JAM\database"; Flags: uninsneveruninstall
Name: "{localappdata}\Farouk\JAM\backups"; Flags: uninsneveruninstall
Name: "{localappdata}\Farouk\JAM\settings"; Flags: uninsneveruninstall
Name: "{localappdata}\Farouk\JAM\logs"; Flags: uninsneveruninstall
Name: "{localappdata}\Farouk\JAM\recovery"; Flags: uninsneveruninstall
Name: "{localappdata}\Farouk\JAM\updates"; Flags: uninsneveruninstall
Name: "{localappdata}\Farouk\JAM\attachments"; Flags: uninsneveruninstall
Name: "{userdocs}\JAM Exports"; Flags: uninsneveruninstall
Name: "{userdocs}\JAM Projects"; Flags: uninsneveruninstall

[Files]
Source: "..\dist\JAM\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\JAM"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: startmenuicon
Name: "{autodesktop}\JAM"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Classes\.jam"; ValueType: string; ValueData: "{#MyProjectProgId}"; Flags: uninsdeletevalue; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\{#MyProjectProgId}"; ValueType: string; ValueData: "JAM Project"; Flags: uninsdeletekey; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\{#MyProjectProgId}\DefaultIcon"; ValueType: string; ValueData: "{app}\{#MyAppExeName},0"; Tasks: fileassoc
Root: HKCU; Subkey: "Software\Classes\{#MyProjectProgId}\shell\open\command"; ValueType: string; ValueData: """{app}\{#MyAppExeName}"" ""%1"""; Tasks: fileassoc

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,JAM}"; WorkingDir: "{app}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Flags: nowait; Check: WizardSilent
