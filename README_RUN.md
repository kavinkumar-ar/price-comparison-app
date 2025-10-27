1. Create and activate a virtualenv (recommended):
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate

2. Install requirements (skip torch if you will not use CLIP):
   pip install -r requirements.txt
   # For torch: follow install instructions at pytorch.org to pick the right wheel for your OS/GPU.

3. Run the app:
   python app.py

4. Open http://127.0.0.1:5000
