

allowed_radius = 100  # Radius in meters within which student must be to register presence

import math
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, g

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
DATABASE = 'chamada.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        user = cursor.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,)).fetchone()

        if user and user[2] == password:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            if user[3] == 'Aluno':
                return redirect(url_for('dashboard_aluno'))
            elif user[3] == 'Professor':
                return render_template('dashboard_professor.html', nome=username)
        else:
            return render_template('login.html', error="Senha incorreta ou usuário não encontrado.")

    return render_template('login.html')

@app.route('/dashboard_aluno')
def dashboard_aluno():
    # Certificar-se de que o usuário está logado como aluno
    if 'user_id' not in session or session['role'] != 'Aluno':
        return redirect(url_for('index'))

    with get_db() as conn:
        cursor = conn.cursor()
        # Recuperando as turmas do aluno logado
        turmas = cursor.execute('''
            SELECT t.nome, u.username
            FROM turmas t
            INNER JOIN aluno_turma m ON t.id = m.turma_id
            INNER JOIN users u ON t.professor_id = u.id
            WHERE m.aluno_id = ?
        ''', (session['user_id'],)).fetchall()
    return render_template('dashboard_aluno.html', nome=session['username'], turmas=turmas)

if __name__ == '__main__':
    app.run(debug=True)

