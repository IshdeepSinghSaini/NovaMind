"""
facts.py - The single source of truth for every important fact about TechNova Solutions.

Every document uses these values, so documents never contradict each other
(for example, the Leave Policy and the FAQ always say the same number of leave days).
Later, the evaluation questions (Phase 14) check the AI's answers against these facts.

ALL DATA IS FICTIONAL. TechNova Solutions is not a real company.
Amounts use "INR" instead of the rupee symbol so every PDF font can display them.
"""

# ---- Company ----
COMPANY = "TechNova Solutions"
COMPANY_LEGAL = "TechNova Solutions Pvt. Ltd."
FOUNDED = 2012
HQ = "Bengaluru, India"
OFFICES = ["Bengaluru (headquarters)", "Pune", "Hyderabad", "Singapore"]
EMPLOYEES = "about 1,200"
PRODUCT = "NovaTrack"

# ---- Internal tools (fictional) ----
HR_PORTAL = "PeopleHub"
EXPENSE_PORTAL = "ExpenseHub"
CHAT_TOOL = "NovaChat"
VPN_CLIENT = "NovaSecure VPN"
MFA_APP = "NovaAuth"
SOFTWARE_STORE = "NovaStore"
ID_PORTAL = "id.technova.internal"
HELP_PORTAL = "help.technova.internal"
VPN_SERVER = "vpn.technova.internal"

# ---- Contacts (fictional .test addresses) ----
HR_EMAIL = "hr@technova.test"
IT_EMAIL = "itsupport@technova.test"
SECURITY_EMAIL = "security@technova.test"
FINANCE_EMAIL = "finance@technova.test"
ETHICS_EMAIL = "ethics@technova.test"
HELPDESK_EXT = "4357"
HELPDESK_HOURS = "8:00 AM to 9:00 PM IST, Monday to Saturday"

# ---- Working time ----
WORK_HOURS = "9:30 AM to 6:30 PM, Monday to Friday"
CORE_HOURS = "11:00 AM to 4:00 PM"
LATE_AFTER = "10:00 AM"
LATE_MARKS_LIMIT = 3  # 3 late marks in a month = half-day leave deducted
REGULARIZE_DAYS = 5   # working days to correct attendance

# ---- Leave ----
ANNUAL_LEAVE = 24          # paid annual leave days per calendar year
ACCRUAL_PER_MONTH = 2
CARRY_FORWARD_MAX = 10
SICK_LEAVE = 10
SICK_CERT_AFTER = 2        # medical certificate if more than 2 consecutive sick days
PUBLIC_HOLIDAYS = 12
MATERNITY_WEEKS = 26
PATERNITY_DAYS = 10
BEREAVEMENT_DAYS = 5
LEAVE_NOTICE_DAYS = 7      # apply 7 days ahead for leave of 3+ days
PROBATION_MONTHS = 6
PROBATION_LEAVE_MAX = 6

# ---- Work from home ----
OFFICE_DAYS_MIN = 3
WFH_DAYS_MAX = 2
ANCHOR_DAYS = "Tuesday and Wednesday"
INTERNET_ALLOWANCE = "INR 1,500 per month"
FULL_REMOTE_MAX_MONTHS = 3

# ---- Benefits ----
HEALTH_COVER = "INR 5,00,000"
LIFE_COVER = "3 times annual CTC"
MEAL_CARD = "INR 2,200 per month"
LEARNING_BUDGET = "INR 40,000 per year"
GYM_ALLOWANCE = "INR 1,500 per month"
EAP_SESSIONS = 6
PAYDAY = "the last working day of every month"

# ---- HR (restricted) ----
NOTICE_PERIOD = "60 days"
NOTICE_PERIOD_SENIOR = "90 days (Level L5 and above)"
PIP_DAYS = 60
GRIEVANCE_DAYS = 15

# ---- Salary bands (HR-only, restricted) ----
SALARY_BANDS = [
    ("L1", "Associate Engineer", "INR 6,00,000 - 9,00,000", "10%"),
    ("L2", "Software Engineer", "INR 9,00,000 - 14,00,000", "10%"),
    ("L3", "Software Engineer II", "INR 14,00,000 - 22,00,000", "10%"),
    ("L4", "Senior Software Engineer", "INR 22,00,000 - 32,00,000", "15%"),
    ("L5", "Lead Engineer", "INR 32,00,000 - 45,00,000", "15%"),
    ("L6", "Principal Engineer / Engineering Manager", "INR 45,00,000 - 65,00,000", "20%"),
]

# ---- IT ----
PASSWORD_MIN = 12
PASSWORD_EXPIRY_DAYS = 90
PASSWORD_HISTORY = 5
LOCKOUT_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
SCREEN_LOCK_MINUTES = 5
VPN_SESSION_HOURS = 12
INCIDENT_REPORT_HOURS = 1
SOFTWARE_REVIEW_DAYS = 3
# restricted IT details
ADMIN_PREFIX = "adm-"
BLR_SUBNET = "10.20.0.0/16"
PUNE_SUBNET = "10.30.0.0/16"
HYD_SUBNET = "10.40.0.0/16"
CORE_SWITCH = "tn-blr-core-01"
DNS_SERVERS = "10.20.0.10 and 10.20.0.11"

# ---- Finance ----
CLAIM_DEADLINE_DAYS = 30
RECEIPT_REQUIRED_ABOVE = "INR 500"
REIMBURSE_DAYS = 10
HOTEL_METRO = "INR 7,000 per night"
HOTEL_NON_METRO = "INR 4,500 per night"
HOTEL_INTL = "USD 180 per night"
PER_DIEM_DOMESTIC = "INR 1,500 per day"
PER_DIEM_INTL = "USD 60 per day"
TRAVEL_ADVANCE = "75%"
MANAGER_APPROVAL_DAYS = 5
PAYMENT_CYCLE = "the 7th and the 22nd of every month"
# restricted finance details
APPROVAL_MATRIX = [
    ("Up to INR 25,000", "Reporting manager"),
    ("INR 25,001 to INR 1,00,000", "Department head"),
    ("INR 1,00,001 to INR 5,00,000", "Finance Controller"),
    ("Above INR 5,00,000", "Chief Financial Officer (CFO)"),
]
AUDIT_SAMPLE = "10%"
VENDOR_TERMS = "Net 45 days"
PAYMENT_RUN_DAY = "every Friday"
INVOICE_TOLERANCE = "2%"

# ---- Product: NovaTrack ----
NT_VERSION = "4.2"
NT_PLANS = [
    ("Starter", "Free for up to 10 users"),
    ("Team", "USD 8 per user per month"),
    ("Enterprise", "Custom pricing; adds SSO, audit logs and 99.95% uptime SLA"),
]
NT_SLA = "99.9%"
NT_SLA_ENTERPRISE = "99.95%"
NT_API_BASE = "https://api.novatrack.example/v2"
NT_RATE_LIMIT = "600 requests per minute per API token"
NT_PAGE_MAX = 100
NT_REGIONS = ["India (Mumbai)", "Singapore", "Europe (Frankfurt)"]
