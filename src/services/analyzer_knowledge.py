from __future__ import annotations

# JAM Analyzer knowledge base.
# The engine is deliberately local and deterministic. These aliases are not
# treated as proof of expertise by themselves; they are only evidence tokens
# that the comparison engine can reason over.

SKILLS: dict[str, dict] = {
    # Languages / programming
    "Python": {"category": "Programming", "aliases": ["python"]},
    "R": {"category": "Programming", "aliases": ["r programming", "r language", "r studio", "rstudio"]},
    "Java": {"category": "Programming", "aliases": ["java"]},
    "JavaScript": {"category": "Programming", "aliases": ["javascript", "js"]},
    "TypeScript": {"category": "Programming", "aliases": ["typescript"]},
    "C#": {"category": "Programming", "aliases": ["c#", "c sharp"]},
    "C++": {"category": "Programming", "aliases": ["c++", "cpp"]},
    "Scala": {"category": "Programming", "aliases": ["scala"]},
    "VBA": {"category": "Programming", "aliases": ["vba", "visual basic for applications"]},
    "Bash": {"category": "Programming", "aliases": ["bash", "shell scripting", "shell script"]},

    # SQL / databases
    "SQL": {"category": "Database", "aliases": ["sql", "structured query language"]},
    "PL/SQL": {"category": "Database", "aliases": ["pl/sql", "pl sql"]},
    "T-SQL": {"category": "Database", "aliases": ["t-sql", "tsql", "transact sql"]},
    "PostgreSQL": {"category": "Database", "aliases": ["postgresql", "postgres"]},
    "MySQL": {"category": "Database", "aliases": ["mysql"]},
    "SQL Server": {"category": "Database", "aliases": ["sql server", "mssql", "microsoft sql server"]},
    "Oracle": {"category": "Database", "aliases": ["oracle database", "oracle db", "oracle"]},
    "SQLite": {"category": "Database", "aliases": ["sqlite"]},
    "Snowflake": {"category": "Database", "aliases": ["snowflake"]},
    "BigQuery": {"category": "Database", "aliases": ["bigquery", "google bigquery"]},
    "Redshift": {"category": "Database", "aliases": ["redshift", "amazon redshift"]},
    "MongoDB": {"category": "Database", "aliases": ["mongodb", "mongo db"]},
    "Elasticsearch": {"category": "Database", "aliases": ["elasticsearch", "elastic search"]},
    "Teradata": {"category": "Database", "aliases": ["teradata"]},

    # BI / visualization / spreadsheets
    "Power BI": {"category": "BI", "aliases": ["power bi", "powerbi"]},
    "DAX": {"category": "BI", "aliases": ["dax", "data analysis expressions"]},
    "Power Query": {"category": "BI", "aliases": ["power query", "m language"]},
    "Tableau": {"category": "BI", "aliases": ["tableau"]},
    "Qlik": {"category": "BI", "aliases": ["qlik", "qlik sense", "qlikview"]},
    "Looker": {"category": "BI", "aliases": ["looker"]},
    "Looker Studio": {"category": "BI", "aliases": ["looker studio", "google data studio", "data studio"]},
    "MicroStrategy": {"category": "BI", "aliases": ["microstrategy"]},
    "SAP BusinessObjects": {"category": "BI", "aliases": ["sap bo", "businessobjects", "business objects", "sap businessobjects"]},
    "Excel": {"category": "BI", "aliases": ["excel", "microsoft excel"]},
    "Power Pivot": {"category": "BI", "aliases": ["power pivot", "powerpivot"]},

    # Data engineering / integration
    "ETL": {"category": "Data Engineering", "aliases": ["etl", "extract transform load"]},
    "ELT": {"category": "Data Engineering", "aliases": ["elt", "extract load transform"]},
    "Talend": {"category": "Data Engineering", "aliases": ["talend"]},
    "Informatica": {"category": "Data Engineering", "aliases": ["informatica", "informatica powercenter"]},
    "dbt": {"category": "Data Engineering", "aliases": ["dbt", "data build tool"]},
    "Airflow": {"category": "Data Engineering", "aliases": ["airflow", "apache airflow"]},
    "SSIS": {"category": "Data Engineering", "aliases": ["ssis", "sql server integration services"]},
    "Azure Data Factory": {"category": "Data Engineering", "aliases": ["azure data factory", "adf"]},
    "Fivetran": {"category": "Data Engineering", "aliases": ["fivetran"]},
    "Kafka": {"category": "Data Engineering", "aliases": ["kafka", "apache kafka"]},
    "Spark": {"category": "Data Engineering", "aliases": ["apache spark", "spark"]},
    "PySpark": {"category": "Data Engineering", "aliases": ["pyspark", "py spark"]},
    "Databricks": {"category": "Data Engineering", "aliases": ["databricks"]},
    "Hadoop": {"category": "Data Engineering", "aliases": ["hadoop", "apache hadoop"]},

    # Cloud / DevOps
    "Azure": {"category": "Cloud", "aliases": ["microsoft azure", "azure"]},
    "AWS": {"category": "Cloud", "aliases": ["aws", "amazon web services"]},
    "GCP": {"category": "Cloud", "aliases": ["gcp", "google cloud platform", "google cloud"]},
    "Docker": {"category": "DevOps", "aliases": ["docker"]},
    "Kubernetes": {"category": "DevOps", "aliases": ["kubernetes", "k8s"]},
    "Git": {"category": "DevOps", "aliases": ["git"]},
    "GitHub": {"category": "DevOps", "aliases": ["github"]},
    "GitLab": {"category": "DevOps", "aliases": ["gitlab"]},
    "CI/CD": {"category": "DevOps", "aliases": ["ci/cd", "ci cd", "continuous integration", "continuous deployment"]},

    # Analytics / statistics / ML
    "Machine Learning": {"category": "Data Science", "aliases": ["machine learning", "ml model", "ml models"]},
    "scikit-learn": {"category": "Data Science", "aliases": ["scikit-learn", "sklearn", "scikit learn"]},
    "XGBoost": {"category": "Data Science", "aliases": ["xgboost"]},
    "TensorFlow": {"category": "Data Science", "aliases": ["tensorflow"]},
    "PyTorch": {"category": "Data Science", "aliases": ["pytorch"]},
    "NLP": {"category": "Data Science", "aliases": ["natural language processing", "nlp"]},
    "Forecasting": {"category": "Analytics", "aliases": ["forecasting", "time series", "time-series"]},
    "Statistics": {"category": "Analytics", "aliases": ["statistics", "statistical analysis", "statistical modelling", "statistical modeling"]},
    "A/B Testing": {"category": "Analytics", "aliases": ["a/b testing", "ab testing", "a/b test", "experimentation"]},
    "Data Mining": {"category": "Analytics", "aliases": ["data mining"]},

    # Data management / quality / governance
    "Data Quality": {"category": "Data Management", "aliases": ["data quality", "quality of data", "qualite des donnees", "qualité des données"]},
    "Data Governance": {"category": "Data Management", "aliases": ["data governance", "gouvernance des donnees", "gouvernance des données"]},
    "Data Lineage": {"category": "Data Management", "aliases": ["data lineage", "lineage"]},
    "Data Catalog": {"category": "Data Management", "aliases": ["data catalog", "data catalogue", "catalogue de donnees", "catalogue de données"]},
    "Master Data Management": {"category": "Data Management", "aliases": ["master data management", "mdm"]},
    "GDPR": {"category": "Data Management", "aliases": ["gdpr", "rgpd"]},
    "Data Modeling": {"category": "Data Management", "aliases": ["data modeling", "data modelling", "modelisation des donnees", "modélisation des données"]},
    "Dimensional Modeling": {"category": "Data Management", "aliases": ["dimensional modeling", "dimensional modelling", "star schema", "snowflake schema"]},

    # CRM / ERP / enterprise
    "Salesforce": {"category": "Enterprise", "aliases": ["salesforce"]},
    "SAP": {"category": "Enterprise", "aliases": ["sap erp", "sap s/4", "sap s4", "sap"]},
    "SAP BW": {"category": "Enterprise", "aliases": ["sap bw", "sap business warehouse"]},
    "SAP Analytics Cloud": {"category": "Enterprise", "aliases": ["sap analytics cloud", "sac"]},
    "Microsoft Dynamics 365": {"category": "Enterprise", "aliases": ["dynamics 365", "microsoft dynamics"]},
    "HubSpot": {"category": "Enterprise", "aliases": ["hubspot"]},

    # Microsoft productivity / automation
    "SharePoint": {"category": "Productivity", "aliases": ["sharepoint"]},
    "Power Automate": {"category": "Productivity", "aliases": ["power automate", "microsoft flow"]},
    "Power Apps": {"category": "Productivity", "aliases": ["power apps", "powerapps"]},

    # Collaboration / project tools
    "Jira": {"category": "Collaboration", "aliases": ["jira"]},
    "Confluence": {"category": "Collaboration", "aliases": ["confluence"]},
    "ServiceNow": {"category": "Collaboration", "aliases": ["servicenow", "service now"]},

    # Methods / business-analysis techniques
    "Agile": {"category": "Methodology", "aliases": ["agile"]},
    "Scrum": {"category": "Methodology", "aliases": ["scrum"]},
    "UAT": {"category": "Methodology", "aliases": ["uat", "user acceptance testing"]},
    "BPMN": {"category": "Methodology", "aliases": ["bpmn"]},
    "UML": {"category": "Methodology", "aliases": ["uml"]},
}


