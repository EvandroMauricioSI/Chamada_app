from datetime import datetime, time, timedelta
import pandas as pd
import math
from geopy.distance import geodesic
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, flash, jsonify, render_template, request, redirect, send_from_directory, url_for, session, g

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
DATABASE = 'chamada.db'

# Defina os limites de horário
HORA_INICIO_MIN = time(7, 0, 0)
HORA_INICIO_MAX = time(22, 0, 0)
HORA_TERMINO_MAX_Madrugada = time(2, 0, 0)
HORA_TERMINO_MAX_Noite = time(22, 0, 0)
DURACAO_NORMAL_AULA = timedelta(hours=4)  # Duração normal de 4 horas

allowed_radius = 50  # Radius in meters within which student must be to register presence

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def check_time_within_range(start_time_str, end_time_str, current_time_str):
    """
    Verifica se o horário atual está dentro do intervalo de horário de início e término.
    """
    start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
    end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
    current_time = datetime.strptime(current_time_str, '%H:%M:%S').time()
    
    return start_time <= current_time <= end_time

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
    # Certifique-se de que o usuário está logado como aluno
    if 'user_id' not in session or session['role'] != 'Aluno':
        return redirect(url_for('index'))

    with get_db() as conn:
        cursor = conn.cursor()

        # Recuperando as turmas do aluno logado
        turmas = cursor.execute('''
            SELECT turmas.nome, users.username
            FROM turmas
            INNER JOIN aluno_turma ON turmas.id = aluno_turma.turma_id
            INNER JOIN users ON turmas.professor_id = users.id
            WHERE aluno_turma.aluno_id = ?
        ''', (session['user_id'],)).fetchall()
        print("Turmas:", turmas)  # Log para verificar as turmas

        # Recuperando e agrupando as aulas disponíveis por nome da turma com status de presença
        aulas = cursor.execute('''
            SELECT Aulas.id, Aulas.turma_id, Aulas.data, Aulas.horaAbertura, Aulas.horaFechamento, 
                Aulas.latitude, Aulas.longitude, turmas.nome as turma_nome,
                CASE WHEN pres.id IS NOT NULL THEN 'Presente' ELSE 'Ausente' END as status_presenca
            FROM Aulas
            INNER JOIN turmas ON Aulas.turma_id = turmas.id
            INNER JOIN aluno_turma ON turmas.id = aluno_turma.turma_id
            LEFT JOIN presencas pres ON Aulas.id = pres.aula_id AND pres.aluno_id = ?
            WHERE aluno_turma.aluno_id = ?
            ORDER BY turmas.nome, Aulas.data
        ''', (session['user_id'], session['user_id'])).fetchall()
        print("Aulas agrupadas por turma:", aulas)  # Log para verificar as aulas
      
        # Recuperando e agrupando as aulas mais recentes para cada turma
        aulas_recentes = cursor.execute('''
            SELECT 
                t.nome, 
                u.username, 
                a.data, 
                a.horaAbertura, 
                a.horaFechamento, 
                a.latitude, 
                a.longitude,
                a.id as aula_id,
                t.id as turma_id
            FROM 
                aluno_turma at
            INNER JOIN 
                turmas t ON at.turma_id = t.id
            INNER JOIN 
                users u ON t.professor_id = u.id
            INNER JOIN 
                (SELECT 
                    Aulas.turma_id, 
                    MAX(Aulas.data || ' ' || Aulas.horaAbertura) as max_datetime
                FROM Aulas
                GROUP BY Aulas.turma_id) as latest ON t.id = latest.turma_id
            INNER JOIN 
                Aulas a ON t.id = a.turma_id AND (a.data || ' ' || a.horaAbertura) = latest.max_datetime
            WHERE 
                at.aluno_id = ?
            ORDER BY 
                a.data DESC, a.horaAbertura DESC
        ''', (session['user_id'],)).fetchall()

        print("Aulas Recentes por turma:", aulas_recentes)  # Log para verificar as aulas

        # Estrutura para armazenar aulas agrupadas por nome da turma
        aulas_agrupadas_por_turma = {}
        for aula in aulas:
            turma_nome = aula[7]  # Aqui é assumido que turma_nome é o oitavo elemento na tupla aula
            if turma_nome not in aulas_agrupadas_por_turma:
                aulas_agrupadas_por_turma[turma_nome] = []
            aulas_agrupadas_por_turma[turma_nome].append(aula)


        print("Aulas agrupadas por turma (estrutura):", aulas_agrupadas_por_turma)  # Log para estrutura

        # Consulta para buscar as informações para o relatório de presenças
        presencas = cursor.execute('''
            SELECT turmas.nome, COUNT(presencas.id) as total_presencas,
                   (SELECT COUNT(*) FROM Aulas WHERE Aulas.turma_id = turmas.id) as total_aulas
            FROM presencas
            INNER JOIN Aulas ON presencas.aula_id = Aulas.id
            INNER JOIN turmas ON Aulas.turma_id = turmas.id
            WHERE presencas.aluno_id = ?
            GROUP BY turmas.id
        ''', (session['user_id'],)).fetchall()
        print("Dados do relatório de presenças:", presencas)  # Log para verificar o relatório

        # Transformar os dados para um formato adequado para o template
        dados_relatorio = {
            'presencas': presencas,
            'taxa_presenca': [(turma, pres / total if total > 0 else 0) for turma, pres, total in presencas],
            'dados_grafico': [(turma, (pres / total) * 100 if total > 0 else 0) for turma, pres, total in presencas]
        }

        return render_template('dashboard_aluno.html', 
                       aluno_id=session['user_id'], 
                       nome=session['username'], 
                       turmas=turmas, 
                       aulas_recentes=aulas_recentes,  # Adicione esta linha
                       aulas_agrupadas_por_turma=aulas_agrupadas_por_turma, 
                       dados_relatorio=dados_relatorio)



