import os
import re
import uuid
import time
import logging
import warnings
from datetime import datetime
from dataclasses import asdict

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt
from werkzeug.utils import secure_filename

from ai.image_classifier import ImageIssueClassifier
from ai.nlp import ComplaintNLPAnalyzer
from ai.fake_detection import FakeReportDetector
from ai.complaint_writer import ComplaintWriter
from storage.db import CivicDB, ReportRecord
from utils.gps import normalize_location

# Optional OpenAI client (SDK v1). Falls back to rule-based replies if unavailable.
try:
    from openai import OpenAI  # type: ignore
except Exception:
    OpenAI = None  # type: ignore

_openai_client_cache = None

def _get_openai_client():
    global _openai_client_cache
    if _openai_client_cache is not None:
        return _openai_client_cache
    if OpenAI is None:
        return None
    # Only create if key is present
    if not os.getenv("OPENAI_API_KEY"):
        return None
    try:
        _openai_client_cache = OpenAI()
        return _openai_client_cache
    except Exception:
        return None

# Configure logging (default INFO). Allow override via LOG_LEVEL env.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(level=numeric_level)

# Suppress noisy third-party loggers
for noisy in [
    "urllib3",
    "httpx",
    "huggingface_hub",
    "transformers",
]:
    logging.getLogger(noisy).setLevel(logging.WARNING)

# Re-enable Werkzeug request/startup info logs
logging.getLogger("werkzeug").setLevel(logging.INFO)

# Aggressively silence PyMongo and Passlib internal debug spam
for noisy_exact in [
    "pymongo",
    "pymongo.topology",
    "pymongo.connection",
    "pymongo.serverSelection",
    "pymongo.command",
    "passlib",
    "passlib.handlers.bcrypt",
]:
    lg = logging.getLogger(noisy_exact)
    lg.setLevel(logging.ERROR)
    lg.propagate = False
    for h in lg.handlers:
        h.setLevel(logging.ERROR)

# Filter runtime warnings from passlib/bcrypt
warnings.filterwarnings("ignore", module=r"passlib.*")

# Fallback env-based verbosity for Transformers
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

try:
    # Reduce Transformers internal logging further
    from transformers.utils import logging as hf_logging
    hf_logging.set_verbosity_error()
except Exception:
    pass

# Load environment variables
load_dotenv()

