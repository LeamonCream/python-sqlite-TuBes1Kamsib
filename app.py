from flask import Flask, render_template, request, redirect, url_for, session  # tambahan session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import bleach  # tambahan bleach untuk sanitasi input (XSS)
from functools import wraps  # tambahan untuk jaga identitas fungsi saat pakai decorator

app = Flask(__name__)

# =========================
# tambahan secret key untuk session
# =========================
app.config['SECRET_KEY'] = 'tubes1cyber'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# =========================
# tambahan akun admin
# =========================
admin_username = 'admin'
admin_password = 'password'


# =========================
# tambahan decorator untuk kunci route
# =========================
# jadi kalau belum login dipaksa ke /login
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    grade = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Student {self.name}>'


# =========================
# tambahan route login
# =========================
# Maksud: menampilkan halaman login (GET) dan memproses login (POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    # jika sudah login, langsung ke index.html
    if 'user' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Cek username & password admin
        if username == admin_username and password == admin_password:
            session['user'] = username
            return redirect(url_for('index'))

        return render_template('login.html', error='Login gagal')

    return render_template('login.html')


# =========================
# tambahan route logout
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required  # tambahan kunci route, jadi harus lewat login dulu baru bisa akses
def index():
    # RAW Query
    students = db.session.execute(text('SELECT * FROM student')).fetchall()
    return render_template('index.html', students=students)


@app.route('/add', methods=['POST'])
@login_required  # tambahan kunci route, jadi harus lewat login dulu baru bisa akses
def add_student():
    # name = request.form['name'] ---- Original Code
    # tambahan bleach untuk sanitasi input (XSS)
    name = bleach.clean(request.form['name'], tags=[], strip=True)
    age = request.form['age']
    grade = request.form['grade']

    # RAW Query (pakai parameter biar lebih aman)
    db.session.execute(
        text("INSERT INTO student (name, age, grade) VALUES (:name, :age, :grade)"),
        {"name": name, "age": age, "grade": grade}
    )
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/delete/<string:id>')
@login_required  # tambahan kunci route
def delete_student(id):
    # RAW Query (pakai parameter biar lebih aman)
    db.session.execute(text("DELETE FROM student WHERE id = :id"), {"id": id})
    db.session.commit()
    return redirect(url_for('index'))


# =========================
# ubah dengan kunci route dan raw query
# =========================
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required  # tambahan kunci route
def edit_student(id):
    if request.method == 'POST':
        # name = request.form['name'] --- Original code
        # tambahan bleach untuk sanitasi input (XSS)
        name = bleach.clean(request.form['name'], tags=[], strip=True)
        age = request.form['age']
        grade = request.form['grade']

        # RAW Query (pakai parameter biar lebih aman)
        # db.session.execute(text(f"UPDATE student SET name='{name}', age={age}, grade='{grade}' WHERE id={id}"))
        db.session.execute(
            text("UPDATE student SET name = :name, age = :age, grade = :grade WHERE id = :id"),
            {"name": name, "age": age, "grade": grade, "id": id}
        )
        db.session.commit()
        return redirect(url_for('index'))
    else:
        # RAW Query (pakai parameter biar lebih aman)
        student = db.session.execute(text("SELECT * FROM student WHERE id = :id"), {"id": id}).fetchone()
        return render_template('edit.html', student=student)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)