@app.route('/create_presenca', methods=['POST'])
def create_presenca():
    response = {'status': 'error', 'message': 'Ocorreu um erro inesperado.'}
    print("Iniciando a função create_presenca")  # Print para iniciar a função

    if request.method == 'POST':
        try:
            aluno_id = request.form.get('aluno_id')
            print(f"aluno_id recebido: {aluno_id}")  # Print para mostrar o aluno_id recebido

            aula_id = request.form.get('aula_id')
            print(f"aula_id recebido: {aula_id}")  # Print para mostrar o aula_id recebido

            turma_id = request.form.get('turma_id')  # Certifique-se de que está sendo enviado no formulário HTML
            print(f"turma_id recebido: {turma_id}")  # Print para mostrar o turma_id recebido
            
            if not aluno_id or not aula_id or not turma_id:
                #flash("Os campos aluno_id, aula_id e turma_id são obrigatórios.")
                #return redirect(url_for('dashboard_aluno'))
                response['message'] = "Os campos aluno_id, aula_id e turma_id são obrigatórios."
                return jsonify(response), 400

            # Converta os IDs para inteiros e valide-os
            try:
                aluno_id = int(aluno_id)
                aula_id = int(aula_id)
                turma_id = int(turma_id)
            except ValueError:
                #flash("Os campos aluno_id, aula_id e turma_id devem ser números inteiros válidos.")
                #return redirect(url_for('dashboard_aluno'))
                response['message'] = "Os campos aluno_id, aula_id e turma_id devem ser números inteiros válidos."
                return jsonify(response), 400

            data = request.form['data']
            hora = request.form['hora']
            latitude = request.form['latitude']
            longitude = request.form['longitude']
            
            # Processamento e validação de data, hora e coordenadas como no seu código original...

            print(f"Preparando para inserir no banco de dados: aula_id={aula_id}, aluno_id={aluno_id}, ...")

            with sqlite3.connect('chamada.db') as conn:
                cur = conn.cursor()
                cur.execute("SELECT horaAbertura, horaFechamento, latitude, longitude FROM Aulas WHERE id=?", (aula_id,))
                aula_info = cur.fetchone()
                

                if aula_info is None:
                    response['message'] = 'Aula não encontrada.'
                    return jsonify(response), 404
                    #flash('Aula não encontrada.')
                    #return redirect(url_for('dashboard_aluno'))

                # Verificação de horários, localização e demais regras como no seu código original...

                 # Aqui adicionamos a lógica para verificar o horário
                hora_atual = datetime.now().strftime('%H:%M:%S')
                data_atual = datetime.now().strftime('%Y-%m-%d')
                if not check_time_within_range(aula_info[0], aula_info[1], hora_atual) or data_atual != data:
                    response = {
                        'status': 'error',
                        'message': 'Não é possível registrar presença fora do horário de aula.'
                    }
                    response['message'] = 'Não é possível registrar presença fora do horário de aula.'
                    return jsonify(response), 403

                # Verifique se a presença já foi registrada
                cur.execute("SELECT * FROM presencas WHERE aluno_id=? AND aula_id=? AND data=?", (aluno_id, aula_id, data))
                if cur.fetchone():
                    #flash('Presença já registrada hoje para esta aula.')
                    #return redirect(url_for('dashboard_aluno'))
                    response['message'] = 'Você já registrou essa presença.'
                    return jsonify(response), 409
                    

                # Inserção da presença no banco de dados
                sql = 'INSERT INTO presencas (aula_id, aluno_id, data, hora, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)'
                values = (aula_id, aluno_id, data, hora, latitude, longitude)
                cur.execute(sql, values)

                print(f"Linhas inseridas: {cur.rowcount}")
                conn.commit()  # Não se esqueça de commitar as alterações no banco de dados
                response['status'] = 'success'
                response['message'] = 'Presença registrada com sucesso!'
                return jsonify(response), 200  # Retornar JSON para chamadas AJAX
            
        except sqlite3.IntegrityError as e:
            print(f"Erro de integridade: {e}")  # Print para mostrar o erro de integridade
            response['message'] = f'Erro de integridade: {e}'
            return jsonify(response), 500
            #flash('Erro de integridade!')
            #return redirect(url_for('dashboard_aluno'))
        
        except Exception as e:
            print(f"Erro ao inserir dados: {e}")  # Print para mostrar outros erros
            response['message'] = f'Erro ao inserir dados: {e}'
            return jsonify(response), 500           
            #flash(f'Erro ao inserir dados: {e}')
            #return redirect(url_for('dashboard_aluno'))

    return jsonify({'status': 'success', 'message': 'Presença registrada com sucesso!'})

