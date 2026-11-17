"""HR department documents (fictional). A section item: str = paragraph, list = bullet points."""

from sample_docs.facts import *  # noqa: F401,F403

DOCUMENTS = [
    # ------------------------------------------------------------------ HR-001
    {
        "doc_code": "HR-001", "title": "HR Policy", "department": "HR",
        "document_type": "Policy", "version": "4.0", "created": "2025-01-10",
        "access_level": "HR", "format": "pdf",
        "sections": [
            ("1. Purpose and Scope", [
                f"This HR Policy describes the internal procedures that the Human Resources team of "
                f"{COMPANY} follows when handling employee relations, performance management, "
                f"disciplinary matters, grievances and exits. It is an internal document for the HR "
                f"team only and must not be shared with other employees.",
                "Employee-facing rules such as leave, attendance and work from home are published "
                "separately in their own policies, which all employees can read.",
            ]),
            ("2. Employee Records and Confidentiality", [
                f"All employee records are stored in {HR_PORTAL}. Only HR business partners and HR "
                "operations staff may view personal files, compensation details, medical documents "
                "and investigation notes.",
                [
                    "Personal files are retained for 7 years after an employee leaves.",
                    "Medical documents are stored in a separate restricted folder.",
                    "Investigation notes are visible only to the HR case owner and the Head of HR.",
                    "Any request from outside HR for employee data must be approved by the Head of HR.",
                ],
            ]),
            ("3. Performance Improvement Plan (PIP)", [
                f"An employee who receives a rating of 'Below Expectations' in two consecutive "
                f"quarterly reviews is placed on a Performance Improvement Plan (PIP) lasting "
                f"{PIP_DAYS} days.",
                [
                    "The manager and HR business partner prepare written, measurable goals.",
                    "Progress check-ins happen every two weeks and are documented in PeopleHub.",
                    "At the end of the PIP, the outcome is one of: successful completion, an "
                    "extension of up to 30 days, or initiation of the separation process.",
                ],
            ]),
            ("4. Disciplinary Procedure", [
                "TechNova follows a progressive disciplinary procedure. Each step must be documented "
                "and the employee must receive a copy.",
                [
                    "Step 1 - Verbal warning, recorded as a file note.",
                    "Step 2 - Written warning, valid for 6 months.",
                    "Step 3 - Final written warning, valid for 12 months.",
                    "Step 4 - Termination of employment.",
                ],
                "Gross misconduct, such as fraud, violence, harassment or deliberate data theft, may "
                "lead directly to suspension and termination after an investigation. During an "
                "investigation, the employee may be placed on paid administrative leave.",
            ]),
            ("5. Grievance Handling", [
                f"Grievances raised by employees are logged as HR cases in {HR_PORTAL} with a case "
                f"code in the format HRC-YYYY-NNNN. The HR case owner must acknowledge a grievance "
                f"within 2 working days and resolve it within {GRIEVANCE_DAYS} working days.",
                "If the employee is not satisfied with the outcome, they may appeal to the Head of HR "
                "within 10 working days. The appeal decision is final.",
            ]),
            ("6. Background Verification", [
                "Every new hire must complete background verification before or within 30 days of "
                "joining. Verification covers identity, education, previous employment and address. "
                "A failed or falsified verification is treated as gross misconduct.",
            ]),
            ("7. Resignation and Exit", [
                f"The standard notice period is {NOTICE_PERIOD}, and {NOTICE_PERIOD_SENIOR}. Notice "
                "may be shortened only with the approval of the department head and HR.",
                [
                    "HR schedules an exit interview in the last week of employment.",
                    "IT revokes all system access on the last working day at 6:30 PM.",
                    "Full and final settlement is processed within 45 days of the last working day.",
                    "Experience and relieving letters are issued after settlement.",
                ],
            ]),
        ],
    },
    # ------------------------------------------------------------------ HR-002
    {
        "doc_code": "HR-002", "title": "Annual Leave Policy", "department": "HR",
        "document_type": "Policy", "version": "2.1", "created": "2025-03-01",
        "access_level": "Employee", "format": "pdf",
        "sections": [
            ("1. Purpose", [
                f"This policy explains the types of leave available to employees of {COMPANY}, how "
                "much leave employees get, and how to apply for it. Taking regular time off is "
                "important for health and productivity, and managers are expected to encourage it.",
            ]),
            ("2. Eligibility", [
                "This policy applies to all full-time permanent employees in India. Contract staff and "
                "interns follow the terms written in their individual contracts.",
            ]),
            ("3. Annual (Paid) Leave Entitlement", [
                f"Every full-time employee is entitled to {ANNUAL_LEAVE} days of paid annual leave per "
                f"calendar year (January to December). Annual leave is earned at the rate of "
                f"{ACCRUAL_PER_MONTH} days per completed month of service.",
                [
                    f"Employees who join during the year receive leave on a pro-rata basis "
                    f"({ACCRUAL_PER_MONTH} days for each full month remaining in the year).",
                    f"During the {PROBATION_MONTHS}-month probation period, leave is earned normally, "
                    f"but a maximum of {PROBATION_LEAVE_MAX} days of annual leave can be used.",
                    "Annual leave cannot be taken in advance of being earned, except with HR approval.",
                ],
            ]),
            ("4. Carry Forward", [
                f"At the end of the calendar year, up to {CARRY_FORWARD_MAX} unused annual leave days "
                f"can be carried forward to the next year. Any unused days above {CARRY_FORWARD_MAX} "
                "lapse on 31 December and cannot be paid out in cash.",
            ]),
            ("5. Sick Leave", [
                f"Employees receive {SICK_LEAVE} days of paid sick leave per calendar year. Sick leave "
                "cannot be carried forward.",
                f"For sick leave of more than {SICK_CERT_AFTER} consecutive days, a medical certificate "
                f"from a registered doctor must be uploaded in {HR_PORTAL} within 3 days of returning.",
            ]),
            ("6. Other Types of Leave", [
                [
                    f"Public holidays: {PUBLIC_HOLIDAYS} days per year. The list is published in "
                    f"{HR_PORTAL} every December for the following year.",
                    f"Maternity leave: {MATERNITY_WEEKS} weeks of fully paid leave.",
                    f"Paternity leave: {PATERNITY_DAYS} working days of paid leave, to be used within "
                    "6 months of the child's birth or adoption.",
                    f"Bereavement leave: {BEREAVEMENT_DAYS} working days of paid leave on the death of "
                    "an immediate family member.",
                    "Marriage leave: 3 working days of paid leave, once during employment.",
                ],
            ]),
            ("7. How to Apply for Leave", [
                f"All leave must be applied for in {HR_PORTAL} under 'My Leave'.",
                [
                    f"For leave of 3 or more consecutive days, apply at least {LEAVE_NOTICE_DAYS} days "
                    "in advance.",
                    "For 1 or 2 days of planned leave, apply at least 1 working day in advance.",
                    "Unplanned sick leave must be informed to the manager by 10:00 AM on the same day "
                    "and applied in PeopleHub within 2 working days of returning.",
                    "The reporting manager approves or rejects the request within 2 working days.",
                ],
            ]),
            ("8. Leave Without Pay", [
                "If an employee has no leave balance, leave without pay (LWP) may be granted by the "
                "manager and HR for up to 30 days in a year. LWP reduces the salary for those days.",
            ]),
            ("9. Questions", [
                f"For questions about leave balances or this policy, contact the HR team at {HR_EMAIL} "
                f"or raise a request in {HR_PORTAL}.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ HR-003
    {
        "doc_code": "HR-003", "title": "Work From Home Policy", "department": "HR",
        "document_type": "Policy", "version": "3.0", "created": "2025-02-15",
        "access_level": "Employee", "format": "docx",
        "sections": [
            ("1. Purpose", [
                f"{COMPANY} follows a hybrid working model. This policy explains when employees can "
                "work from home (WFH), what is expected of them, and how remote work is supported.",
            ]),
            ("2. Hybrid Working Model", [
                f"Employees must work from the office at least {OFFICE_DAYS_MIN} days per week and may "
                f"work from home for up to {WFH_DAYS_MAX} days per week.",
                [
                    f"{ANCHOR_DAYS} are mandatory office days (anchor days) for all teams, so that "
                    "teams can meet in person.",
                    "The remaining WFH days are agreed between the employee and the manager.",
                    "Unused WFH days cannot be carried over to the next week.",
                ],
            ]),
            ("3. Eligibility", [
                f"All permanent employees who have completed their {PROBATION_MONTHS}-month probation "
                "are eligible. During probation, employees work from the office every day unless the "
                "manager approves otherwise.",
                "Roles that need physical presence (for example, front desk, facilities and hardware "
                "lab staff) are not eligible for regular WFH.",
            ]),
            ("4. Expectations While Working From Home", [
                [
                    f"Be available during core hours ({CORE_HOURS}) on {CHAT_TOOL} and email.",
                    f"Always connect to company systems through the {VPN_CLIENT} client.",
                    "Work from a private, safe place. Do not work on confidential data in public places "
                    "such as cafes.",
                    "Keep the camera on for team meetings unless there is a valid reason.",
                    "Mark the WFH day in PeopleHub under 'My Attendance'.",
                ],
            ]),
            ("5. Equipment and Internet Allowance", [
                f"Employees receive an internet allowance of {INTERNET_ALLOWANCE}, paid with salary. "
                "The company laptop must be used for all work. Personal computers must not be used to "
                "access company data.",
                "Employees may request a monitor and a keyboard for home use through the IT helpdesk. "
                "These remain company property and must be returned when leaving the company.",
            ]),
            ("6. Fully Remote Work (Exceptions)", [
                f"In special situations (for example, medical reasons or family care), an employee may "
                f"request fully remote work for up to {FULL_REMOTE_MAX_MONTHS} months. This needs "
                "approval from the reporting manager, the department head and HR.",
            ]),
            ("7. Misuse", [
                "Repeatedly being unreachable during core hours or misreporting attendance is a "
                "violation of this policy and may lead to WFH privileges being withdrawn and "
                "disciplinary action.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ HR-004
    {
        "doc_code": "HR-004", "title": "Employee Onboarding Guide", "department": "HR",
        "document_type": "Guide", "version": "2.3", "created": "2025-04-05",
        "access_level": "Employee", "format": "docx",
        "sections": [
            ("1. Welcome to TechNova", [
                f"Welcome to {COMPANY}! This guide helps new employees through their first 90 days. "
                "Please read it in your first week and keep it handy.",
            ]),
            ("2. Before Day One", [
                [
                    f"You will receive your {HR_PORTAL} login on your personal email 3 days before joining.",
                    "Upload your identity proof, education certificates and bank details in PeopleHub.",
                    "Complete the background verification form sent by HR.",
                ],
            ]),
            ("3. Your First Day", [
                [
                    "Report to the reception at 9:30 AM. Your HR onboarding partner will meet you.",
                    "Collect your ID card, company laptop and welcome kit.",
                    f"IT will help you set up your password, the {MFA_APP} app for multi-factor "
                    f"authentication, and the {VPN_CLIENT} client.",
                    "You will be introduced to your onboarding buddy, an experienced colleague from "
                    "your team who helps you settle in.",
                ],
            ]),
            ("4. Mandatory Trainings (within 14 days)", [
                "All new employees must complete the following trainings in PeopleHub within 14 days "
                "of joining:",
                [
                    "Information Security Awareness",
                    "Employee Code of Conduct",
                    "Prevention of Sexual Harassment (POSH) at the workplace",
                    "Data Privacy Basics",
                ],
            ]),
            ("5. The 30-60-90 Day Plan", [
                "Your manager will share a 30-60-90 day plan in your first week.",
                [
                    "First 30 days: learn about the team, products and tools; complete trainings.",
                    "Days 31-60: take ownership of small tasks and contribute to team work.",
                    "Days 61-90: work independently on regular tasks and agree on goals for the year.",
                ],
            ]),
            ("6. Probation", [
                f"The probation period is {PROBATION_MONTHS} months. At the end, your manager completes a "
                "probation review in PeopleHub. On successful completion you receive a confirmation letter.",
            ]),
            ("7. Useful Contacts", [
                [
                    f"HR team: {HR_EMAIL}",
                    f"IT helpdesk: extension {HELPDESK_EXT} or {IT_EMAIL}",
                    f"Finance and reimbursements: {FINANCE_EMAIL}",
                ],
            ]),
        ],
    },
    # ------------------------------------------------------------------ HR-005
    {
        "doc_code": "HR-005", "title": "Employee Benefits", "department": "HR",
        "document_type": "Policy", "version": "2.0", "created": "2025-01-20",
        "access_level": "Employee", "format": "pdf",
        "sections": [
            ("1. Overview", [
                f"{COMPANY} offers a range of benefits to support the health, wellbeing and growth of "
                "employees and their families. Benefits start from the date of joining unless stated "
                "otherwise.",
            ]),
            ("2. Health Insurance", [
                f"All employees are covered by a group health insurance policy with a sum insured of "
                f"{HEALTH_COVER} per year on a family floater basis.",
                [
                    "Covered members: employee, spouse and up to 2 children.",
                    "Parents and parents-in-law can be added through an optional top-up plan; the "
                    "premium for parents is paid by the employee through salary deduction.",
                    "Cashless treatment is available at network hospitals.",
                    "New family members (for example, after marriage or childbirth) must be added "
                    "within 30 days of the event.",
                ],
            ]),
            ("3. Life and Accident Insurance", [
                f"Term life insurance cover of {LIFE_COVER} and personal accident cover are provided "
                "at no cost to the employee.",
            ]),
            ("4. Meal Card", [
                f"Employees receive a meal card of {MEAL_CARD}, which can be used at the office "
                "cafeteria and partner restaurants.",
            ]),
            ("5. Learning and Development", [
                f"Each employee has a learning budget of {LEARNING_BUDGET}. It can be used for "
                "certifications, online courses, books and conference tickets related to the "
                "employee's role.",
                [
                    "Manager approval is required before purchase.",
                    f"Claims are submitted in {EXPENSE_PORTAL} under the 'Learning' category.",
                    "If an employee leaves within 12 months of a certification paid by the company, "
                    "the certification cost may be recovered.",
                ],
            ]),
            ("6. Wellness", [
                [
                    f"Gym or fitness reimbursement: {GYM_ALLOWANCE}.",
                    f"Employee Assistance Programme (EAP): {EAP_SESSIONS} free and confidential "
                    "counselling sessions per year for employees and their family members.",
                    "Annual health check-up for employees aged 30 and above.",
                ],
            ]),
            ("7. Salary and Payday", [
                f"Salary is paid on {PAYDAY}. Payslips are available in {HR_PORTAL}.",
            ]),
            ("8. Questions", [
                f"For questions about benefits, contact {HR_EMAIL}.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ HR-006
    {
        "doc_code": "HR-006", "title": "Attendance Policy", "department": "HR",
        "document_type": "Policy", "version": "1.4", "created": "2025-02-01",
        "access_level": "Employee", "format": "txt",
        "sections": [
            ("1. Purpose", [
                "This policy explains working hours, how attendance is recorded, and what happens "
                "in case of late arrival or missing attendance.",
            ]),
            ("2. Working Hours", [
                f"Standard working hours are {WORK_HOURS}, with a one-hour lunch break. Core hours are "
                f"{CORE_HOURS}; all employees must be available during core hours, whether working "
                "from the office or from home.",
            ]),
            ("3. Recording Attendance", [
                [
                    "In the office, attendance is recorded automatically when you swipe your ID card "
                    "at the entrance.",
                    f"When working from home, mark your attendance in {HR_PORTAL} under 'My Attendance' "
                    "before 10:00 AM.",
                    "When on client visits or business travel, mark 'On Duty' in PeopleHub.",
                ],
            ]),
            ("4. Late Arrival", [
                f"Arriving after {LATE_AFTER} is recorded as a late mark. {LATE_MARKS_LIMIT} late marks "
                "in one calendar month result in a half-day of annual leave being deducted. Managers "
                "may excuse late marks caused by genuine emergencies.",
            ]),
            ("5. Attendance Regularization", [
                f"If you forgot to swipe or mark attendance, submit a regularization request in "
                f"{HR_PORTAL} within {REGULARIZE_DAYS} working days. After this period, the day is "
                "treated as leave without pay unless HR approves an exception.",
            ]),
            ("6. Unplanned Absence", [
                "If you cannot come to work unexpectedly, inform your manager by 10:00 AM by phone or "
                "NovaChat. Being absent for 3 consecutive working days without informing anyone is "
                "treated as unauthorized absence and may lead to disciplinary action.",
            ]),
        ],
    },
    # ------------------------------------------------------------------ HR-007
    {
        "doc_code": "HR-007", "title": "Salary Bands and Compensation Guidelines", "department": "HR",
        "document_type": "Guideline", "version": "2026.1", "created": "2026-01-15",
        "access_level": "HR", "format": "pdf",
        "sections": [
            ("1. Confidentiality Notice", [
                "This document contains confidential compensation information. It is restricted to "
                "the HR team. Sharing salary band information with employees or outside the company is "
                "a serious policy violation.",
            ]),
            ("2. Engineering Salary Bands (Annual CTC)", [
                "The following annual cost-to-company (CTC) ranges apply to engineering roles in India "
                "for the financial year starting April 2026:",
                [f"{lvl} - {role}: {band} (target bonus {bonus} of CTC)"
                 for lvl, role, band, bonus in SALARY_BANDS],
            ]),
            ("3. Placement Within a Band", [
                [
                    "New hires are normally placed between the minimum and the midpoint of the band.",
                    "Offers above the midpoint need approval from the Head of HR.",
                    "Offers above the band maximum are not allowed without CEO approval.",
                ],
            ]),
            ("4. Annual Increment Cycle", [
                "Salary increments are effective from 1 April every year, based on the annual "
                "performance rating:",
                [
                    "Exceeds Expectations: 10% to 15% increase.",
                    "Meets Expectations: 6% to 9% increase.",
                    "Partially Meets Expectations: 0% to 4% increase.",
                    "Below Expectations: no increase.",
                ],
            ]),
            ("5. Promotions", [
                "A promotion to the next level comes with a minimum increase of 12% or placement at the "
                "minimum of the new band, whichever is higher. Promotions are reviewed twice a year, in "
                "April and October.",
            ]),
        ],
    },
]