BUSINESS_CONCEPTS: dict[str, list[str]] = {
    "KPI": ["kpi", "key performance indicator", "indicateurs de performance", "indicateur de performance"],
    "Reporting": ["reporting", "reports", "rapporting", "rapports"],
    "Dashboarding": ["dashboard", "dashboards", "tableau de bord", "tableaux de bord"],
    "Data Visualization": ["data visualization", "data visualisation", "visualisation de donnees", "visualisation des donnees"],
    "Business Analysis": ["business analysis", "business analyst", "analyse metier", "analyse métier"],
    "Requirements Gathering": ["requirements gathering", "requirements analysis", "recueil des besoins", "expression de besoin", "cahier des charges"],
    "Stakeholder Management": ["stakeholder management", "stakeholders", "parties prenantes", "metiers", "métiers"],
    "Process Improvement": ["process improvement", "continuous improvement", "amelioration continue", "amélioration continue", "optimisation des processus"],
    "Project Management": ["project management", "gestion de projet", "project manager", "chef de projet"],
    "Performance Analysis": ["performance analysis", "performance management", "analyse de performance", "pilotage de la performance"],
    "Operations": ["operations", "operational", "operations analysis", "operationnel", "opérationnel", "exploitation"],
    "Supply Chain": ["supply chain", "chaine logistique", "chaîne logistique"],
    "Logistics": ["logistics", "logistique"],
    "Inventory": ["inventory", "stock", "stocks", "inventory management", "gestion des stocks"],
    "Procurement": ["procurement", "purchasing", "achats", "approvisionnement"],
    "Finance": ["finance", "financial", "financier", "financiere", "financière"],
    "Controlling": ["controlling", "controle de gestion", "contrôle de gestion"],
    "Budgeting": ["budgeting", "budget", "budgetaire", "budgétaire"],
    "Financial Forecasting": ["financial forecasting", "forecast", "forecasting", "prevision", "prévision"],
    "Sales Analytics": ["sales analytics", "sales performance", "analyse des ventes", "performance commerciale"],
    "Marketing Analytics": ["marketing analytics", "marketing performance", "analyse marketing"],
    "CRM Analytics": ["crm analytics", "crm data", "customer relationship management"],
    "Product Analytics": ["product analytics", "product data", "analyse produit"],
    "Customer Analytics": ["customer analytics", "customer data", "client data", "donnees clients", "données clients"],
    "Customer Experience": ["customer experience", "cx", "experience client", "expérience client"],
    "Segmentation": ["segmentation", "customer segmentation", "segmentation client"],
    "Data Cleaning": ["data cleaning", "data cleansing", "nettoyage des donnees", "nettoyage des données"],
    "Data Validation": ["data validation", "validation des donnees", "validation des données"],
    "Data Reconciliation": ["data reconciliation", "reconciliation de donnees", "réconciliation de données"],
    "Root Cause Analysis": ["root cause analysis", "analyse des causes racines", "root cause"],
    "Automation": ["automation", "automatisation", "automate", "automating"],
    "Documentation": ["documentation", "documenting", "documenter"],
    "Training": ["training", "formation", "former les utilisateurs", "user training"],
    "Presentation": ["presentation", "présentation", "presenting", "communication des resultats", "communication des résultats"],
    "Data Storytelling": ["data storytelling", "storytelling", "story telling"],
    "Decision Support": ["decision support", "aide a la decision", "aide à la décision"],
    "Airline / Aviation": ["airline", "aviation", "air transport", "transport aerien", "transport aérien"],
    "E-commerce": ["e-commerce", "ecommerce", "e commerce"],
    "Retail": ["retail", "distribution", "commerce de detail", "commerce de détail"],
    "Banking": ["banking", "bank", "banque", "bancaire"],
    "Insurance": ["insurance", "assurance", "assurances"],
    "Telecom": ["telecom", "telecommunications", "télécom", "telecommunication"],
}


