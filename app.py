# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Feedback
from scraper import get_mock_product_data

from PIL import Image

# Optional: try to import CLIP (if installed). If not available, fallback to mock categories.
USE_CLIP = False
try:
    from transformers import CLIPProcessor, CLIPModel
    import torch
    # If import succeeds, enable CLIP usage
    USE_CLIP = True
except Exception as e:
    # CLIP not available — we'll use fallback labels
    USE_CLIP = False

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'replace-with-strong-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

# CLIP setup if available
categories = ["phone", "laptop", "tablet", "camera", "headphones", "watch", "shoe", "bag", "television", "speaker"]
if USE_CLIP:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    templates = ["a photo of a {}.", "a product photo of a {}.", "a picture of a {}."]
    # precompute text embeddings
    with torch.no_grad():
        text_inputs = [t.format(c) for c in categories for t in templates]
        toks = processor(text=text_inputs, return_tensors="pt", padding=True).to(device)
        text_embs = model.get_text_features(**toks)
        text_embs = text_embs / text_embs.norm(dim=-1, keepdim=True)
        text_embs = text_embs.view(len(categories), len(templates), -1).mean(dim=1)
        text_embs = text_embs / text_embs.norm(dim=-1, keepdim=True)

# Create DB if missing
with app.app_context():
    db.create_all()

# ---------- Helpers ----------
def allowed_file(filename):
    allowed = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

def predict_label(filepath):
    """Return detected product label (title cased). Uses CLIP if available, otherwise fallback."""
    if USE_CLIP:
        try:
            img = Image.open(filepath).convert('RGB')
            inputs = processor(images=img, return_tensors="pt").to(device)
            with torch.no_grad():
                image_emb = model.get_image_features(**inputs)
                image_emb = image_emb / image_emb.norm(dim=-1, keepdim=True)
                sims = (image_emb @ text_embs.T).squeeze(0)
                best_index = sims.argmax().item()
                return categories[best_index].title()
        except Exception as e:
            print("CLIP error:", e)
            # fallback to mock
    # fallback: simple filename-based or random pick
    # try to infer from filename words
    fname = os.path.basename(filepath).lower()
    for c in categories:
        if c in fname:
            return c.title()
    # else random
    import random
    return random.choice(categories).title()

# ---------- Routes ----------
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or not password:
            flash("Please fill all fields.", "warning")
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash("Account with this email already exists.", "warning")
            return redirect(url_for('signup'))
        u = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(u)
        db.session.commit()
        flash("Account created. Please sign in.", "success")
        return redirect(url_for('signin'))
    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash("Logged in successfully.", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for('signin'))
    return render_template('signin.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('welcome'))

@app.route('/home')
def home():
    if 'user_id' not in session:
        flash("Login required.", "warning")
        return redirect(url_for('signin'))
    return render_template('home.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session:
        flash("Login required.", "warning")
        return redirect(url_for('signin'))
    if 'image' not in request.files:
        flash("No file selected.", "warning")
        return redirect(url_for('home'))
    file = request.files['image']
    if file.filename == '':
        flash("No file selected.", "warning")
        return redirect(url_for('home'))
    if not allowed_file(file.filename):
        flash("File type not allowed.", "danger")
        return redirect(url_for('home'))

    filename = secure_filename(file.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    # predict product label
    label = predict_label(save_path)

    # fetch product data (mock)
    product = get_mock_product_data(label)

    return render_template('home.html', filename=filename, product=product)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        msg = request.form.get('message', '').strip()
        if not msg:
            flash("Please enter your feedback.", "warning")
            return redirect(url_for('feedback'))
        fb = Feedback(user_name=name if name else None, message=msg)
        db.session.add(fb)
        db.session.commit()
        flash("Thank you for your feedback!", "success")
        return redirect(url_for('home') if 'user_id' in session else url_for('welcome'))
    return render_template('feedback.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash("Please sign in.", "warning")
        return redirect(url_for('signin'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        # Example: change display name
        newname = request.form.get('name', '').strip()
        if newname:
            user.name = newname
            db.session.commit()
            session['user_name'] = newname
            flash("Profile updated.", "success")
            return redirect(url_for('profile'))
    return render_template('settings.html', user=user)

# run
if __name__ == '__main__':
    app.run(debug=True)
