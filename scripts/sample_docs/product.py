"""Product documents about NovaTrack (fictional). A section item: str = paragraph, list = bullet points."""

from sample_docs.facts import *  # noqa: F401,F403

DOCUMENTS = [
    # ----------------------------------------------------------------- PRD-001
    {
        "doc_code": "PRD-001", "title": "NovaTrack Product Overview", "department": "Product",
        "document_type": "Overview", "version": NT_VERSION, "created": "2025-06-02",
        "access_level": "Employee", "format": "pdf",
        "sections": [
            ("1. What Is NovaTrack?", [
                f"{PRODUCT} is {COMPANY}'s main product: a cloud-based project management and issue "
                "tracking platform for software teams. It helps teams plan work, track issues, run "
                f"sprints and see progress in one place. The current version is {NT_VERSION}.",
            ]),
            ("2. Who Uses NovaTrack?", [
                [
                    "Software development teams using Scrum or Kanban.",
                    "Product managers planning roadmaps and releases.",
                    "Support teams tracking customer-reported bugs.",
                    "Engineering leaders who need reports on delivery and quality.",
                ],
            ]),
            ("3. Main Features", [
                [
                    "Boards - Kanban and Scrum boards with drag-and-drop issues.",
                    "Sprints - plan, start and close sprints with burndown charts.",
                    "Roadmaps - timeline view of epics and releases.",
                    "Automations - rules such as 'when a pull request is merged, move the issue to Done'.",
                    "Time tracking - log time on issues and view timesheets.",
                    "Reports - velocity, cycle time and bug trend reports.",
                    "Integrations - connect Git repositories, chat tools and CI pipelines.",
                ],
            ]),
            ("4. Pricing Plans", [
                [f"{name}: {desc}." for name, desc in NT_PLANS],
            ]),
            ("5. Availability and Data Regions", [
                f"NovaTrack is available with an uptime SLA of {NT_SLA} on the Team plan and "
                f"{NT_SLA_ENTERPRISE} on the Enterprise plan. Customers can choose to store data in "
                f"one of these regions: {', '.join(NT_REGIONS)}.",
            ]),
            ("6. What Makes NovaTrack Different", [
                [
                    "Fast setup: a new team can start in under 10 minutes with templates.",
                    "Simple pricing with a free plan for small teams.",
                    "Strong automation without writing code.",
                    "Data residency options for customers in Asia and Europe.",
                ],
            ]),
        ],
    },
    # ----------------------------------------------------------------- PRD-002
    {
        "doc_code": "PRD-002", "title": "NovaTrack Feature Documentation", "department": "Product",
        "document_type": "Documentation", "version": NT_VERSION, "created": "2025-06-10",
        "access_level": "Employee", "format": "docx",
        "sections": [
            ("1. Projects and Issues", [
                "A project is a container for work. Each project has issues, which can be of type Epic, "
                "Story, Task, Bug or Sub-task. Every issue has a key such as WEB-123, where WEB is the "
                "project key.",
                [
                    "Issue fields: title, description, assignee, reporter, priority, labels, due date, "
                    "story points and status.",
                    "Priorities: Highest, High, Medium, Low, Lowest.",
                    "Default workflow: To Do, In Progress, In Review, Done.",
                ],
            ]),
            ("2. Boards", [
                "Kanban boards show issues as cards in columns. Teams can set work-in-progress (WIP) "
                "limits per column; the column turns red when the limit is exceeded. Scrum boards show "
                "only the issues in the active sprint.",
            ]),
            ("3. Sprints", [
                [
                    "Create a sprint from the backlog and drag issues into it.",
                    "Default sprint length is 2 weeks (can be 1 to 4 weeks).",
                    "When a sprint is closed, unfinished issues move to the backlog or the next sprint.",
                    "The burndown chart shows remaining story points per day.",
                ],
            ]),
            ("4. Roadmaps", [
                "Roadmaps show epics on a timeline. Dependencies between epics are drawn as arrows; if a "
                "dependent epic is scheduled before the epic it depends on, NovaTrack shows a warning.",
            ]),
            ("5. Automations", [
                "Automations are 'when-if-then' rules. Each project can have up to 50 active rules on the "
                "Team plan and unlimited rules on Enterprise.",
                [
                    "Example: When an issue is moved to In Review, assign it to the team lead.",
                    "Example: When a Bug with Highest priority is created, post a message in the team chat.",
                    "Example: Every Monday at 9:00 AM, send a summary of overdue issues.",
                ],
            ]),
            ("6. Permissions", [
                "Project roles are Admin, Member and Viewer. Admins manage settings and members; Members "
                "create and edit issues; Viewers can only read. Enterprise customers can also use SSO and "
                "view audit logs of all admin actions.",
            ]),
            ("7. Notifications", [
                "Users get notifications for assigned issues, mentions and watched issues by email and in "
                "the app. Each user can change notification settings under Profile > Notifications.",
            ]),
        ],
    },
    # ----------------------------------------------------------------- PRD-003
    {
        "doc_code": "PRD-003", "title": "NovaTrack API Documentation", "department": "Product",
        "document_type": "Documentation", "version": NT_VERSION, "created": "2025-06-15",
        "access_level": "Employee", "format": "txt",
        "sections": [
            ("1. Overview", [
                f"The NovaTrack REST API lets customers integrate NovaTrack with their own tools. The base "
                f"URL is {NT_API_BASE}. All requests and responses use JSON.",
            ]),
            ("2. Authentication", [
                "Every request must include an API token in the Authorization header: "
                "'Authorization: Bearer <token>'. Users create tokens under Profile > API Tokens. Tokens "
                "expire after 1 year and can be revoked at any time.",
            ]),
            ("3. Rate Limits", [
                f"The API allows {NT_RATE_LIMIT}. When the limit is exceeded, the API returns HTTP 429 "
                "with a 'Retry-After' header telling the client how many seconds to wait.",
            ]),
            ("4. Main Endpoints", [
                [
                    "GET /projects - list projects.",
                    "GET /projects/{key}/issues - list issues in a project.",
                    "POST /issues - create an issue.",
                    "GET /issues/{key} - get one issue.",
                    "PATCH /issues/{key} - update fields of an issue.",
                    "POST /issues/{key}/comments - add a comment.",
                    "GET /sprints/{id} - get sprint details.",
                ],
            ]),
            ("5. Pagination", [
                f"List endpoints use cursor-based pagination. Use the 'limit' parameter (default 25, "
                f"maximum {NT_PAGE_MAX}) and pass the 'next_cursor' value from the response to get the "
                "next page.",
            ]),
            ("6. Webhooks", [
                "Webhooks send an HTTP POST to the customer's URL when events happen, such as "
                "issue.created, issue.updated and sprint.closed. Each webhook request is signed with an "
                "HMAC-SHA256 signature in the 'X-NovaTrack-Signature' header so customers can verify it.",
            ]),
            ("7. Error Codes", [
                [
                    "400 Bad Request - the request body is invalid.",
                    "401 Unauthorized - missing or invalid API token.",
                    "403 Forbidden - the token does not have permission.",
                    "404 Not Found - the project or issue does not exist.",
                    "429 Too Many Requests - rate limit exceeded.",
                    "500 Internal Server Error - contact support with the 'X-Request-Id' header value.",
                ],
            ]),
        ],
    },
    # ----------------------------------------------------------------- PRD-004
    {
        "doc_code": "PRD-004", "title": "NovaTrack Technical Architecture Guide", "department": "Product",
        "document_type": "Guide", "version": NT_VERSION, "created": "2025-07-01",
        "access_level": "Employee", "format": "pdf",
        "sections": [
            ("1. Architecture Summary", [
                "NovaTrack is built as a set of microservices running in containers on a Kubernetes "
                "cluster in each data region. Services communicate through REST APIs and an event bus.",
            ]),
            ("2. Main Services", [
                [
                    "API Gateway - receives all client requests, checks tokens and applies rate limits.",
                    "Identity Service - users, login, SSO and API tokens.",
                    "Issue Service - projects, issues, comments and workflows.",
                    "Sprint Service - sprints, boards and burndown calculations.",
                    "Automation Service - evaluates automation rules.",
                    "Notification Service - email and in-app notifications.",
                    "Search Service - full-text search over issues.",
                ],
            ]),
            ("3. Data Storage", [
                [
                    "PostgreSQL - main database for projects, issues and users.",
                    "Redis - caching and short-lived data such as sessions.",
                    "Object storage - file attachments.",
                    "Search index - for fast issue search.",
                ],
                "Each region has its own databases, so customer data stays in the chosen region.",
            ]),
            ("4. Events", [
                "When something changes (for example, an issue is updated), the service publishes an "
                "event on the event bus. Other services, such as Automation and Notification, react to "
                "these events. This keeps services loosely connected.",
            ]),
            ("5. Reliability", [
                [
                    "Every service runs at least 3 copies across different availability zones.",
                    "Databases are backed up every hour; backups are kept for 35 days.",
                    "Recovery Point Objective (RPO): 1 hour. Recovery Time Objective (RTO): 4 hours.",
                    f"Target availability: {NT_SLA} (Team) and {NT_SLA_ENTERPRISE} (Enterprise).",
                ],
            ]),
            ("6. Security", [
                [
                    "All traffic is encrypted with TLS 1.2 or higher.",
                    "Data at rest is encrypted with AES-256.",
                    "Every customer's data is separated by a tenant ID that is checked on every query.",
                    "Security patches are applied within 7 days for critical issues.",
                ],
            ]),
            ("7. Deployment", [
                "Code is deployed several times a day using a CI/CD pipeline. New versions are first "
                "released to 5% of traffic (canary release) and rolled out fully if error rates stay normal.",
            ]),
        ],
    },
    # ----------------------------------------------------------------- PRD-005
    {
        "doc_code": "PRD-005", "title": "NovaTrack Troubleshooting Manual", "department": "Product",
        "document_type": "Manual", "version": NT_VERSION, "created": "2025-07-08",
        "access_level": "Employee", "format": "docx",
        "sections": [
            ("1. How to Use This Manual", [
                "This manual helps support engineers and customer success managers solve common NovaTrack "
                "problems. Each problem lists the symptom, likely cause and fix.",
            ]),
            ("2. Login and SSO Problems", [
                [
                    "Error NT-1001 (Invalid credentials): the user typed a wrong password; ask them to "
                    "reset it from the login page.",
                    "Error NT-1002 (SSO configuration error): the customer's SSO certificate has expired "
                    "or changed; the customer admin must upload the new certificate in Admin > Security.",
                    "Error NT-1003 (User not provisioned): the user exists in the customer's identity "
                    "provider but was not added to NovaTrack; the admin must assign the NovaTrack app.",
                ],
            ]),
            ("3. Board and Sync Problems", [
                [
                    "Issues not appearing on the board: check the board filter and that the issue status "
                    "is mapped to a board column.",
                    "Changes not visible to teammates: ask them to refresh; real-time updates can be "
                    "blocked by company proxies that block WebSocket connections.",
                    "Burndown chart looks wrong: story points were changed after the sprint started; the "
                    "chart shows the scope change as an upward step.",
                ],
            ]),
            ("4. Automation Problems", [
                [
                    "Rule did not run: check the rule's audit log under Project Settings > Automation.",
                    "Error NT-2001 (Rule limit reached): the project has reached 50 active rules on the "
                    "Team plan; disable unused rules or upgrade to Enterprise.",
                    "Rule runs in a loop: add a condition so the rule ignores changes made by automation.",
                ],
            ]),
            ("5. API and Integration Problems", [
                [
                    "HTTP 401 from the API: the token is missing, expired or revoked.",
                    "HTTP 429 from the API: the integration exceeds the rate limit; it should wait for the "
                    "time in the 'Retry-After' header.",
                    "Webhooks not received: check that the customer's endpoint returns HTTP 200 within 10 "
                    "seconds; NovaTrack retries failed webhooks 5 times over 1 hour.",
                ],
            ]),
            ("6. Escalation", [
                "If a problem cannot be solved with this manual, create an internal escalation ticket with "
                "the customer name, region, request ID and steps to reproduce. Engineering on-call responds "
                "to P1 customer escalations within 30 minutes.",
            ]),
        ],
    },
]