ROLE_FAMILIES: dict[str, list[str]] = {
    "Data Analyst": [
        "data analyst", "analyste data", "analyste de donnees", "analyste de données",
        "data analytics analyst", "analyst data",
    ],
    "BI Analyst": [
        "bi analyst", "business intelligence analyst", "analyste bi", "analyste decisionnel",
        "analyste décisionnel", "business intelligence consultant",
    ],
    "BI Developer": [
        "bi developer", "business intelligence developer", "developpeur bi", "développeur bi",
        "power bi developer", "tableau developer",
    ],
    "Business Analyst": [
        "business analyst", "analyste fonctionnel", "analyste métier", "analyste metier",
    ],
    "Data Engineer": [
        "data engineer", "ingenieur data", "ingénieur data", "data engineering",
    ],
    "Data Scientist": [
        "data scientist", "data science", "scientist data",
    ],
    "Analytics Engineer": [
        "analytics engineer", "analytical engineer",
    ],
    "Product Analyst": [
        "product analyst", "product data analyst", "analyste produit",
    ],
    "CRM Analyst": [
        "crm analyst", "crm data analyst", "analyste crm",
    ],
    "Marketing Analyst": [
        "marketing analyst", "marketing data analyst", "analyste marketing",
    ],
    "Sales Analyst": [
        "sales analyst", "sales data analyst", "analyste commercial", "analyste des ventes",
    ],
    "Performance Analyst": [
        "performance analyst", "analyste performance", "analyste de performance",
    ],
    "Reporting Analyst": [
        "reporting analyst", "analyste reporting", "reporting specialist",
    ],
    "Data Quality Analyst": [
        "data quality analyst", "data quality specialist", "analyste qualite des donnees",
        "analyste qualité des données",
    ],
    "Data Governance Analyst": [
        "data governance analyst", "data governance specialist", "analyste gouvernance data",
        "analyste gouvernance des donnees", "analyste gouvernance des données",
    ],
    "Operations Analyst": [
        "operations analyst", "operational analyst", "analyste operations", "analyste opérations",
        "analyste operationnel", "analyste opérationnel",
    ],
    "Supply Chain Analyst": [
        "supply chain analyst", "logistics analyst", "analyste supply chain", "analyste logistique",
    ],
    "Financial Analyst": [
        "financial analyst", "finance analyst", "analyste financier", "controleur de gestion",
        "contrôleur de gestion",
    ],
    "Risk Analyst": [
        "risk analyst", "analyste risques", "analyste risque",
    ],
    "Product Owner": [
        "product owner", "po data", "data product owner",
    ],
    "Product Manager": [
        "product manager", "data product manager",
    ],
    "Project Manager": [
        "project manager", "chef de projet", "data project manager",
    ],
    "Accountant": [
        "accountant", "accounting specialist", "accounting officer", "comptable",
        "bookkeeper", "bookkeeping",
    ],
    "Auditor": [
        "auditor", "audit associate", "auditeur", "auditrice", "audit financier",
    ],
    "Human Resources": [
        "human resources", "hr specialist", "hr generalist", "hr manager",
        "ressources humaines", "talent acquisition", "recruiter", "recruteur",
    ],
    "Software Developer": [
        "software developer", "software engineer", "backend developer", "backend engineer",
        "frontend developer", "front end developer", "full stack developer",
        "fullstack developer", "developpeur logiciel", "développeur logiciel",
        "developpeur backend", "développeur backend",
    ],
    "Cybersecurity": [
        "cybersecurity", "cyber security", "security engineer", "security analyst",
        "analyste cybersecurite", "analyste cybersécurité", "securite informatique",
        "sécurité informatique",
    ],
    "Sales": [
        "sales representative", "sales executive", "account executive",
        "business developer", "business development representative",
        "commercial", "ingenieur commercial", "ingénieur commercial",
    ],
    "Marketing": [
        "marketing specialist", "marketing manager", "digital marketing",
        "responsable marketing", "charge marketing", "chargé marketing",
    ],
    "Customer Service": [
        "customer service", "customer support", "support agent", "conseiller client",
        "conseiller clientele", "conseiller clientèle", "service client",
    ],
    "Legal": [
        "legal counsel", "legal specialist", "lawyer", "juriste", "avocat",
    ],
}


