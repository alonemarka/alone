from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'reelix-super-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///reelix.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Klasör oluştur
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ====================== MODELLER ======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, default="Merhaba, Reelix kullanıyorum!")
    is_admin = db.Column(db.Boolean, default=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    file = db.Column(db.String(200))
    is_video = db.Column(db.Boolean, default=False)
    likes = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ====================== ROUTES ======================
@app.route('/')
def home():
    posts = Post.query.order_by(Post.date.desc()).all()
    return render_template('home.html', posts=posts)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten alınmış!')
            return redirect(url_for('register'))
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('home'))
        flash('Hatalı kullanıcı adı veya şifre!')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        content = request.form.get('content', '')
        file = request.files.get('file')
        if file and file.filename:
            filename = file.filename
            is_video = filename.lower().endswith(('.mp4', '.mov', '.avi'))
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            post = Post(user_id=current_user.id, content=content, file=filename, is_video=is_video)
            db.session.add(post)
            db.session.commit()
            flash('Paylaşım yapıldı!')
            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        return "Bu sayfaya erişim iznin yok!", 403
    
    users = User.query.all()
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        action = request.form.get('action')
        user = User.query.get(user_id)
        if user:
            if action == "reset":
                user.password = generate_password_hash("123456")
                flash(f"{user.username} şifresi sıfırlandı → 123456")
            elif action == "make_admin":
                user.is_admin = True
                flash(f"{user.username} admin yapıldı!")
        db.session.commit()
    return render_template('admin.html', users=users)

# ====================== BAŞLATMA ======================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # İlk admin hesabı
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password=generate_password_hash('admin123'), is_admin=True)
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin hesabı oluşturuldu: admin / admin123")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
