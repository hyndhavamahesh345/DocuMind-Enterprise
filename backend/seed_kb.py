import pickle
from langchain_core.documents import Document

parent_store = {}

kb_data = [
    # Refund constraints & conditions
    {'text': 'Customers may request a full refund within 30 days of purchase. All refund requests must be submitted through the HR Self-Service Portal. Processing takes 5-7 business days. Refunds after 30 days require manager approval and are subject to a 15% administrative fee.', 'page': 12, 'name': 'Refund_Policy_2026.pdf'},
    {'text': 'Defective products returned within 14 days and accompanied by the original receipt will be fully reimbursed without administrative fees. Returning custom-made products is strictly prohibited under standard agreements.', 'page': 13, 'name': 'Refund_Policy_2026.pdf'},
    {'text': 'To check your refund status, employees and managers must login to the tracking module and input the case ID generated from the self-service portal.', 'page': 15, 'name': 'Refund_Policy_2026.pdf'},
    
    # Leave Policy & Entitlements
    {'text': 'Leave requests must be submitted a minimum of 5 business days in advance via the HR portal. Annual leave accrues at 1.67 days per month (20 days/year). Emergency leave (up to 3 days) may be requested retrospectively with supporting documentation submitted within 48 hours.', 'page': 24, 'name': 'HR_Handbook.pdf'},
    {'text': 'Maternity leave policies provide up to 16 weeks of fully paid leave. Paternity leave is capped at 4 weeks. Additional unpaid parental leave can extend up to a 6-month period if requested 30 days prior.', 'page': 25, 'name': 'HR_Handbook.pdf'},
    {'text': 'Sick leave balance cannot be cashed out at the end of the year or upon termination. Unused annual leave can carry over to a maximum of 10 days into the new calendar year.', 'page': 28, 'name': 'HR_Handbook.pdf'},
    
    # IT Security & Passwords
    {'text': 'All corporate accounts require password changes every 90 days. Passwords must be a minimum of 12 characters, including uppercase, lowercase, a number, and a special character. Multi-factor authentication (MFA) is mandatory for all systems.', 'page': 3, 'name': 'IT_Security_Guidelines.pdf'},
    {'text': 'Shared passwords are strictly prohibited and constitute a security policy violation. If a shared password is required for generic service accounts, it must be stored and rotated in the Enterprise Password Vault (EPV).', 'page': 4, 'name': 'IT_Security_Guidelines.pdf'},
    {'text': 'Any employee leaving their workstation unlocked and unattended may face disciplinary action. Screensavers must be configured to lock automatically after 5 minutes of inactivity.', 'page': 6, 'name': 'IT_Security_Guidelines.pdf'},
    
    # Onboarding Process
    {'text': 'The onboarding process is structured across 4 weeks: Week 1 covers pre-joining documentation and IT setup. Week 2 covers department orientation and team introductions. Week 3 covers systems training and compliance modules. Week 4 covers role-specific task shadowing.', 'page': 8, 'name': 'Onboarding_Manual.pdf'},
    {'text': 'All new hires must complete mandatory compliance training within the first 30 days. Failure to do so will result in suspension of network access.', 'page': 9, 'name': 'Onboarding_Manual.pdf'},
    {'text': 'Managers are responsible for assigning an onboarding buddy for each new hire. This buddy should have at least 1 year of tenure and no active HR warnings.', 'page': 11, 'name': 'Onboarding_Manual.pdf'},
    
    # Expense and Travel
    {'text': 'Flights must be booked at least 14 days in advance to qualify for standard class travel. Last-minute bookings require VP approval. Business class is permitted for continuous flights exceeding 8 hours.', 'page': 4, 'name': 'Travel_Expense_Policy.pdf'},
    {'text': 'Daily food allowance is capped at $75 per day. Receipts are required for any single meal exceeding $25. Alcohol is strictly non-reimbursable unless client entertainment takes place, in which case a separate limit of $150 applies.', 'page': 7, 'name': 'Travel_Expense_Policy.pdf'},
    
    # Facility and Office 
    {'text': 'The standard office hours are 8:00 AM to 6:00 PM local time. Keycard access is disabled outside these hours unless special weekend or night-shift access has been formally requested.', 'page': 2, 'name': 'Facilities_Guide.pdf'},
    {'text': 'Visitor badges must be returned to the front desk at the end of the day. If a visitor badge is lost, a $50 replacement fee must be charged to the hosting department.', 'page': 5, 'name': 'Facilities_Guide.pdf'},
]

import uuid
for item in kb_data:
    pid = str(uuid.uuid4())
    doc = Document(
        page_content=item["text"],
        metadata={
            "source": item["name"],
            "page": item["page"],
            "parent_id": pid
        }
    )
    parent_store[pid] = doc

with open("parent_store.pkl", "wb") as f:
    pickle.dump(parent_store, f)

doc_meta = [
    {"name": "Refund_Policy_2026.pdf", "pages": 22, "chunks": 15},
    {"name": "HR_Handbook.pdf", "pages": 50, "chunks": 42},
    {"name": "IT_Security_Guidelines.pdf", "pages": 18, "chunks": 20},
    {"name": "Onboarding_Manual.pdf", "pages": 15, "chunks": 10},
    {"name": "Travel_Expense_Policy.pdf", "pages": 12, "chunks": 8},
    {"name": "Facilities_Guide.pdf", "pages": 9, "chunks": 5},
]
with open("doc_meta.pkl", "wb") as f:
    pickle.dump(doc_meta, f)

from langchain_community.retrievers import BM25Retriever
all_docs = list(parent_store.values())
bm25_retriever = BM25Retriever.from_documents(all_docs)
with open("bm25_store.pkl", "wb") as f:
    pickle.dump(bm25_retriever, f)
print("Demo Knowledge Base successfully created!")