RELATED_ROLE_FAMILIES: dict[str, set[str]] = {
    "Data Analyst": {"BI Analyst", "Reporting Analyst", "Performance Analyst", "Product Analyst", "CRM Analyst", "Marketing Analyst", "Sales Analyst", "Operations Analyst", "Supply Chain Analyst"},
    "BI Analyst": {"Data Analyst", "BI Developer", "Reporting Analyst", "Performance Analyst"},
    "BI Developer": {"BI Analyst", "Data Engineer", "Analytics Engineer"},
    "Business Analyst": {"Product Owner", "Project Manager", "Data Analyst"},
    "Data Engineer": {"Analytics Engineer", "BI Developer", "Data Scientist"},
    "Data Scientist": {"Data Analyst", "Data Engineer", "Analytics Engineer"},
    "Analytics Engineer": {"Data Engineer", "BI Developer", "Data Analyst"},
    "Product Analyst": {"Data Analyst", "Product Owner", "Marketing Analyst"},
    "CRM Analyst": {"Data Analyst", "Marketing Analyst", "Sales Analyst"},
    "Marketing Analyst": {"Data Analyst", "CRM Analyst", "Sales Analyst", "Product Analyst"},
    "Sales Analyst": {"Data Analyst", "CRM Analyst", "Marketing Analyst", "Performance Analyst"},
    "Performance Analyst": {"Data Analyst", "Reporting Analyst", "Operations Analyst", "Financial Analyst"},
    "Reporting Analyst": {"Data Analyst", "BI Analyst", "Performance Analyst"},
    "Data Quality Analyst": {"Data Governance Analyst", "Data Analyst"},
    "Data Governance Analyst": {"Data Quality Analyst", "Data Analyst"},
    "Operations Analyst": {"Data Analyst", "Performance Analyst", "Supply Chain Analyst"},
    "Supply Chain Analyst": {"Operations Analyst", "Data Analyst", "Performance Analyst"},
    "Financial Analyst": {"Performance Analyst", "Data Analyst"},
    "Risk Analyst": {"Financial Analyst", "Data Analyst"},
    "Product Owner": {"Business Analyst", "Product Manager", "Product Analyst", "Project Manager"},
    "Product Manager": {"Product Owner", "Product Analyst", "Business Analyst"},
    "Project Manager": {"Business Analyst", "Product Owner"},
    "Accountant": {"Auditor", "Financial Analyst"},
    "Auditor": {"Accountant", "Risk Analyst", "Financial Analyst"},
    "Human Resources": set(),
    "Software Developer": {"Data Engineer"},
    "Cybersecurity": set(),
    "Sales": {"Sales Analyst"},
    "Marketing": {"Marketing Analyst"},
    "Customer Service": set(),
    "Legal": set(),
}


