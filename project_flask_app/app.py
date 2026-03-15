from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
import tensorflow as tf
import os
import matplotlib.pyplot as plt
from werkzeug.utils import secure_filename

# Инициализация Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Используем SQLite для простоты
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Отключаем отслеживание изменений, чтобы избежать предупреждений

db = SQLAlchemy(app)


# Модели данных

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # admin/user


class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    accuracy_epoch = db.Column(db.Float, nullable=False)
    class_count = db.Column(db.String(200), nullable=False)
    classification_accuracy = db.Column(db.Float, nullable=False)
    top_5_classes = db.Column(db.String(100), nullable=False)


# Функция для создания таблиц
def create_tables():
    with app.app_context():
        db.create_all()


# Вызовем создание таблиц при запуске приложения
create_tables()


# Главная страница
@app.route('/')
def home():
    return redirect(url_for('login'))


# Страница входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            return "Неверный логин или пароль."
    return render_template('login.html')


# Страница дашборда
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_role = session.get('role')

    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))

    # Для пользователя - просмотр графиков и аналитики
    analytics_data = Analytics.query.all()
    return render_template('index.html', analytics_data=analytics_data)


# Админский дашборд
@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        new_user = User(first_name=first_name, last_name=last_name, username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()

    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)


# Загрузка данных пользователем
@app.route('/upload_data', methods=['POST'])
def upload_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Загрузка модели
            model = tf.keras.models.load_model('models/simple_one_cell_model.h5')
            # Добавить логику обработки данных с помощью модели
            return redirect(url_for('dashboard'))


# Страница аналитики
@app.route('/analytics', methods=['GET'])
def analytics():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    analytics_data = Analytics.query.all()
    return jsonify([data.serialize() for data in analytics_data])


# Запуск Flask приложения
if __name__ == '__main__':
    app.run(debug=True)