def create_app() -> Flask:
    app = Flask(__name__)
    
    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "civic-eye-secret-key-change-me")
    upload_dir = os.getenv("UPLOAD_DIR", os.path.join(os.path.dirname(__file__), "uploads"))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Ensure static folder exists
    static_folder = app.static_folder or 'static'
    os.makedirs(static_folder, exist_ok=True)
    os.makedirs(os.path.join(static_folder, 'css'), exist_ok=True)
    os.makedirs(os.path.join(static_folder, 'js'), exist_ok=True)
    os.makedirs(os.path.join(static_folder, 'images'), exist_ok=True)
    
    # CORS configuration
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
    CORS(app, resources={r"/api/*": {"origins": allowed_origins.split(",")}})
    
    # JWT configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "change-me")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 60 * 60 * 8  # 8 hours
    jwt = JWTManager(app)
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    # Initialize services
    classifier = ImageIssueClassifier()
    nlp = ComplaintNLPAnalyzer()
    fake_detector = FakeReportDetector()
    writer = ComplaintWriter()
    db = CivicDB()
    
    # Routes
    @app.context_processor
    def inject_cache_buster():
        # Use app start time so all static links change per restart
        return {"cache_buster": int(time.time())}
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/login')
    def login_page():
        return render_template('login.html')
    
    @app.route('/signup')
    def signup_page():
        return render_template('signup.html')
    
    @app.route('/home')
    def home():
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return render_template('home.html', user=session.get('user'))
    
    @app.route('/report')
    def report_page():
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return render_template('report.html')
    
    @app.route('/track')
    def track_page():
        return render_template('track.html')
    
    @app.route('/solutions')
    def solutions_page():
        return render_template('solutions.html')
    
    @app.route('/resources')
    def resources_page():
        return render_template('resources.html')
    
    # New: Map View
    @app.route('/map')
    def map_view_page():
        return render_template('map.html')

    @app.route('/about')
    def about_page():
        return render_template('about.html')
    
    @app.route('/contact')
    def contact_page():
        return render_template('contact.html')
    
    @app.route('/profile')
    def profile_page():
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return render_template('profile.html', user=session.get('user'))
    
    @app.route('/admin')
    def admin_page():
        if 'user' not in session or session.get('user', {}).get('role') != 'admin':
            flash('Access denied. Admin privileges required.')
            return redirect(url_for('home'))
        reports = db.list_reports(limit=100)
        authorities = db.list_authorities()
        return render_template('admin.html', reports=reports, authorities=authorities)
    
    # Authentication routes
    @app.route('/auth/login', methods=['POST'])
    def login():
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('login_page'))
        
        user = db.find_user(username)
        if not user or not db.verify_password(user, password):
            flash('Invalid credentials')
            return redirect(url_for('login_page'))
        
        session['user'] = {
            'username': user['username'],
            'role': user.get('role', 'citizen')
        }
        
        flash(f'Welcome back, {username}!')
        return redirect(url_for('home'))
    
    @app.route('/auth/signup', methods=['POST'])
    def signup():
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([name, username, email, password]):
            flash('All fields are required', 'error')
            return redirect(url_for('signup_page'))
        
        # Ensure DB connectivity
        if not db.is_connected():
            flash('Database connection error. Please check MONGODB_URI/MONGODB_DB.', 'error')
            return redirect(url_for('signup_page'))
        
        # Check if user exists
        if db.find_user(username):
            flash('Username already exists', 'error')
            return redirect(url_for('signup_page'))
        
        # Create user
        success = db.create_user(username, email, password, name)
        if success:
            flash('Account created successfully! Please login', 'success')
            return redirect(url_for('login_page'))
        else:
            flash('Error creating account', 'error')
            return redirect(url_for('signup_page'))
    
    @app.route('/auth/logout')
    def logout():
        session.pop('user', None)
        flash('You have been logged out')
        return redirect(url_for('index'))
    
    # Issue reporting route
    @app.route('/submit_report', methods=['POST'])
    def submit_report():
        if 'user' not in session:
            flash('Please login to submit reports')
            return redirect(url_for('login_page'))
        
        text = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        issue_type_manual = request.form.get('issue_type')
        
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add UUID to prevent conflicts
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
                image_path = os.path.join(upload_dir, filename)
                file.save(image_path)
        
        # AI: classify and analyze
        predicted_issue = None
        if image_path:
            predicted_issue = classifier.classify_image(image_path)
        
        analysis = nlp.analyze(text or "")
        nlp_issue = analysis.get("issue_type")
        
        # Pick best guess issue type (manual > AI > NLP > unknown)
        issue_type = issue_type_manual or predicted_issue or nlp_issue or "unknown"
        
        # Fake / duplicate detection
        recent = [asdict(r) for r in db.list_reports(limit=50)]
        is_fake, fake_score = fake_detector.is_fake(
            text=text or "",
            image_path=image_path,
            latitude=latitude,
            longitude=longitude,
            recent_reports=recent,
        )
        
        # Normalize location
        location = normalize_location(latitude, longitude)
        
        # Generate complaint
        complaint_text = writer.generate(
            issue_type=issue_type,
            description=text or "",
            location=location,
        )
        
        # Persist
        record = ReportRecord(
            report_id=uuid.uuid4().hex,
            created_at=datetime.utcnow().isoformat() + "Z",
            issue_type=issue_type,
            text=text,
            voice_text=None,
            image_path=image_path,
            location=location,
            complaint_text=complaint_text,
            status="submitted",
            fake=is_fake,
            fake_score=fake_score,
        )
        db.save_report(record)
        
        if is_fake:
            flash(f'Report submitted but flagged for review (ID: {record.report_id})')
        else:
            flash(f'Report submitted successfully! Your complaint ID is: {record.report_id}')
        
        return redirect(url_for('track_page'))
    
    # Complaint tracking route
    @app.route('/check_status', methods=['POST'])
    def check_status():
        complaint_id = request.form.get('complaint_id')
        if not complaint_id:
            flash('Please enter a complaint ID')
            return redirect(url_for('track_page'))
        
        record = db.get_report(complaint_id)
        if not record:
            flash('Complaint not found')
            return redirect(url_for('track_page'))
        
        return render_template('track.html', record=record)
    
    # Admin status update route
    @app.route('/update_status', methods=['POST'])
    def update_status():
        if 'user' not in session or session.get('user', {}).get('role') not in ['admin', 'authority']:
            flash('Access denied')
            return redirect(url_for('home'))
        
        report_id = request.form.get('report_id')
        new_status = request.form.get('status')
        
        if not report_id or not new_status:
            flash('Report ID and status are required')
            return redirect(url_for('admin_page'))
        
        success = db.update_status(report_id, new_status)
        if success:
            flash('Status updated successfully')
        else:
            flash('Failed to update status')
        
        return redirect(url_for('admin_page'))
    
    # API Routes (for AJAX calls if needed)
    @app.route('/api/health')
    def api_health():
        return jsonify({"status": "ok"})

    @app.route('/api/db_health')
    def api_db_health():
        return jsonify({"connected": db.is_connected()})
    
    @app.route('/api/reports')
    def api_reports():
        reports = db.list_reports(limit=100)
        return jsonify([asdict(r) for r in reports])
    
    @app.route('/api/status/<report_id>')
    def api_status(report_id):
        record = db.get_report(report_id)
        if not record:
            return jsonify({"error": "not_found"}), 404
        return jsonify(asdict(record))
    
    # Chatbot route
    @app.route('/chatbot', methods=['POST'])
    def chatbot_reply():
        try:
            payload = request.get_json(silent=True) or {}
            message = (payload.get('message') or '').strip()
            if not message:
                return jsonify({"reply": "Please type a message."})

            txt = message.lower()

            # Simple intents/FAQ (ordered: more specific first)
            responses = [
                (['status', 'track', 'tracking'], "Use the Track page and enter your complaint ID to see the latest status."),
                (['report', 'complaint', 'file'], "To file a complaint, go to Report Issue, add a description, optional photo, and location, then submit."),
                (['login', 'signup', 'account'], "Use the Login/Sign Up pages in the header. Passwords are stored securely."),
                (['map'], "The Map View shows recent issues pinned to their locations."),
                (['mongodb', 'mongo'], "This app uses MongoDB Atlas. Configure MONGODB_URI and MONGODB_DB in the .env file to connect."),
                (['admin'], "Admins and authorities can review and update statuses from the Admin page."),
                (['hello', 'hi', 'hey'], "Hello! How can I help you with Civic Eye today?"),
                (['help', 'support'], "You can report issues via 'Report Issue', track them under 'Track', or view insights on the dashboard."),
            ]

            def any_keyword_in_text(text: str, keywords: list[str]) -> bool:
                for k in keywords:
                    if re.search(r"\b" + re.escape(k) + r"\b", text):
                        return True
                return False

            for keywords, reply in responses:
                if any_keyword_in_text(txt, keywords):
                    return jsonify({"reply": reply})

            # If OpenAI is configured and SDK is available, generate an AI answer
            _openai_client = _get_openai_client()
            if _openai_client:
                debug = os.getenv("CHATBOT_DEBUG") == "1"
                try:
                    system_prompt = (
                        "You are Civic Eye, a concise assistant for a civic issue reporting web app. "
                        "Answer user questions about reporting issues, tracking complaints, authentication, map view, and general guidance. "
                        "If asked something outside app scope, politely provide a brief helpful answer. Keep replies under 6 lines."
                    )
                    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

                    # Try the Responses API first
                    try:
                        resp = _openai_client.responses.create(
                            model=model,
                            input=f"System: {system_prompt}\nUser: {message}"
                        )
                        ai_text = getattr(resp, "output_text", None) or str(resp)
                        ai_text = ai_text.strip()[:1200]
                        if debug:
                            ai_text = "[AI:responses] " + ai_text
                        return jsonify({"reply": ai_text})
                    except Exception as inner:
                        logging.getLogger(__name__).info("Responses API failed, trying Chat Completions: %s", inner)

                    # Fallback: Chat Completions API (older SDKs)
                    try:
                        chat = _openai_client.chat.completions.create(
                            model=model,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": message},
                            ],
                            temperature=0.5,
                        )
                        ai_text = (chat.choices[0].message.content or "").strip()[:1200]
                        if debug:
                            ai_text = "[AI:chat] " + ai_text
                        return jsonify({"reply": ai_text})
                    except Exception as inner2:
                        logging.getLogger(__name__).warning("OpenAI chat completion failed: %s", inner2)
                except Exception as exc:
                    logging.getLogger(__name__).warning("OpenAI reply failed: %s", exc)

            # Default fallback
            return jsonify({"reply": "I didn't catch that. You can ask about reporting, tracking status, map view, login/signup, or MongoDB setup."})
        except Exception as exc:
            logging.getLogger(__name__).exception("Chatbot error: %s", exc)
            return jsonify({"reply": "Sorry, something went wrong handling your message."}), 200
    
    return app

# Create the app
app = create_app()
