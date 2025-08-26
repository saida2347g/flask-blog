from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
db = SQLAlchemy(app)

# =================== MODELS ===================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.Column(db.String(200))
    is_private = db.Column(db.Boolean, default=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# =================== ROUTES ===================
@app.route('/')
def index():
    posts = Post.query.order_by(Post.date_created.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Регистрация успешна! Войдите.")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash("Неверный логин или пароль")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

@app.route('/create', methods=['GET','POST'])
def create():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form['tags']
        is_private = 'private' in request.form
        post = Post(title=title, content=content, tags=tags, user_id=session['user_id'], is_private=is_private)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/post/<int:id>', methods=['GET','POST'])
def post(id):
    post = Post.query.get_or_404(id)
    comments = Comment.query.filter_by(post_id=id).all()
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect(url_for('login'))
        content = request.form['content']
        comment = Comment(content=content, user_id=session['user_id'], post_id=id)
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for('post', id=id))
    return render_template('post.html', post=post, comments=comments)

@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    post = Post.query.get_or_404(id)
    if post.user_id != session.get('user_id'):
        return redirect(url_for('index'))
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        post.tags = request.form['tags']
        post.is_private = 'private' in request.form
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('edit.html', post=post)

@app.route('/delete/<int:id>')
def delete(id):
    post = Post.query.get_or_404(id)
    if post.user_id != session.get('user_id'):
        return redirect(url_for('index'))
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

# =================== HTML GENERATOR ===================
# Автоматически создаем базовые шаблоны при первом запуске
TEMPLATES = {
    'index.html': """
    <!doctype html>
    <html lang='ru'>
    <head><title>Блог</title></head>
    <body>
        <h1>Лента постов</h1>
        {% if session['user_id'] %}<a href='{{ url_for('create') }}'>Новый пост</a> | <a href='{{ url_for('logout') }}'>Выйти</a>{% else %}<a href='{{ url_for('login') }}'>Войти</a> | <a href='{{ url_for('register') }}'>Регистрация</a>{% endif %}
        <ul>
            {% for post in posts %}
                {% if not post.is_private %}
                    <li><a href='{{ url_for('post', id=post.id) }}'>{{ post.title }}</a> — {{ post.author.username }}</li>
                {% endif %}
            {% endfor %}
        </ul>
    </body></html>
    """,
    'register.html': """
    <h1>Регистрация</h1>
    <form method='post'>
        <input name='username' placeholder='Логин'><br>
        <input name='password' type='password' placeholder='Пароль'><br>
        <button type='submit'>Зарегистрироваться</button>
    </form>
    """,
    'login.html': """
    <h1>Вход</h1>
    <form method='post'>
        <input name='username' placeholder='Логин'><br>
        <input name='password' type='password' placeholder='Пароль'><br>
        <button type='submit'>Войти</button>
    </form>
    """,
    'create.html': """
    <h1>Создать пост</h1>
    <form method='post'>
        <input name='title' placeholder='Заголовок'><br>
        <textarea name='content' placeholder='Текст'></textarea><br>
        <input name='tags' placeholder='Теги'><br>
        <label><input type='checkbox' name='private'> Приватный пост</label><br>
        <button type='submit'>Опубликовать</button>
    </form>
    """,
    'post.html': """
    <h1>{{ post.title }}</h1>
    <p>{{ post.content }}</p>
    <small>Автор: {{ post.author.username }}</small>
    <h3>Комментарии:</h3>
    <ul>
        {% for c in comments %}
            <li>{{ c.content }}</li>
        {% endfor %}
    </ul>
    {% if session['user_id'] %}
    <form method='post'>
        <textarea name='content' placeholder='Ваш комментарий'></textarea><br>
        <button type='submit'>Отправить</button>
    </form>
    {% endif %}
    {% if post.user_id == session['user_id'] %}
        <a href='{{ url_for('edit', id=post.id) }}'>Редактировать</a> | <a href='{{ url_for('delete', id=post.id) }}'>Удалить</a>
    {% endif %}
    """,
    'edit.html': """
    <h1>Редактировать пост</h1>
    <form method='post'>
        <input name='title' value='{{ post.title }}'><br>
        <textarea name='content'>{{ post.content }}</textarea><br>
        <input name='tags' value='{{ post.tags }}'><br>
        <label><input type='checkbox' name='private' {% if post.is_private %}checked{% endif %}> Приватный пост</label><br>
        <button type='submit'>Сохранить</button>
    </form>
    """
}

with app.app_context():
    if not os.path.exists('templates'):
        os.mkdir('templates')
    for name, content in TEMPLATES.items():
        path = os.path.join('templates', name)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
