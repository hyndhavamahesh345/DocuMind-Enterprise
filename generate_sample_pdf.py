from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import os

def create_sample_pdf():
    directory = "data/docs"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    file_path = os.path.join(directory, "HR_Policy_2024.pdf")
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Page 1
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, height - 50, "DocuMind Enterprise: Standard HR Policy 2024")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 100, "1. Leave Policy")
    c.setFont("Helvetica", 11)
    c.drawString(100, height - 120, "Employees are entitled to 20 days of paid annual leave per calendar year.")
    c.drawString(100, height - 135, "Sick leave is capped at 10 days per year and requires a medical certificate for more than 2 days.")
    c.drawString(100, height - 150, "Maternity leave is 26 weeks, and paternity leave is 2 weeks.")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 180, "2. Remote Work Policy")
    c.setFont("Helvetica", 11)
    c.drawString(100, height - 200, "Employees can work remotely up to 3 days a week with manager approval.")
    c.drawString(100, height - 215, "A home office allowance of $500 is provided for equipment setup.")

    # Page 2
    c.showPage()
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 50, "3. Reimbursement Policy")
    c.setFont("Helvetica", 11)
    c.drawString(100, height - 70, "Travel expenses will be reimbursed for business trips.")
    c.drawString(100, height - 85, "Meal allowance is $50 per day during travel.")
    c.drawString(100, height - 100, "Internet bills up to $50 per month are reimbursable for remote workers.")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, height - 130, "4. Code of Conduct")
    c.setFont("Helvetica", 11)
    c.drawString(100, height - 150, "Strict adherence to the company's anti-discrimination policy is required.")
    c.drawString(100, height - 165, "Confidentiality of client data is paramount.")

    c.save()
    print(f"DONE: Sample PDF created at {file_path}")

if __name__ == "__main__":
    create_sample_pdf()