LANGUAGES: dict[str, list[str]] = {
    "English": ["english", "anglais"],
    "French": ["french", "francais", "français"],
    "Arabic": ["arabic", "arabe"],
    "German": ["german", "allemand"],
    "Spanish": ["spanish", "espagnol"],
    "Italian": ["italian", "italien"],
    "Portuguese": ["portuguese", "portugais"],
    "Dutch": ["dutch", "neerlandais", "néerlandais"],
    "Chinese": ["chinese", "mandarin", "chinois"],
    "Japanese": ["japanese", "japonais"],
}


LANGUAGE_LEVELS: dict[str, int] = {
    "native": 6,
    "mother tongue": 6,
    "langue maternelle": 6,
    "bilingual": 6,
    "bilingue": 6,
    "c2": 6,
    "fluent": 5,
    "courant": 5,
    "courante": 5,
    "c1": 5,
    "professional proficiency": 4,
    "professionnel": 4,
    "professionnelle": 4,
    "b2": 4,
    "intermediate": 3,
    "intermediaire": 3,
    "intermédiaire": 3,
    "b1": 3,
    "a2": 2,
    "basic": 1,
    "notions": 1,
    "a1": 1,
}


DEGREE_PATTERNS: list[tuple[str, int]] = [
    (r"\bph\.?d\.?\b|\bdoctorate\b|\bdoctorat\b", 5),
    (r"\bbac\s*\+\s*5\b|\bmaster(?:'s)?\b|\bmsc\b|\bmba\b|\bdiplome d[' ]?ingenieur\b|\bdiplôme d[' ]?ingénieur\b|\bengineering degree\b", 4),
    (r"\bbac\s*\+\s*4\b|\bmaitrise\b|\bmaîtrise\b", 3),
    (r"\bbac\s*\+\s*3\b|\bbachelor(?:'s)?\b|\bbsc\b|\blicence\b", 3),
    (r"\bbac\s*\+\s*2\b|\bbts\b|\bdut\b|\bassociate(?:'s)?\b", 2),
    (r"\bbaccalaureat\b|\bbaccalauréat\b|\bhigh school\b", 1),
]

DEGREE_LABELS = {
    0: "Not specified",
    1: "High school / Baccalauréat",
    2: "Bac+2 / Associate",
    3: "Bachelor / Licence",
    4: "Master / Engineering degree",
    5: "PhD / Doctorate",
}


