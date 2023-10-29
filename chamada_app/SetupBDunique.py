import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'chamada.db'

def insert_initial_users():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Lista de usuários iniciais
    users = [
        ('Aluno', 'Aluno1', generate_password_hash('Aluno1')),
        ('Aluno', 'Aluno2', generate_password_hash('Aluno2')),
        ('Aluno', 'Aluno3', generate_password_hash('Aluno3')),
        ('Professor', 'Professor1', generate_password_hash('Professor1')),
        ('Professor', 'Professor2', generate_password_hash('Professor2')),
        ('Professor', 'Professor3', generate_password_hash('Professor3'))
    ]

    cursor.executemany("INSERT INTO users (role, username, password) VALUES (?, ?, ?)", users)
    conn.commit()
    conn.close()

insert_initial_users()