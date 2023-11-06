allowed_radius = 100  # Radius in meters within which student must be to register presence

from datetime import datetime
import math
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, flash, jsonify, render_template, request, redirect, url_for, session, g

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
        try:
            role = request.form['role']
            username = request.form['username']
            password = request.form['password']

            # Connect to the database
            conn = sqlite3.connect('chamada.db')
            cur = conn.cursor()

            # Insert the new user into the database
            cur.execute('INSERT INTO users (role, username, password) VALUES (?, ?, ?)', 
                        (role, username, password))
            conn.commit()

            # Close the database connection
            conn.close()

            flash('Conta criada com sucesso! Por favor, faça o login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Erro: Este nome de usuário já está em uso. Por favor, escolha outro.', 'error')
            return render_template('create_user.html'), 400
        except Exception as e:
            flash('Erro ao criar a conta: ' + str(e), 'error')
            return render_template('create_user.html'), 400

    # Render the create user form if the method is GET or the user creation was not successful
    return render_template('create_user.html')

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
                return redirect(url_for('dashboard_professor'))
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
        
        # Recuperando as aulas disponíveis para o aluno logado
        aulas = cursor.execute('''
            SELECT Aulas.id, Aulas.turma_id, Aulas.data, Aulas.horaAbertura, Aulas.horaFechamento, Aulas.latitude, Aulas.longitude
            FROM Aulas
            INNER JOIN aluno_turma ON Aulas.turma_id = aluno_turma.turma_id
            WHERE aluno_turma.aluno_id = ?
        ''', (session['user_id'],)).fetchall()

    return render_template('dashboard_aluno.html', nome=session['username'], turmas=turmas, aulas=aulas)

@app.route('/register_presence', methods=['POST'])
def register_presence():
    if request.method == 'POST':
        try:
            # Obter os dados do formulário
            data = request.get_json()
            turma_id = data['turmaId']
            latitude = data['latitude']
            longitude = data['longitude']
            
            # Verificar se a localização está dentro do raio permitido
            # e se o horário atual está dentro do intervalo permitido para a aula
            # Essa lógica precisará ser implementada
            
            # Registrar a presença no banco de dados
            conn = sqlite3.connect('chamada.db')
            cur = conn.cursor()

            # Substituir 'id_aluno' pelo ID do aluno atual, que deve ser obtido de outra maneira, possivelmente através da sessão
            id_aluno = 'id_aluno_aqui'  
            cur.execute('INSERT INTO Presencas (turma_id, aluno_id, data, hora) VALUES (?, ?, CURRENT_DATE, CURRENT_TIME)', (turma_id, id_aluno))

            conn.commit()
            conn.close()

            return jsonify({'success': True})

        except Exception as e:
            # Em caso de erro, retornar uma resposta indicando falha
            return jsonify({'success': False, 'error': str(e)})

@app.route('/create_lesson', methods=['POST'])
def create_lesson():
 if request.method == 'POST':
        try:
            turma_id = request.form['turma_id']    
            if not turma_id:
                # Handle the error - turma_id is empty
                print(f"O campo turma_id está vazio.: ")
                return redirect(url_for('dashboard_professor', message='O campo turma_id está vazio.'))

            # Se turma_id não estiver vazio, tente converter para int
            try:
                turma_id = int(turma_id)
            except ValueError as e:
                # Handle the error - turma_id is not an integer
                print(f"O campo turma_id não é um inteiro válido.: {e}", e.args)
                return redirect(url_for('dashboard_professor', message='O campo turma_id não é um inteiro válido.'))

            latitude = request.form['latitude']
            longitude = request.form['longitude']
            data = request.form['data']
            horaAbertura = request.form['horaAbertura']
            horaFechamento = request.form['horaFechamento']

            try:
                data = datetime.strptime(data, '%Y-%m-%d').date().isoformat()
                horaAbertura = datetime.strptime(horaAbertura, '%H:%M:%S').time().isoformat()
                horaFechamento = datetime.strptime(horaFechamento, '%H:%M:%S').time().isoformat()
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError as e:
                flash(f'Erro de validação: {e}')
                return render_template('dashboard_professor.html'), 400
    
            # Conexão com o banco de dados
            conn = sqlite3.connect('chamada.db')
            cur = conn.cursor()

            # Inserir a nova aula no banco de dados
            sql = 'INSERT INTO Aulas (turma_id, data, horaAbertura, horaFechamento, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)'
            values = (turma_id, data, horaAbertura, horaFechamento, latitude, longitude)
            cur.execute(sql, values)
            
            # Verificar se os dados foram inseridos
            print(f"Linhas inseridas: {cur.rowcount}")

            # Salvar as mudanças e fechar a conexão com o banco de dados
            conn.commit()
            conn.close()
            
        except sqlite3.IntegrityError as e:
            # Tratar erros de integridade
            print(f"Erro de integridade: {e}")
            return redirect(url_for('dashboard_professor', message='Erro de integridade!'))
            # ...
        except Exception as e:
            # Tratar outros erros
            print(f"Erro ao inserir dados: {e}", e.args)
            return redirect(url_for('dashboard_professor', message='Erro ao inserir dados'))
            
            # Redirecionar para a página de dashboard do professor com uma mensagem de sucesso
            
        except sqlite3.IntegrityError:
            flash('Erro: Não foi possível criar a aula.', 'error')
            return render_template('dashboard_professor.html'), 400
        except Exception as e:
            flash('Erro ao criar a criar a aula: ' + str(e), 'error')
            return render_template('dashboard_professor.html'), 400

        # (O redirecionamento e a mensagem de sucesso são apenas ilustrativos)
        return redirect(url_for('dashboard_professor', message='Aula criada com sucesso!'))

@app.route('/dashboard_professor')
def dashboard_professor():
    try:
        # Connect to the database
        conn = sqlite3.connect('chamada.db')
        cur = conn.cursor()

        # Retrieve the professor's classes (assuming there's a professor_id to filter with)
        # This SQL query is just a placeholder; you need to replace it with your actual query
        cur.execute('SELECT * FROM turmas WHERE professor_id = ?', (session['user_id'],))
        turmas = cur.fetchall()

        # Close the database connection
        conn.close()

        return render_template('dashboard_professor.html', turmas=turmas)
    except Exception as e:
        flash('Erro ao carregar o dashboard: ' + str(e), 'error')
        return render_template('error.html'), 400

if __name__ == '__main__':
    app.run(debug=True)
