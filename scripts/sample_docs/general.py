"""General company documents (fictional). A section item: str = paragraph, list = bullet points."""

from sample_docs.facts import *  # noqa: F401,F403

DOCUMENTS = [
    # ----------------------------------------------------------------- GEN-001
    {
        "doc_code": "GEN-001", "title": "Company Overview", "department": "General",
        "document_type": "Overview", "version": "5.0", "created": "2025-01-05",
        "access_level": "Public", "format": "pdf",
        "sections": [
            ("1. Who We Are", [
                f"{COMPANY_LEGAL} is a software company founded in {FOUNDED} and headquartered in "
                f"{HQ}. We build {PRODUCT}, a project management and issue tracking platform used by "
                f"software teams around the world. TechNova has {EMPLOYEES} employees.",
            ]),
            ("2. Our Mission", [
                "Our mission is to help teams plan, track and deliver great software with less effort "
                "and more clarity.",
            ]),
            ("3. Our Values", [
                [
                    "Customer First - we start with the customer's problem.",
                    "Ownership - we take responsibility for outcomes, not just tasks.",
                    "Integrity - we do the right thing, even when no one is watching.",
                    "Learn Always - we stay curious and keep improving.",
                ],
            ]),
            ("4. Our Offices", [
                "TechNova has offices in the following locations:",
                OFFICES,
            ]),
            ("5. Our History", [
                [
                    f"{FOUNDED}: TechNova is founded in Bengaluru with 8 people.",
                    "2015: The first version of NovaTrack is launched.",
                    "2018: The Pune and Hyderabad offices open.",
                    "2021: The Singapore office opens to serve customers in Southeast Asia.",
                    f"2025: NovaTrack {NT_VERSION} is released with automation and roadmap features.",
                ],
            ]),
            ("6. Leadership", [
                "The company is led by the Chief Executive Officer (CEO), supported by the Chief "
                "Technology Officer (CTO), the Chief Financial Officer (CFO), the Chief Product Officer "
                "(CPO) and the Head of Human Resources.",
            ]),
            ("7. Departments", [
                [
                    "Engineering - builds and runs NovaTrack.",
                    "Product - decides what to build and why.",
                    "Human Resources - hiring, people policies and employee wellbeing.",
                    "Finance - budgets, payments, reimbursements and invoices.",
                    "IT - laptops, networks, accounts and security.",
                    "Sales and Customer Success - help customers buy and succeed with NovaTrack.",
                ],
            ]),
        ],
    },
    # ----------------------------------------------------------------- GEN-002
    {
        "doc_code": "GEN-002", "title": "Company FAQ", "department": "General",
        "document_type": "FAQ", "version": "3.2", "created": "2025-05-12",
        "access_level": "Public", "format": "docx",
        "sections": [
            ("About This FAQ", [
                "This document answers the questions employees ask most often. For full details, "
                "always refer to the related policy document.",
            ]),
            ("Q: How many paid leaves do I get in a year?", [
                f"You get {ANNUAL_LEAVE} days of paid annual leave per calendar year, plus "
                f"{SICK_LEAVE} days of sick leave and {PUBLIC_HOLIDAYS} public holidays. See the "
                "Annual Leave Policy (HR-002).",
            ]),
            ("Q: How many days can I work from home?", [
                f"Up to {WFH_DAYS_MAX} days per week. {ANCHOR_DAYS} are mandatory office days. See the "
                "Work From Home Policy (HR-003).",
            ]),
            ("Q: When is salary paid?", [
                f"Salary is paid on {PAYDAY}. Payslips are available in {HR_PORTAL}.",
            ]),
            ("Q: How do I contact the IT helpdesk?", [
                f"Call extension {HELPDESK_EXT}, email {IT_EMAIL}, or raise a ticket at {HELP_PORTAL}. "
                f"The helpdesk is available {HELPDESK_HOURS}.",
            ]),
            ("Q: I forgot my password. What should I do?", [
                f"Use the self-service portal at {ID_PORTAL}. See the Password Reset Guide (IT-003).",
            ]),
            ("Q: How do I claim travel expenses?", [
                f"Submit your claim in {EXPENSE_PORTAL} within {CLAIM_DEADLINE_DAYS} days of the end of "
                "the trip, with receipts. See the Travel Reimbursement Policy (FIN-001).",
            ]),
            ("Q: I lost my ID card. What should I do?", [
                "Report it immediately to the Facilities desk and the IT helpdesk so that the card can "
                "be blocked. A replacement card costs INR 500 and is issued within 2 working days.",
            ]),
            ("Q: Is there a dress code?", [
                "Business casual from Monday to Thursday, and casual on Fridays. Client meetings require "
                "business formal clothing.",
            ]),
            ("Q: Where can I report unethical behaviour?", [
                f"Write to {ETHICS_EMAIL}. Reports can be anonymous. See the Employee Code of Conduct "
                "(GEN-003).",
            ]),
        ],
    },
    # ----------------------------------------------------------------- GEN-003
    {
        "doc_code": "GEN-003", "title": "Employee Code of Conduct", "department": "General",
        "document_type": "Policy", "version": "4.1", "created": "2025-01-05",
        "access_level": "Public", "format": "pdf",
        "sections": [
            ("1. Purpose", [
                f"This Code of Conduct describes the behaviour {COMPANY} expects from every employee, "
                "contractor and intern. Every employee must read it and accept it in PeopleHub every year.",
            ]),
            ("2. Respect and Anti-Harassment", [
                "TechNova has zero tolerance for harassment, bullying or discrimination based on gender, "
                "religion, caste, age, disability, sexual orientation or any other personal "
                "characteristic. Complaints of sexual harassment are handled by the Internal Committee "
                "under the POSH policy.",
            ]),
            ("3. Conflicts of Interest", [
                "Employees must avoid situations where personal interests conflict with the company's "
                "interests.",
                [
                    "Do not work for a competitor, customer or vendor while employed at TechNova.",
                    "Declare any family relationship with a vendor or candidate to HR.",
                    "Outside work (for example, freelancing) needs written approval from HR.",
                ],
            ]),
            ("4. Gifts and Hospitality", [
                "Employees may accept gifts from business partners only if the value is below INR 2,000 "
                "and the gift is not cash. Gifts above this value must be declared to the ethics team "
                "and returned politely.",
            ]),
            ("5. Protecting Company Information", [
                "Customer data, source code, financial results and employee information are "
                "confidential. Share them only with people who need them for their work. Follow the "
                "Cybersecurity Guidelines (IT-005).",
            ]),
            ("6. Use of Company Assets", [
                "Company laptops, accounts and tools are for business use. Limited personal use is "
                "allowed if it does not affect work or security. Never install unapproved software.",
            ]),
            ("7. Speaking Up (Whistleblowing)", [
                f"Report suspected violations to your manager, HR, or {ETHICS_EMAIL}. Reports can be "
                "made anonymously. TechNova strictly prohibits retaliation against anyone who reports "
                "a concern in good faith.",
            ]),
            ("8. Consequences", [
                "Violations of this Code may lead to disciplinary action, up to and including "
                "termination of employment.",
            ]),
        ],
    },
    # ----------------------------------------------------------------- GEN-004
    {
        "doc_code": "GEN-004", "title": "Communication Guidelines", "department": "General",
        "document_type": "Guideline", "version": "2.0", "created": "2025-03-18",
        "access_level": "Public", "format": "txt",
        "sections": [
            ("1. Purpose", [
                "These guidelines help employees choose the right communication channel and "
                "communicate clearly and professionally.",
            ]),
            ("2. Choosing the Right Channel", [
                [
                    "Email - formal communication, external communication, approvals and anything "
                    "that needs a record.",
                    f"{CHAT_TOOL} - quick questions and day-to-day team discussion.",
                    "Video meetings - discussions that need back-and-forth conversation.",
                    "Ticketing portals - requests to IT, HR or Finance (so they can be tracked).",
                ],
            ]),
            ("3. Response Times", [
                [
                    "Reply to internal emails within 1 business day.",
                    "Reply to customer emails within 4 business hours.",
                    "NovaChat messages during core hours should be answered within 2 hours.",
                ],
            ]),
            ("4. Meetings", [
                [
                    "Every meeting must have an agenda shared in the invitation.",
                    "Keep meetings to 30 minutes where possible.",
                    "Share notes and action items within 24 hours.",
                    "Avoid scheduling meetings outside core hours across time zones without agreement.",
                ],
            ]),
            ("5. External Communication", [
                "Only the Corporate Communications team may speak to the media or post official "
                "statements on behalf of TechNova. Employees must not share confidential information on "
                "social media.",
            ]),
            ("6. Tone and Etiquette", [
                "Be respectful, clear and concise. Avoid writing in all capital letters. Do not use "
                "NovaChat or email to give critical feedback - discuss it privately in person or on a call.",
            ]),
        ],
    },
    # ----------------------------------------------------------------- GEN-005
    {
        "doc_code": "GEN-005", "title": "Workplace Guidelines", "department": "General",
        "document_type": "Guideline", "version": "1.6", "created": "2025-02-22",
        "access_level": "Public", "format": "docx",
        "sections": [
            ("1. Office Hours and Access", [
                f"Offices are open from 8:00 AM to 10:00 PM on working days. Standard working hours are "
                f"{WORK_HOURS}. Always carry your ID card; tailgating (letting someone enter behind you "
                "without swiping) is not allowed.",
            ]),
            ("2. Visitors", [
                [
                    "Register visitors at reception at least 1 day in advance.",
                    "Visitors must wear a visitor badge and be accompanied at all times.",
                    "Visitors are not allowed in server rooms or hardware labs.",
                ],
            ]),
            ("3. Clean Desk", [
                "Clear your desk at the end of the day. Lock away confidential papers and never leave "
                "your laptop unlocked or unattended.",
            ]),
            ("4. Dress Code", [
                "Business casual from Monday to Thursday, and casual on Fridays. Business formal for "
                "client meetings.",
            ]),
            ("5. Cafeteria and Common Areas", [
                "The cafeteria is open from 8:30 AM to 8:00 PM. Meal cards can be used for payment. "
                "Please keep common areas clean and book meeting rooms through the calendar.",
            ]),
            ("6. Parking", [
                "Parking is available on a first-come, first-served basis. Two-wheeler and four-wheeler "
                "parking stickers are issued by the Facilities team.",
            ]),
            ("7. Health and Safety", [
                [
                    "Learn the location of the nearest emergency exit and fire extinguisher.",
                    "During a fire alarm, leave by the stairs (not the lift) and go to the assembly "
                    "point in the front parking area.",
                    "Report injuries and safety hazards to the Facilities desk immediately.",
                ],
            ]),
        ],
    },
]
