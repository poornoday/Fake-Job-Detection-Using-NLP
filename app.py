import os
import datetime
import csv
import io
import joblib
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fake-job-secret-key-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fake_jobs.db'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Corrected Model Folder Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model', 'model_lr.pkl')
VECT_PATH = os.path.join(BASE_DIR, 'model', 'vectorizer.pkl')

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECT_PATH)

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))

class PredictionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_text = db.Column(db.Text)
    result = db.Column(db.String(20))
    confidence = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class FlaggedPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_text = db.Column(db.Text)
    predicted_as = db.Column(db.String(20))
    reason = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    text = request.form.get('job_description', '')
    if not text: return redirect(url_for('index'))
    
    vect_text = vectorizer.transform([text])
    prediction = model.predict(vect_text)[0]
    prob = model.predict_proba(vect_text).max()
    res_text = "Fake" if prediction == 1 else "Real"

    new_log = PredictionLog(job_text=text[:200], result=res_text, confidence=round(prob*100, 2))
    db.session.add(new_log)
    db.session.commit()

    return render_template('index.html', prediction=res_text, confidence=round(prob*100, 2), original_text=text)

@app.route('/flag', methods=['POST'])
def flag():
    j_text = request.form.get('job_text')
    p_as = request.form.get('predicted_as')
    reas = request.form.get('reason')
    
    if j_text and reas:
        db.session.add(FlaggedPost(job_text=j_text, predicted_as=p_as, reason=reas))
        db.session.commit()
        flash('Report submitted successfully!')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid Credentials')
    return render_template('login.html', mode='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        db.session.add(User(username=request.form['username'], password=hashed_pw))
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('login.html', mode='register')

@app.route('/dashboard')
@login_required
def dashboard():
    logs = PredictionLog.query.order_by(PredictionLog.timestamp.desc()).all()
    flags = FlaggedPost.query.order_by(FlaggedPost.timestamp.desc()).all()
    fake = PredictionLog.query.filter_by(result='Fake').count()
    real = PredictionLog.query.filter_by(result='Real').count()
    
    trend = db.session.query(func.date(PredictionLog.timestamp), func.count(PredictionLog.id)).group_by(func.date(PredictionLog.timestamp)).all()
    labels = [str(t[0]) for t in trend]
    counts = [t[1] for t in trend]

    return render_template('dashboard.html', logs=logs, flags=flags, fake=fake, real=real, total=len(logs), labels=labels, counts=counts)

@app.route('/export/csv')
@login_required
def export_csv():
    logs = PredictionLog.query.all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Time', 'Result', 'Confidence'])
    for l in logs: writer.writerow([l.timestamp, l.result, l.confidence])
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(mem, mimetype='text/csv', as_attachment=True, download_name='report.csv')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
if __name__ == '__main__':
    app.run(debug=True)