# Education-field evidence. Degree level alone is not enough when a job asks
# for a specific field of study. The analyzer compares the requested field
# against degree/education lines from the CV instead of assuming a higher but
# unrelated degree is compatible.
EDUCATION_FIELDS: dict[str, list[str]] = {
    "Accounting": [
        "accounting", "accountancy", "comptabilite", "comptabilité",
        "expertise comptable", "dcg", "dscg",
    ],
    "Finance": [
        "finance", "financial management", "gestion financiere",
        "gestion financière", "corporate finance",
    ],
    "Law": [
        "law", "legal studies", "droit", "sciences juridiques",
        "juridique", "juridiques",
    ],
    "Labor / Social Law": [
        "labor law", "labour law", "employment law", "social law",
        "droit social", "droit du travail", "relations sociales",
    ],
    "Data / Analytics": [
        "data analytics", "business analytics", "data analysis",
        "analyse de donnees", "analyse de données", "data science",
        "business intelligence", "informatique decisionnelle",
        "informatique décisionnelle",
    ],
    "Computer Science": [
        "computer science", "informatique", "software engineering",
        "genie logiciel", "génie logiciel", "information systems",
        "systemes d'information", "systèmes d'information",
    ],
    "Statistics / Mathematics": [
        "statistics", "statistique", "statistiques", "mathematics",
        "mathematiques", "mathématiques", "applied mathematics",
    ],
    "Business / Management": [
        "business administration", "business management", "management",
        "gestion", "commerce", "administration des entreprises",
    ],
    "Economics": [
        "economics", "economie", "économie", "economic sciences",
        "sciences economiques", "sciences économiques",
    ],
    "Engineering": [
        "engineering", "ingenierie", "ingénierie", "ingenieur", "ingénieur",
    ],
    "Human Resources": [
        "human resources", "ressources humaines", "gestion des ressources humaines",
        "hr management",
    ],
    "Marketing": [
        "marketing", "digital marketing", "marketing digital",
    ],
    "Supply Chain / Logistics": [
        "supply chain", "logistics", "logistique", "gestion logistique",
    ],
}

EDUCATION_FIELD_RELATIONS: dict[str, set[str]] = {
    "Accounting": {"Finance"},
    "Finance": {"Accounting", "Economics"},
    "Law": {"Labor / Social Law"},
    "Labor / Social Law": {"Law"},
    "Data / Analytics": {"Computer Science", "Statistics / Mathematics"},
    "Computer Science": {"Data / Analytics"},
    "Statistics / Mathematics": {"Data / Analytics"},
    "Business / Management": {"Economics"},
    "Economics": {"Business / Management", "Finance"},
    "Engineering": {"Computer Science"},
    "Human Resources": {"Business / Management"},
    "Marketing": {"Business / Management"},
    "Supply Chain / Logistics": {"Business / Management"},
}


SENIORITY_PATTERNS: dict[str, list[str]] = {
    "Internship": ["intern", "internship", "stagiaire", "stage"],
    "Junior": ["junior", "entry level", "entry-level", "debutant", "débutant"],
    "Senior": ["senior", "sr.", "sr "],
    "Lead": ["lead", "principal", "staff"],
    "Manager": ["manager", "head of", "responsable", "director", "directeur", "directrice"],
}


REQUIRED_MARKERS = [
    "required", "requires", "require", "requirement", "requirements", "must have", "must", "mandatory",
    "essential", "minimum", "at least", "you have", "you bring", "we expect",
    "requis", "requise", "requis(e)", "obligatoire", "imperatif", "impératif",
    "minimum", "au moins", "vous maitrisez", "vous maîtrisez", "maitrise de",
    "maîtrise de", "exige", "exigé", "exigee", "exigée", "indispensable",
]

PREFERRED_MARKERS = [
    "preferred", "nice to have", "nice-to-have", "bonus", "ideally", "a plus",
    "would be a plus", "appreciated", "desirable", "souhaite", "souhaité",
    "souhaitee", "souhaitée", "apprecie", "apprécié", "serait un plus",
    "idealement", "idéalement", "un plus", "atout",
]

NEGATIVE_REQUIREMENT_MARKERS = [
    "not required", "no experience required", "not mandatory", "optional",
    "pas obligatoire", "non requis", "aucune experience requise", "aucune expérience requise",
]

RESPONSIBILITY_MARKERS = [
    "responsibilities", "responsibility", "what you will do", "you will",
    "your role", "mission", "missions", "responsable de", "vous serez",
    "vos missions", "role", "rôle", "activities", "activites", "activités",
]

PROFESSIONAL_SIGNAL_WORDS = [
    "experience", "skills", "competencies", "competences", "compétences", "requirements",
    "qualification", "qualifications", "missions", "responsibilities", "profile", "profil",
    "degree", "diploma", "diplome", "diplôme", "language", "langue", "salary", "salaire",
    "team", "equipe", "équipe", "client", "customer", "project", "projet", "data", "analyst",
    "engineer", "manager", "business", "reporting", "dashboard", "kpi", "sql", "python",
]


