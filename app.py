from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure SQLite Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@app.route('/about')
def about():
    return render_template('about.html')


# User Model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Post Model (for posts including media and tracking likes)
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    media = db.Column(db.String(300), nullable=True)
    author = db.Column(db.String(150), nullable=False)

# Create the database and tables
with app.app_context():
    db.create_all()


# Likes tracking (Post ID and Usernames)
likes = {}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create the database if it doesn't exist
with app.app_context():
    db.create_all()

# Home page displaying posts
@app.route('/')
def home():
    posts = Post.query.all()  # Retrieve all posts
    return render_template('index.html', posts=posts, likes=likes)

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration Successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Check username and password.')
    return render_template('login.html')

# User Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# Create Post (with media upload)
@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files['media']
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_url = f"uploads/{filename}"
        else:
            media_url = None
        new_post = Post(title=title, content=content, media=media_url, author=current_user.username)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('create.html')

# Edit Post
@app.route('/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Ensure only the author can edit the post
    if post.author != current_user.username:
        flash('You do not have permission to edit this post.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('Post updated successfully!')
        return redirect(url_for('profile'))

    return render_template('edit.html', post=post)

# Delete Post
@app.route('/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Ensure only the author can delete the post
    if post.author != current_user.username:
        flash('You do not have permission to delete this post.')
        return redirect(url_for('home'))

    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!')
    return redirect(url_for('profile'))

# User Profile
@app.route('/profile')
@login_required
def profile():
    user_posts = Post.query.filter_by(author=current_user.username).all()  # Get posts by logged-in user
    return render_template('profile.html', user=current_user, posts=user_posts)

# Like a Post
@app.route('/like/<int:post_id>')
@login_required
def like_post(post_id):
    if post_id not in likes:
        likes[post_id] = []
    if current_user.username not in likes[post_id]:
        likes[post_id].append(current_user.username)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

