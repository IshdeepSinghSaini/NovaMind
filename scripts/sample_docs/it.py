"""IT department documents (fictional). A section item: str = paragraph, list = bullet points."""

from sample_docs.facts import *  # noqa: F401,F403

DOCUMENTS = [
    # ------------------------------------------------------------------ IT-001
    {
        "doc_code": "IT-001", "title": "IT Support Manual", "department": "IT",
        "document_type": "Manual", "version": "3.4", "created": "2025-02-10",
        "access_level": "IT", "format": "pdf",
        "sections": [
            ("1. Purpose", [
                "This manual is the internal runbook for the IT Support team. It defines support "
                "levels, ticket priorities, escalation paths and standard procedures. It is restricted "
                "to IT staff.",
            ]),
            ("2. Support Levels", [
                [
                    "L1 Service Desk - first contact; password issues, VPN help, basic troubleshooting.",
                    "L2 Desktop and Network Support - laptop repairs, reimaging, network issues.",
                    "L3 Infrastructure and Security Engineering - servers, firewalls, identity systems.",
                ],
                "L1 must escalate a ticket to L2 if it is not resolved within 4 hours, and L2 must "
                "escalate to L3 if it needs infrastructure or security changes.",
            ]),
            ("3. Ticket Priorities and Service Levels", [
                [
                    "P1 Critical (office-wide outage, security incident): respond in 15 minutes, "
                    "resolve in 4 hours.",
                    "P2 High (a team cannot work): respond in 1 hour, resolve in 1 working day.",
                    "P3 Medium (one user affected, workaround exists): respond in 4 hours, resolve in "
                    "3 working days.",
                    "P4 Low (requests and questions): respond in 1 working day, resolve in 5 working days.",
                ],
            ]),
            ("4. Privileged (Admin) Accounts", [
                f"IT engineers use separate privileged accounts for administrative work. Privileged "
                f"accounts use the prefix '{ADMIN_PREFIX}' (for example, {ADMIN_PREFIX}firstname).",
                [
                    "Privileged accounts are approved by the IT Security Manager.",
                    "They must never be used for email or web browsing.",
                    "All privileged accounts are reviewed every quarter and unused ones are disabled.",
                    "Privileged sessions on servers are recorded.",
                ],
            ]),
            ("5. Laptop Reimaging Procedure", [
                [
                    "Confirm the user's data is synced to the company cloud drive.",
                    "Remove the device from the device management console.",
                    "Boot from the standard TechNova image (Windows 11 Enterprise, build approved by "
                    "Security).",
                    "Re-enrol the device, install standard software from NovaStore and enable disk "
                    "encryption.",
                    "Hand over the laptop and close the ticket with the asset tag number.",
                ],
            ]),
            ("6. Asset Management", [
                "Every laptop, monitor and phone has an asset tag in the format TN-AST-NNNNN. Asset "
                "records are updated within 1 working day of any issue, return or repair.",
            ]),
            ("7. On-Call Rota", [
                "One L2 and one L3 engineer are on call outside business hours on a weekly rota. P1 "
                "incidents outside business hours are paged to the on-call engineers automatically.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ IT-002
    {
        "doc_code": "IT-002", "title": "VPN Configuration Guide", "department": "IT",
        "document_type": "Guide", "version": "2.2", "created": "2025-03-12",
        "access_level": "Employee", "format": "docx",
        "sections": [
            ("1. What Is the VPN?", [
                f"The VPN (Virtual Private Network) creates a secure, encrypted connection between your "
                f"laptop and the TechNova network. You must use the {VPN_CLIENT} client whenever you work "
                "outside the office, including when working from home.",
            ]),
            ("2. Before You Start", [
                [
                    "You need your TechNova username and password.",
                    f"You need the {MFA_APP} app set up on your phone for multi-factor authentication.",
                    "The VPN works on company laptops only (Windows and macOS).",
                ],
            ]),
            ("3. Installing the VPN Client", [
                [
                    f"Open {SOFTWARE_STORE} on your company laptop.",
                    f"Search for '{VPN_CLIENT}' and click Install.",
                    "Restart your laptop when the installation finishes.",
                ],
            ]),
            ("4. Connecting to the VPN", [
                [
                    f"Open {VPN_CLIENT} from the Start menu (Windows) or Applications (macOS).",
                    f"In the Server field, enter {VPN_SERVER} (this is usually filled in automatically).",
                    "Enter your TechNova username and password.",
                    f"Approve the sign-in request in the {MFA_APP} app on your phone.",
                    "The status changes to 'Connected' and a green shield appears in the system tray.",
                ],
            ]),
            ("5. Important Rules", [
                [
                    f"The VPN disconnects automatically after {VPN_SESSION_HOURS} hours. Reconnect to "
                    "continue working.",
                    "Split tunnelling is disabled: all internet traffic goes through the company network "
                    "while connected.",
                    "Do not share your VPN session or credentials with anyone.",
                ],
            ]),
            ("6. Common Errors", [
                [
                    "Error E-401 (Authentication failed): check your password; if your account is locked, "
                    f"wait {LOCKOUT_MINUTES} minutes or reset your password.",
                    "Error E-503 (Gateway busy): wait 2 minutes and try again.",
                    "Error E-720 (Network adapter problem): restart the laptop; if it continues, "
                    "reinstall the client from NovaStore.",
                    "Connected but cannot open internal sites: disconnect, wait 30 seconds and reconnect.",
                ],
                f"If the problem continues, contact the IT helpdesk at extension {HELPDESK_EXT} or "
                f"{IT_EMAIL}.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ IT-003
    {
        "doc_code": "IT-003", "title": "Password Reset Guide", "department": "IT",
        "document_type": "Guide", "version": "1.8", "created": "2025-01-28",
        "access_level": "Employee", "format": "txt",
        "sections": [
            ("1. Password Rules", [
                [
                    f"At least {PASSWORD_MIN} characters long.",
                    "Must contain an uppercase letter, a lowercase letter, a number and a special character.",
                    f"Passwords expire every {PASSWORD_EXPIRY_DAYS} days; you get reminders 14 days before.",
                    f"You cannot reuse any of your last {PASSWORD_HISTORY} passwords.",
                    f"After {LOCKOUT_ATTEMPTS} wrong attempts, the account is locked for "
                    f"{LOCKOUT_MINUTES} minutes.",
                ],
            ]),
            ("2. Resetting Your Password (Self-Service)", [
                [
                    f"Go to {ID_PORTAL} from any browser.",
                    "Click 'Forgot password'.",
                    "Enter your TechNova email address.",
                    f"Approve the verification request in the {MFA_APP} app.",
                    "Enter and confirm your new password.",
                    "Sign in again on your laptop, NovaChat and email using the new password.",
                ],
            ]),
            ("3. Changing Your Password Before It Expires", [
                f"Sign in to {ID_PORTAL}, open 'Security' and click 'Change password'. On Windows you "
                "can also press Ctrl+Alt+Delete and choose 'Change a password' while connected to the "
                "office network or the VPN.",
            ]),
            ("4. Lost Phone or MFA Problems", [
                f"If you lost the phone with {MFA_APP}, you cannot use self-service reset. Call the IT "
                f"helpdesk at extension {HELPDESK_EXT}. For security, the helpdesk will verify your "
                "identity using your employee ID and a confirmation from your reporting manager before "
                "resetting your MFA.",
            ]),
            ("5. Safety Tips", [
                [
                    "IT will never ask for your password by email, phone or chat.",
                    "Use a passphrase such as three or four random words with numbers and symbols.",
                    "Never write your password on paper or share it with colleagues.",
                ],
            ]),
        ],
    },
    # ------------------------------------------------------------------ IT-004
    {
        "doc_code": "IT-004", "title": "Network Troubleshooting Manual", "department": "IT",
        "document_type": "Manual", "version": "2.0", "created": "2025-04-02",
        "access_level": "IT", "format": "docx",
        "sections": [
            ("1. Purpose", [
                "This manual contains the internal network layout and troubleshooting steps for the IT "
                "team. It contains sensitive infrastructure details and is restricted to IT staff.",
            ]),
            ("2. Office Network Layout", [
                [
                    f"Bengaluru office subnet: {BLR_SUBNET}",
                    f"Pune office subnet: {PUNE_SUBNET}",
                    f"Hyderabad office subnet: {HYD_SUBNET}",
                    f"Bengaluru core switch: {CORE_SWITCH}",
                    f"Internal DNS servers: {DNS_SERVERS}",
                ],
            ]),
            ("3. Wi-Fi Networks", [
                [
                    "TechNova-Corp - for company laptops; uses certificate-based (802.1X) authentication.",
                    "TechNova-Guest - for visitors and personal phones; internet only, isolated from "
                    "the corporate network; passwords rotate weekly.",
                ],
            ]),
            ("4. Troubleshooting: User Cannot Connect", [
                [
                    "Check whether the problem affects one user or many (check the monitoring dashboard).",
                    "Ask the user to run 'ipconfig /all' and confirm the IP address belongs to the "
                    "office subnet.",
                    "If the address starts with 169.254, DHCP failed: check the access switch port and "
                    "the DHCP scope usage.",
                    f"Test name resolution with 'nslookup {HELP_PORTAL}'. If it fails, check the DNS "
                    "servers.",
                    "For TechNova-Corp Wi-Fi failures, check that the device certificate is valid and "
                    "not expired.",
                ],
            ]),
            ("5. Troubleshooting: Slow Network", [
                [
                    "Check uplink utilisation on the core switch; above 80% for 15 minutes is a P2.",
                    "Look for broadcast storms or a looping cable on the affected floor switch.",
                    "Run a speed test against the internal test server and compare with the baseline.",
                ],
            ]),
            ("6. Change Management", [
                "Any change to core switches, firewalls or DNS must be approved in the Change Advisory "
                "Board (CAB), which meets every Thursday. Emergency changes need approval from the IT "
                "Security Manager and must be documented within 24 hours.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ IT-005
    {
        "doc_code": "IT-005", "title": "Cybersecurity Guidelines", "department": "IT",
        "document_type": "Guideline", "version": "3.1", "created": "2025-02-18",
        "access_level": "Employee", "format": "pdf",
        "sections": [
            ("1. Why Security Matters", [
                f"Every employee is responsible for protecting {COMPANY}, our customers and our data. "
                "Most security incidents start with a simple mistake, such as clicking a phishing link.",
            ]),
            ("2. Data Classification", [
                [
                    "Public - can be shared with anyone (for example, the company website).",
                    "Internal - for employees only (for example, most policies).",
                    "Confidential - for specific teams (for example, customer data, financial results).",
                    "Restricted - highest protection (for example, salary data, security keys).",
                ],
            ]),
            ("3. Phishing", [
                [
                    "Check the sender address carefully before clicking links or opening attachments.",
                    "Be suspicious of urgent requests for money, gift cards or passwords.",
                    f"Report suspicious emails using the 'Report Phish' button in email or forward them "
                    f"to {SECURITY_EMAIL}.",
                ],
            ]),
            ("4. Device Security", [
                [
                    f"Your screen locks automatically after {SCREEN_LOCK_MINUTES} minutes of inactivity; "
                    "lock it manually (Windows key + L) whenever you leave your desk.",
                    "Disk encryption is enabled on all company laptops and must not be turned off.",
                    "USB storage devices are blocked on company laptops.",
                    "Install software only from NovaStore (see the Software Installation Policy, IT-006).",
                ],
            ]),
            ("5. Accounts and Passwords", [
                f"Use multi-factor authentication with {MFA_APP} for all company systems. Follow the "
                "password rules in the Password Reset Guide (IT-003).",
            ]),
            ("6. Reporting a Security Incident", [
                f"Report any suspected security incident (lost laptop, clicked a phishing link, data sent "
                f"to the wrong person) within {INCIDENT_REPORT_HOURS} hour to {SECURITY_EMAIL} or the IT "
                f"helpdesk at extension {HELPDESK_EXT}. Reporting quickly is never punished; hiding an "
                "incident is a policy violation.",
            ]),
            ("7. AI Tools", [
                "Do not paste confidential or restricted company data, customer data or source code "
                "into public AI tools. Use only AI tools approved by IT.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ IT-006
    {
        "doc_code": "IT-006", "title": "Software Installation Policy", "department": "IT",
        "document_type": "Policy", "version": "1.5", "created": "2025-03-03",
        "access_level": "Employee", "format": "txt",
        "sections": [
            ("1. Purpose", [
                "This policy explains how employees can get software for their company laptops in a "
                "safe and legal way.",
            ]),
            ("2. Approved Software (NovaStore)", [
                f"{SOFTWARE_STORE} is the self-service software catalog on every company laptop. "
                "Software in NovaStore is licensed, security-checked and can be installed without a ticket.",
            ]),
            ("3. Requesting Software Not in NovaStore", [
                [
                    f"Raise a ticket at {HELP_PORTAL} under 'Software Request'.",
                    "Explain the business need and attach your manager's approval.",
                    f"IT Security reviews the request within {SOFTWARE_REVIEW_DAYS} working days.",
                    "If approved, the software is added to NovaStore or installed by IT.",
                ],
            ]),
            ("4. Prohibited Software", [
                [
                    "Unlicensed or pirated software.",
                    "Torrent and peer-to-peer file sharing clients.",
                    "Personal cloud storage sync clients.",
                    "Remote access tools not approved by IT.",
                    "Browser extensions that read all website data, unless approved.",
                ],
            ]),
            ("5. Admin Rights", [
                "Employees do not have local administrator rights on company laptops. Developers who "
                "need elevated rights for their work can request temporary elevation through the "
                "helpdesk, which lasts up to 8 hours.",
            ]),
            ("6. Violations", [
                "Unapproved software is removed automatically by device management. Repeated violations "
                "are reported to the employee's manager and HR.",
            ]),
        ],
    },
]