# Common words intentionally excluded from lexical-overlap scoring. This is not
# a linguistic model; the goal is to remove generic job-ad boilerplate so that
# overlap is driven by meaningful business/technical terms.
STOPWORDS = {
    "a", "about", "above", "across", "after", "again", "against", "all", "also", "am", "an",
    "and", "any", "are", "as", "at", "be", "because", "been", "before", "being", "below", "between",
    "both", "but", "by", "can", "could", "did", "do", "does", "doing", "down", "during", "each",
    "few", "for", "from", "further", "had", "has", "have", "having", "he", "her", "here", "hers",
    "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "just", "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off", "on",
    "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she",
    "should", "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why",
    "will", "with", "you", "your", "yours", "yourself", "yourselves", "work", "working", "role", "job",
    "position", "company", "team", "candidate", "candidates", "including", "etc", "using", "use", "used",
    "new", "within", "strong", "excellent", "good", "support", "ensure", "provide", "develop", "manage",
    # French
    "a", "afin", "ainsi", "alors", "au", "aucun", "aussi", "autre", "aux", "avec", "avoir", "car",
    "ce", "ces", "cet", "cette", "chez", "comme", "comment", "dans", "de", "des", "du", "elle", "en",
    "entre", "est", "et", "etre", "être", "faire", "il", "ils", "je", "la", "le", "les", "leur", "leurs",
    "lui", "mais", "mes", "moi", "mon", "ne", "nos", "notre", "nous", "on", "ou", "où", "par", "pas",
    "plus", "pour", "que", "quel", "quelle", "quelles", "quels", "qui", "sa", "sans", "se", "ses", "si",
    "son", "sont", "sur", "ta", "te", "tes", "toi", "ton", "tous", "tout", "toute", "toutes", "tu", "un",
    "une", "vos", "votre", "vous", "poste", "entreprise", "equipe", "équipe", "profil", "mission", "missions",
}

TITLE_STOPWORDS = STOPWORDS | {
    "h/f", "f/h", "m/f", "f/m", "h/f/x", "f/h/x", "cdi", "cdd", "internship", "stage", "alternance",
    "apprenticeship", "freelance", "remote", "hybrid", "onsite", "paris", "france", "tunisia", "tunis",
}


