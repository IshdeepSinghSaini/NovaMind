"""Finance department documents (fictional). A section item: str = paragraph, list = bullet points."""

from sample_docs.facts import *  # noqa: F401,F403

DOCUMENTS = [
    # ----------------------------------------------------------------- FIN-001
    {
        "doc_code": "FIN-001", "title": "Travel Reimbursement Policy", "department": "Finance",
        "document_type": "Policy", "version": "3.3", "created": "2025-02-05",
        "access_level": "Employee", "format": "pdf",
        "sections": [
            ("1. Purpose", [
                f"This policy explains how employees of {COMPANY} can get their money back for business "
                "travel expenses, such as flights, hotels, local transport and meals, and what limits apply.",
            ]),
            ("2. Pre-Approval", [
                f"All business trips must be approved in {EXPENSE_PORTAL} by the reporting manager "
                "before booking. Trips without pre-approval may not be reimbursed.",
            ]),
            ("3. Flights and Trains", [
                [
                    "Book economy class for all domestic and international flights.",
                    "Business class is allowed only for international flights longer than 8 hours, "
                    "with Vice President approval.",
                    "Book at least 14 days in advance where possible to get lower fares.",
                    "AC 2-tier or AC chair car is allowed for train travel.",
                ],
            ]),
            ("4. Hotel Limits", [
                [
                    f"Metro cities (Mumbai, Delhi, Bengaluru, Chennai, Hyderabad, Kolkata, Pune): up to "
                    f"{HOTEL_METRO}.",
                    f"Non-metro cities in India: up to {HOTEL_NON_METRO}.",
                    f"International: up to {HOTEL_INTL}.",
                ],
                "Amounts above these limits are paid by the employee unless approved in advance by the "
                "department head.",
            ]),
            ("5. Daily Allowance (Per Diem)", [
                f"For meals and small incidental expenses, employees receive a per diem of "
                f"{PER_DIEM_DOMESTIC} for domestic travel and {PER_DIEM_INTL} for international travel. "
                "No receipts are needed for the per diem. If meals are provided by the hotel or client, "
                "the per diem for that meal is reduced by one third.",
            ]),
            ("6. Local Transport", [
                "Taxis and app-based cabs are reimbursed at actual cost for travel between the airport, "
                "hotel and business locations. Personal sightseeing is not reimbursed.",
            ]),
            ("7. Travel Advance", [
                f"Employees can request an advance of up to {TRAVEL_ADVANCE} of the estimated trip cost in "
                f"{EXPENSE_PORTAL}. The advance must be settled in the final claim.",
            ]),
            ("8. Submitting a Claim", [
                [
                    f"Submit the claim in {EXPENSE_PORTAL} within {CLAIM_DEADLINE_DAYS} days of the end "
                    "of the trip. Late claims need department head approval.",
                    f"Attach receipts for every expense above {RECEIPT_REQUIRED_ABOVE}.",
                    "Select the approved trip request so the claim is linked to it.",
                ],
                f"Approved claims are reimbursed to the employee's salary bank account within "
                f"{REIMBURSE_DAYS} working days of final approval. For step-by-step instructions, see "
                "the Employee Reimbursement Procedure (FIN-004).",
            ]),
            ("9. Not Reimbursable", [
                [
                    "Alcohol, personal entertainment and minibar charges.",
                    "Traffic fines and parking penalties.",
                    "Travel for family members.",
                    "Loss of personal belongings.",
                ],
            ]),
        ],
    },
    # ----------------------------------------------------------------- FIN-002
    {
        "doc_code": "FIN-002", "title": "Expense Management Policy", "department": "Finance",
        "document_type": "Policy", "version": "2.4", "created": "2025-01-25",
        "access_level": "Finance", "format": "docx",
        "sections": [
            ("1. Purpose", [
                "This internal Finance policy defines how company spending is approved, recorded and "
                "audited. It is restricted to the Finance team.",
            ]),
            ("2. Approval Matrix", [
                "Every expense or purchase request must be approved according to its value:",
                [f"{amount}: {approver}" for amount, approver in APPROVAL_MATRIX],
                "Splitting a purchase into smaller requests to avoid a higher approval level is a "
                "serious policy violation.",
            ]),
            ("3. Corporate Credit Cards", [
                [
                    "Corporate cards are issued to department heads and frequent travellers only.",
                    "Standard monthly limit: INR 2,00,000; department heads: INR 5,00,000.",
                    "Card statements must be reconciled in ExpenseHub by the 5th of the next month.",
                    "Personal use of corporate cards is not allowed.",
                ],
            ]),
            ("4. Expense Audit", [
                f"Every month, Finance randomly audits {AUDIT_SAMPLE} of approved expense claims, and "
                "every claim above INR 1,00,000. Findings are shared with the employee's manager.",
            ]),
            ("5. Handling Policy Violations", [
                [
                    "First violation: claim corrected and the employee is informed.",
                    "Repeated violations: reported to the department head and HR.",
                    "Fraudulent claims: treated as gross misconduct under the HR disciplinary procedure.",
                ],
            ]),
            ("6. Accounting Codes", [
                "Every expense must be booked to the correct general ledger (GL) code and cost centre. "
                "Common codes: 6100 Travel, 6200 Training, 6300 Software Subscriptions, 6400 Office "
                "Supplies, 6500 Client Entertainment.",
            ]),
            ("7. Budget Monitoring", [
                "Finance sends a budget-versus-actual report to each department head by the 10th of every "
                "month. Spending above 90% of the quarterly budget needs Finance Controller approval.",
            ]),
        ],
    },
    # ----------------------------------------------------------------- FIN-003
    {
        "doc_code": "FIN-003", "title": "Invoice Processing Guide", "department": "Finance",
        "document_type": "Guide", "version": "1.9", "created": "2025-03-20",
        "access_level": "Finance", "format": "pdf",
        "sections": [
            ("1. Purpose", [
                "This guide explains how the Accounts Payable (AP) team receives, checks, approves and "
                "pays vendor invoices. It is restricted to the Finance team.",
            ]),
            ("2. Receiving Invoices", [
                "Vendors must send invoices to the AP mailbox. Invoices sent to individual employees must "
                "be forwarded to AP within 2 working days. Every invoice is logged in the AP register "
                "with a unique number.",
            ]),
            ("3. Three-Way Match", [
                "Before approval, every invoice must match:",
                [
                    "The Purchase Order (PO) - what we agreed to buy and at what price.",
                    "The Goods Receipt Note (GRN) - confirmation that we received the goods or services.",
                    "The Invoice - what the vendor is charging.",
                ],
                f"Differences within a tolerance of {INVOICE_TOLERANCE} of the PO value can be approved "
                "by the AP lead. Larger differences go back to the requester and the vendor.",
            ]),
            ("4. Checks Before Payment", [
                [
                    "Vendor is active in the vendor master and bank details are verified.",
                    "Tax registration number and tax amounts are correct.",
                    "No duplicate invoice (same vendor, invoice number and amount).",
                    "Approval follows the approval matrix in the Expense Management Policy (FIN-002).",
                ],
            ]),
            ("5. Payment Terms and Payment Runs", [
                f"Standard vendor payment terms are {VENDOR_TERMS} from the invoice date. Small and "
                "micro vendors are paid within the time required by applicable regulations. Payment runs "
                f"happen {PAYMENT_RUN_DAY}.",
            ]),
            ("6. Bank Detail Changes", [
                "Any request from a vendor to change bank details must be verified by calling the vendor "
                "on the phone number already on file (never a number given in the change request). This "
                "protects against invoice fraud.",
            ]),
            ("7. Month-End Close", [
                "All invoices received by the 25th of the month are booked in the same month. Accruals "
                "for services received but not yet invoiced are booked by the 3rd working day of the "
                "next month.",
            ]),
        ],
    },
    # ----------------------------------------------------------------- FIN-004
    {
        "doc_code": "FIN-004", "title": "Employee Reimbursement Procedure", "department": "Finance",
        "document_type": "Procedure", "version": "2.1", "created": "2025-04-10",
        "access_level": "Employee", "format": "txt",
        "sections": [
            ("1. Purpose", [
                f"This procedure explains, step by step, how to claim reimbursement for business "
                f"expenses in {EXPENSE_PORTAL}.",
            ]),
            ("2. What Can Be Claimed", [
                [
                    "Business travel (see the Travel Reimbursement Policy, FIN-001).",
                    "Certifications and courses from your learning budget (with manager approval).",
                    "Client meals and entertainment approved in advance by your manager.",
                    "Small office or work purchases approved by your manager.",
                ],
            ]),
            ("3. How to Submit a Claim", [
                [
                    f"Log in to {EXPENSE_PORTAL} and click 'New Claim'.",
                    "Choose the category (Travel, Learning, Client Meals or Other).",
                    "Enter the date, amount and a short business reason for each expense.",
                    f"Upload clear photos or PDFs of receipts for every expense above "
                    f"{RECEIPT_REQUIRED_ABOVE}.",
                    "Click 'Submit'. The claim goes to your reporting manager.",
                ],
            ]),
            ("4. Approval and Payment Timeline", [
                [
                    f"Your manager approves or rejects the claim within {MANAGER_APPROVAL_DAYS} working days.",
                    "Finance verifies the claim and the receipts.",
                    f"Approved claims are paid in the next payment cycle, on {PAYMENT_CYCLE}, and always "
                    f"within {REIMBURSE_DAYS} working days of final approval.",
                    "Payment is made to your salary bank account; you get an email when it is paid.",
                ],
            ]),
            ("5. Common Reasons for Rejection", [
                [
                    "Missing or unreadable receipts.",
                    f"Claim submitted more than {CLAIM_DEADLINE_DAYS} days after the expense or trip.",
                    "Expense above policy limits without prior approval.",
                    "Personal expenses included in the claim.",
                ],
                "If a claim is rejected, correct it and submit it again.",
            ]),
            ("6. Help", [
                f"For questions about a claim, contact {FINANCE_EMAIL} with your claim number.",
            ]),
        ],
    },
]
