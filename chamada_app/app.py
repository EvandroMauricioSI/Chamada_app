
allowed_radius = 100  # Radius in meters within which student must be to register presence

import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the Haversine distance between two points on the earth."""
    R = 6371000  # Radius of the Earth in meters
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3

from geopy.distance import geodesic

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

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        db = get_db()
        cursor = db.cursor()
        
        # Verificar se o nome de usuário já existe
        existing_user = cursor.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
        if existing_user:
            # Se o nome de usuário já existir, mostrar uma mensagem ao usuário
            return render_template('create_user.html', error="Nome de usuário já está em uso. Por favor, escolha outro.")

        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        db.commit()

        return redirect(url_for('user_login'))

    return render_template('create_user.html')


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        user = cursor.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,)).fetchone()

        # Adicione esta linha para imprimir o usuário buscado do banco de dados
        print(user)

        if user and password:
            # Adicione esta linha para imprimir se a senha estiver correta
            print("Senha correta!")
            
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['role'] = user[3]

            if user[3] == 'Aluno':
                return render_template('dashboard_aluno.html', nome=username)
            elif user[3] == 'Professor':
                return render_template('dashboard_professor.html', nome=username)
        else:
            # Adicione esta linha para imprimir se a senha estiver incorreta ou o usuário não foi encontrado
            print("Senha incorreta ou usuário não encontrado.")

    return render_template('login.html')


@app.route('/register_presence', methods=['GET', 'POST'])

def register_presence():
    if 'username' not in session:
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        turma_id = request.form['turma_id']
        aluno_id = session['user_id']
        aluno_latitude = float(request.form['latitude'])
        aluno_longitude = float(request.form['longitude'])

        # Retrieve the professor's location for the given turma
        db = get_db()
        cursor = db.cursor()
        professor_id = cursor.execute("SELECT professor_id FROM turmas WHERE id = ?", (turma_id,)).fetchone()[0]
        professor_latitude, professor_longitude = cursor.execute("SELECT latitude, longitude FROM users WHERE id = ?", (professor_id,)).fetchone()

        # Calculate the distance between the student and professor using haversine_distance
        distance = haversine_distance(aluno_latitude, aluno_longitude, professor_latitude, professor_longitude)

        # Check if the student is within the allowed radius
        if distance <= allowed_radius:
            cursor.execute("INSERT INTO presencas (aluno_id, turma_id, data, hora, local) VALUES (?, ?, date('now'), time('now'), ?)", (aluno_id, turma_id, "Verified Location"))
            db.commit()
            return "Presença registrada com sucesso!"
        else:
            return "Você está fora do raio permitido para registrar presença."

    return render_template('register_presence.html')

def view_turmas():
    user_id = session['user_id']
    role = session['role']

    db = get_db()
    cursor = db.cursor()

    if role == 'Aluno':
        turmas = cursor.execute("SELECT t.nome FROM turmas t JOIN aluno_turma at ON t.id = at.turma_id WHERE at.aluno_id = ?", (user_id,)).fetchall()
    elif role == 'Professor':
        turmas = cursor.execute("SELECT nome FROM turmas WHERE professor_id = ?", (user_id,)).fetchall()

    return render_template('view_turmas.html', turmas=turmas)

@app.route('/view_presences')
def view_presences():
    professor_id = session['user_id']

    db = get_db()
    cursor = db.cursor()
    presencas = cursor.execute("SELECT u.username, t.nome, p.data, p.hora, p.local FROM presencas p JOIN users u ON p.aluno_id = u.id JOIN turmas t ON p.turma_id = t.id WHERE t.professor_id = ?", (professor_id,)).fetchall()

    return render_template('view_presences.html', presencas=presencas)

@app.route('/register_attendance/<int:turma_id>', methods=['POST'])
def register_attendance(turma_id):
    user_id = session.get('user_id')
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_time = datetime.now().strftime('%H:%M:%S')
    db = get_db()
    db.execute('INSERT INTO presencas (aluno_id, turma_id, data, hora, local) VALUES (?, ?, ?, ?, ?)', (user_id, turma_id, current_date, current_time, 'Sala A'))
    db.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