# Role-specific domain signals used by Match Engine v3.1.
# These are not generic "nice to have" keywords: they represent vocabulary that
# normally proves the CV actually contains evidence for the target profession.
ROLE_DOMAIN_SIGNALS: dict[str, list[str]] = {
    "Risk Analyst": [
        "risk assessment", "risk analysis", "credit risk", "market risk",
        "operational risk", "risk model", "var", "value at risk",
        "stress testing", "risk controls", "risk appetite",
    ],
    "Product Owner": [
        "product backlog", "backlog", "user stories", "acceptance criteria",
        "sprint", "roadmap", "stakeholder", "agile", "scrum",
        "prioritization", "prioritisation",
    ],
    "Product Manager": [
        "product strategy", "product roadmap", "roadmap", "product discovery",
        "user research", "prioritization", "prioritisation", "go to market",
        "product metrics", "market research",
    ],
    "Project Manager": [
        "project plan", "project planning", "planning projet", "budget",
        "timeline", "milestone", "jalon", "risk management", "governance",
        "stakeholder", "project delivery", "gestion de projet",
    ],
    "Accountant": [
        "ifrs", "gaap", "general ledger", "grand livre", "journal entries",
        "ecritures comptables", "écritures comptables", "account reconciliation",
        "reconciliation", "réconciliation", "month end close", "monthly close",
        "cloture mensuelle", "clôture mensuelle", "year end close",
        "balance sheet", "bilan comptable", "income statement",
        "profit and loss", "p&l", "accounts payable", "accounts receivable",
        "bookkeeping", "comptabilite", "comptabilité", "vat", "tva",
        "tax accounting", "fiscalite", "fiscalité", "trial balance",
    ],
    "Auditor": [
        "audit", "internal control", "controle interne", "contrôle interne",
        "audit procedures", "substantive testing", "risk assessment",
        "financial statements", "ifrs", "gaap", "audit report",
    ],
    "Data Analyst": [
        "sql", "power bi", "tableau", "python", "dax", "power query",
        "dashboard", "data analysis", "analyse de donnees", "analyse de données",
        "data visualization", "visualisation de donnees", "visualisation de données",
        "kpi", "reporting", "etl", "data cleaning", "data quality",
    ],
    "BI Analyst": [
        "power bi", "dax", "power query", "sql", "tableau", "dashboard",
        "reporting", "business intelligence", "bi", "kpi", "data model",
    ],
    "BI Developer": [
        "power bi", "dax", "sql", "etl", "semantic model", "data model",
        "star schema", "business intelligence", "deployment pipeline",
        "row level security", "rls", "data warehouse",
    ],
    "Business Analyst": [
        "requirements gathering", "requirements analysis", "user stories",
        "functional specifications", "specifications fonctionnelles",
        "stakeholder management", "process mapping", "bpmn", "uat",
        "business process", "recueil des besoins", "expression de besoin",
    ],
    "Data Engineer": [
        "data pipeline", "etl", "elt", "airflow", "spark", "pyspark",
        "kafka", "dbt", "data warehouse", "data lake", "lakehouse",
        "orchestration", "ingestion",
    ],
    "Data Scientist": [
        "machine learning", "statistical modeling", "statistical modelling",
        "feature engineering", "model evaluation", "scikit-learn", "sklearn",
        "xgboost", "tensorflow", "pytorch", "nlp", "predictive model",
    ],
    "Analytics Engineer": [
        "dbt", "sql", "data modeling", "data modelling", "semantic layer",
        "data warehouse", "elt", "transformation", "analytics engineering",
    ],
    "Product Analyst": [
        "product analytics", "funnel", "retention", "cohort", "a/b testing",
        "experimentation", "product metrics", "conversion", "activation",
        "engagement",
    ],
    "CRM Analyst": [
        "crm", "salesforce", "customer segmentation", "segmentation client",
        "campaign", "lifecycle", "retention", "customer data", "donnees clients",
        "données clients",
    ],
    "Marketing Analyst": [
        "marketing analytics", "campaign", "attribution", "roas", "cac",
        "conversion", "seo", "sea", "acquisition", "marketing performance",
    ],
    "Sales Analyst": [
        "sales performance", "sales pipeline", "forecast", "revenue", "quota",
        "crm", "salesforce", "commercial performance", "performance commerciale",
    ],
    "Performance Analyst": [
        "kpi", "performance management", "performance analysis",
        "operational performance", "performance operationnelle",
        "performance opérationnelle", "variance analysis", "productivity",
        "dashboard", "reporting",
    ],
    "Reporting Analyst": [
        "reporting", "dashboard", "kpi", "power bi", "excel", "sql",
        "performance reporting", "management reporting",
    ],
    "Data Quality Analyst": [
        "data quality", "qualite des donnees", "qualité des données",
        "data validation", "data cleansing", "data controls", "data governance",
        "quality rules", "data remediation",
    ],
    "Data Governance Analyst": [
        "data governance", "gouvernance des donnees", "gouvernance des données",
        "data catalog", "data lineage", "metadata", "data owner",
        "data steward", "data quality",
    ],
    "Financial Analyst": [
        "financial modeling", "financial analysis", "analyse financiere",
        "analyse financière", "budget", "forecast", "variance analysis",
        "p&l", "cash flow", "business case",
    ],
    "Supply Chain Analyst": [
        "supply chain", "inventory", "stock", "logistics", "logistique",
        "forecast", "demand planning", "transport", "warehouse", "entrepot",
        "entrepôt",
    ],
    "Operations Analyst": [
        "operations", "operational performance", "performance operationnelle",
        "performance opérationnelle", "process improvement", "kpi",
        "service level", "sla", "productivity",
    ],
    "Human Resources": [
        "recruitment", "recrutement", "payroll", "paie", "talent acquisition",
        "employee relations", "hris", "ressources humaines",
    ],
    "Marketing": [
        "marketing", "campaign", "campagne", "seo", "sea", "acquisition",
        "conversion", "brand", "crm", "segmentation",
    ],
    "Legal": [
        "labor law", "labour law", "employment law", "social law",
        "droit social", "droit du travail", "code du travail",
        "collective bargaining", "convention collective", "accord collectif",
        "employee relations", "relations sociales", "cse",
        "employment contract", "contrat de travail", "contentieux",
        "legal research", "veille juridique", "procedure disciplinaire",
        "procédure disciplinaire", "licenciement",
    ],
    "Customer Service": [
        "customer service", "service client", "customer support",
        "relation client", "customer satisfaction", "satisfaction client",
        "ticketing", "case management", "gestion des reclamations",
        "gestion des réclamations",
    ],
    "Sales": [
        "sales", "vente", "pipeline", "prospecting", "prospection",
        "revenue", "chiffre d'affaires", "account management", "crm",
    ],
    "Cybersecurity": [
        "cybersecurity", "cybersecurite", "cybersécurité", "siem", "soc",
        "vulnerability", "vulnerabilite", "vulnérabilité", "incident response",
        "security controls", "iso 27001",
    ],
    "Software Developer": [
        "software development", "developpement logiciel", "développement logiciel",
        "api", "git", "backend", "frontend", "testing", "unit tests",
        "deployment", "ci/cd",
    ],
}
