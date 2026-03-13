---
description: How to run the DocuMind Enterprise platform
---

# Running DocuMind Enterprise

Follow these steps to initialize the full stack.

![DocuMind Interface](C:/Users/nirjo/.gemini/antigravity/brain/9dfe82a4-50de-494e-9279-5e6c620ac351/documind_enterprise_mockup_1773407369958.png)

## Steps

### 1. Initialize Backend
// turbo
```powershell
cd backend; .\venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

### 2. Start Frontend Server
// turbo
```powershell
cd frontend; python -m http.server 8001
```

### 3. Access Application
Open [http://localhost:8001](http://localhost:8001) in your browser.