@app.route('/create_lesson', methods=['POST'])
def create_lesson():
    if request.method == 'POST':
        try:
            print("Requisição POST recebida para /create_lesson")
            turma_id = request.form.get('turma_id')
            data = request.form.get('data')
            horaAbertura = request.form.get('horaAbertura')
            horaFechamento = request.form.get('horaFechamento')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')

            print(f"Form data recebido: turma_id={turma_id}, data={data}, horaAbertura={horaAbertura}, horaFechamento={horaFechamento}, latitude={latitude}, longitude={longitude}")

            # Verifique se algum dos campos está vazio, incluindo latitude e longitude
            if not all([turma_id, data, horaAbertura, horaFechamento, latitude, longitude]):
                print("Erro: Nem todos os campos foram fornecidos.")
                return jsonify({'status': 'error', 'message': 'Todos os campos são obrigatórios.'}), 400

            print("Todos os campos necessários estão presentes.")

            # Conversão e validação dos dados
            turma_id = int(turma_id)
            data = datetime.strptime(data, '%Y-%m-%d').date()
            horaAbertura = datetime.strptime(horaAbertura, '%H:%M:%S').time()
            horaFechamento = datetime.strptime(horaFechamento, '%H:%M:%S').time()
            print(f"Form data após conversão: turma_id={turma_id}, data={data}, horaAbertura={horaAbertura}, horaFechamento={horaFechamento}, latitude={latitude}, longitude={longitude}")

            # Verificar os limites de horário de início
            if horaAbertura < HORA_INICIO_MIN:
                return jsonify({'status': 'error', 'message': 'A aula não pode começar antes das 07:00:00.'}), 400
            if horaAbertura > HORA_INICIO_MAX:
                return jsonify({'status': 'error', 'message': 'A aula não pode ser criada após as 22:00:00.'}), 400

            # Ajustar a hora de fechamento com base na hora de abertura e no limite máximo
            hora_inicio_aula = datetime.combine(data, horaAbertura)
            hora_fechamento_proposta = hora_inicio_aula + DURACAO_NORMAL_AULA
            hora_fechamento_final = hora_fechamento_proposta.time()

            if hora_fechamento_final < HORA_TERMINO_MAX_Madrugada or hora_fechamento_final > HORA_TERMINO_MAX_Noite:
                hora_fechamento_final = HORA_TERMINO_MAX_Noite
            else:
                hora_fechamento_final = hora_fechamento_proposta.time()


            # Conexão com o banco de dados
            conn = get_db()
            cur = conn.cursor()

            # Verificar se já existe aula em andamento
            print("Verificando se já existe aula em andamento para a turma e data fornecidas.")
            cur.execute('''
                SELECT * FROM Aulas
                WHERE turma_id = ? AND data = ?
                AND NOT (horaFechamento <= ? OR horaAbertura >= ?)
            ''', (turma_id, data.isoformat(), horaAbertura.isoformat(), horaFechamento.isoformat()))
            aulas = cur.fetchall()

            if aulas:
                print("Erro: Já existe uma aula em andamento para esta turma no intervalo especificado.")
                return jsonify({'status': 'error', 'message': 'Já existe uma aula em andamento para esta turma no intervalo especificado.'}), 400

            print("Nenhuma aula em andamento encontrada, prosseguindo para criar nova aula.")

            # Inserir a nova aula no banco de dados com a hora de fechamento ajustada
            sql = 'INSERT INTO Aulas (turma_id, data, horaAbertura, horaFechamento, latitude, longitude) VALUES (?, ?, ?, ?, ?, ?)'
            values = (turma_id, data.isoformat(), horaAbertura.isoformat(), hora_fechamento_final.isoformat(), latitude, longitude)
            cur.execute(sql, values)

            print(f"Aula criada com sucesso. ID da nova aula: {cur.lastrowid}")

            # Salvar as mudanças e fechar a conexão com o banco de dados
            conn.commit()

            return jsonify({'status': 'success', 'message': 'Aula criada com sucesso!'}), 200

        except ValueError as e:
            print(f"Erro de conversão de valor: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400
        except sqlite3.IntegrityError as e:
            print(f"Erro de integridade no banco de dados: {e}")
            return jsonify({'status': 'error', 'message': 'Erro de integridade: ' + str(e)}), 500
        except Exception as e:
            print(f"Erro inesperado: {e}")
            return jsonify({'status': 'error', 'message': 'Erro ao inserir dados: ' + str(e)}), 500

    print("Recebido um método que não é POST para /create_lesson")
    return jsonify({'status': 'error', 'message': 'Método inválido.'}), 405

@app.route('/dashboard_professor')
def dashboard_professor():
    # Certifique-se de que o usuário está logado como professor
    if 'user_id' not in session or session['role'] != 'Professor':
        return redirect(url_for('index'))

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Recuperando as turmas do professor logado
        turmas = cursor.execute('''
            SELECT t.nome, u.username
            FROM turmas t
            INNER JOIN users u ON t.professor_id = u.id
            WHERE t.professor_id = ?
        ''', (session['user_id'],)).fetchall()
        
        # Recuperando e agrupando as aulas disponíveis por nome da turma
        aulas = cursor.execute('''
            SELECT Aulas.id, Aulas.turma_id, Aulas.data, Aulas.horaAbertura, Aulas.horaFechamento, Aulas.latitude, Aulas.longitude, turmas.nome as turma_nome
            FROM Aulas
            INNER JOIN turmas ON Aulas.turma_id = turmas.id
            WHERE turmas.professor_id = ?
            ORDER BY turmas.nome, Aulas.data
        ''', (session['user_id'],)).fetchall()

        # Lógica para agrupar aulas por turma...
        aulas_agrupadas_por_turma = {}
        for aula in aulas:
            turma_nome = aula[7]
            if turma_nome not in aulas_agrupadas_por_turma:
                aulas_agrupadas_por_turma[turma_nome] = []
            aulas_agrupadas_por_turma[turma_nome].append(aula)

        # Adicionar consulta SQL para obter o relatório de presenças por disciplina
        presencas_por_disciplina = cursor.execute('''
            SELECT 
                turmas.nome,
                COUNT(DISTINCT Aulas.id) AS total_aulas,
                alunos_por_turma.total_alunos,
                COUNT(presencas.id) AS total_presencas_registradas,
                alunos_por_turma.total_alunos * COUNT(DISTINCT Aulas.id) AS total_presencas_possiveis,
                (100.0 * COUNT(presencas.id) / NULLIF(alunos_por_turma.total_alunos * COUNT(DISTINCT Aulas.id), 0)) AS percentual_medio_presenca
            FROM 
                turmas
            LEFT JOIN 
                Aulas ON turmas.id = Aulas.turma_id
            LEFT JOIN (
                SELECT 
                    turma_id, 
                    COUNT(aluno_id) AS total_alunos
                FROM 
                    aluno_turma
                GROUP BY 
                    turma_id
            ) AS alunos_por_turma ON turmas.id = alunos_por_turma.turma_id
            LEFT JOIN 
                presencas ON Aulas.id = presencas.aula_id
            WHERE 
                turmas.professor_id = ?
            GROUP BY 
                turmas.id
        ''',(session['user_id'],)).fetchall()

        dados_grafico = [
        {
            'nome_disciplina': disciplina[0],  # Nome da disciplina
            'percentual_presenca': disciplina[5] if disciplina[5] is not None else 0  # Percentual de presença
        }
        for disciplina in presencas_por_disciplina
        ]
        dados_relatorio = {
            'presencas_por_disciplina': presencas_por_disciplina,
            'dados_grafico': dados_grafico
            }

        dados_grafico_json = jsonify(dados_grafico).json

        return render_template('dashboard_professor.html', 
                            nome=session['username'], 
                            turmas=turmas, 
                            aulas_agrupadas_por_turma=aulas_agrupadas_por_turma, 
                            dados_relatorio=dados_relatorio,
                            dados_grafico_json=dados_grafico_json)

@app.route('/aula_detalhes/<int:aula_id>')
def aula_detalhes(aula_id):
    conn = get_db()
    cursor = conn.cursor()

    # Consulta para obter a turma da aula específica
    cursor.execute('SELECT turma_id FROM Aulas WHERE id = ?', (aula_id,))
    turma_id = cursor.fetchone()[0]

    # Consulta para obter detalhes dos alunos associados à turma da aula
    detalhes_alunos = cursor.execute('''
        SELECT u.id, u.username, CASE WHEN p.id IS NOT NULL THEN 'Presente' ELSE 'Ausente' END as status
        FROM aluno_turma at
        INNER JOIN users u ON at.aluno_id = u.id
        LEFT JOIN presencas p ON u.id = p.aluno_id AND p.aula_id = ?
        WHERE at.turma_id = ? AND u.role = 'Aluno'
    ''', (aula_id, turma_id)).fetchall()

    detalhes_alunos = [dict(id=row[0], username=row[1], status=row[2]) for row in detalhes_alunos]
    return jsonify(detalhes_alunos)

@app.route('/registrar_presenca', methods=['POST'])
def registrar_presenca():
    try:
        aluno_id = request.form.get('aluno_id')
        aula_id = request.form.get('aula_id')
        with get_db() as conn:
            cur = conn.cursor()
            # Verifique se o aluno já está presente
            cur.execute('SELECT * FROM presencas WHERE aula_id = ? AND aluno_id = ?', (aula_id, aluno_id))
            if cur.fetchone():
                flash('Aluno já registrado como presente.', 'info')
            else:
                cur.execute('INSERT INTO presencas (aula_id, aluno_id, data, hora, latitude, longitude) VALUES (?, ?, CURRENT_DATE, CURRENT_TIME, 0, 0)', (aula_id, aluno_id))
                conn.commit()
                flash('Presença registrada com sucesso.', 'success')
        return redirect(url_for('dashboard_professor'))
    except Exception as e:
        print(f"Erro ao registrar presença: {e}")
        flash('Erro ao registrar presença.', 'error')
        return redirect(url_for('dashboard_professor'))


@app.route('/excluir_presenca', methods=['POST'])
def excluir_presenca():
    try:
        aluno_id = request.form.get('aluno_id')
        aula_id = request.form.get('aula_id')
        with get_db() as conn:
            cur = conn.cursor()
            # Verifique se o aluno está ausente
            cur.execute('SELECT * FROM presencas WHERE aula_id = ? AND aluno_id = ?', (aula_id, aluno_id))
            if not cur.fetchone():
                flash('Não há registro de presença para excluir.', 'info')
            else:
                cur.execute('DELETE FROM presencas WHERE aula_id = ? AND aluno_id = ?', (aula_id, aluno_id))
                conn.commit()
                flash('Presença excluída com sucesso.', 'success')
        return redirect(url_for('dashboard_professor'))
    except Exception as e:
        print(f"Erro ao excluir presença: {e}")
        flash('Erro ao excluir presença.', 'error')
        return redirect(url_for('dashboard_professor'))

@app.route('/excluir_aula/<int:aula_id>', methods=['POST'])
def excluir_aula(aula_id):
    try:
        with get_db() as conn:
            cur = conn.cursor()
            # Excluir registros de presença relacionados à aula
            cur.execute('DELETE FROM presencas WHERE aula_id = ?', (aula_id,))
            # Excluir a aula
            cur.execute('DELETE FROM Aulas WHERE id = ?', (aula_id,))
            conn.commit()
            flash('Aula excluída com sucesso.', 'success')
    except Exception as e:
        conn.rollback()
        print(f"Erro ao excluir aula: {e}")
        flash('Erro ao excluir aula.', 'error')
    return redirect(url_for('dashboard_professor'))

@app.route('/exportar_relatorio')
def exportar_relatorio():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Consulta SQL para obter a lista de presenças por turma
        query = '''
            SELECT 
                t.nome as Turma, 
                u.username as Aluno, 
                a.data as Data, 
                a.id as Aula, 
                CASE WHEN p.id IS NOT NULL THEN 'Presente' ELSE 'Ausente' END as Status
            FROM 
                turmas t
            INNER JOIN 
                aluno_turma at ON t.id = at.turma_id
            INNER JOIN 
                users u ON at.aluno_id = u.id
            LEFT JOIN 
                Aulas a ON t.id = a.turma_id
            LEFT JOIN 
                presencas p ON a.id = p.aula_id AND u.id = p.aluno_id
            WHERE 
                t.professor_id = ?
            ORDER BY 
                t.nome, u.username, a.data
        '''
        cursor.execute(query, (session['user_id'],))
        dados = cursor.fetchall()

        # Cria um DataFrame do Pandas
        df = pd.DataFrame(dados, columns=['Turma', 'Aluno', 'Data', 'Aula', 'Status'])

        # Defina o nome do arquivo
        filename = "relatorio_turmas.xlsx"

        # Salvar o DataFrame em um arquivo Excel
        df.to_excel(filename, index=False)

        return send_from_directory(directory='.', path=filename, as_attachment=True)

    except Exception as e:
        print("Erro ao gerar relatório: ", e)
        return "Erro ao gerar relatório", 500

@app.route('/get_turma_id/<string:turma_nome>')
def get_turma_id(turma_nome):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM turmas WHERE nome = ?", (turma_nome,))
    turma = cursor.fetchone()
    conn.close()
    if turma:
        return jsonify({'status': 'success', 'turma_id': turma[0]})
    else:
        return jsonify({'status': 'error', 'message': 'Turma não encontrada'})

@app.route('/exit')
def exit():
    # Aqui você pode adicionar qualquer lógica necessária, como limpar a sessão
    return render_template('exit.html')


if __name__ == '__main__':
    app.run(debug=True)
