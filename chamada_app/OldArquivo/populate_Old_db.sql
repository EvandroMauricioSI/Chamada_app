-- Inserindo usuários
INSERT INTO users (role, username, password, latitude, longitude) VALUES 
('Aluno', 'aluno1', 'senha1', -23.5616, -46.6561),
('Aluno', 'aluno2', 'senha2', -23.5620, -46.6565),
('Professor', 'prof1', 'senha3', -23.5618, -46.6563),
('Professor', 'prof2', 'senha4', -23.5617, -46.6562);

-- Inserindo turmas
INSERT INTO turmas (nome, professor_id, latitude, longitude) VALUES 
('Turma A', 3, -23.5618, -46.6563),
('Turma B', 4, -23.5617, -46.6562);

-- Associando alunos às turmas
INSERT INTO aluno_turma (aluno_id, turma_id) VALUES 
(1, 1),
(1, 2),
(2, 1);

-- Inserindo aulas
INSERT INTO Aulas (turma_id, data, horaAbertura, horaFechamento, latitude, longitude) VALUES
(1, '2023-11-03', '08:00', '12:00', -23.5618, -46.6563),
(2, '2023-11-04', '09:00', '13:00', -23.5617, -46.6562);

-- Nota: As IDs das aulas devem ser inseridas manualmente caso o AUTOINCREMENT não esteja ativado ou se quisermos referenciar aulas específicas. 
-- Se o AUTOINCREMENT estiver ativado e não precisarmos de referências específicas, as IDs serão geradas automaticamente.

-- Inserindo presenças
-- Nota: Precisamos garantir que as IDs das aulas correspondam às IDs geradas na inserção anterior.
INSERT INTO presencas (aula_id, aluno_id, data, hora, latitude, longitude) VALUES 
-- Presumindo que a aula com ID 1 pertence à turma 1 e assim por diante.
(1, 1, '2023-11-03', '08:00', -23.5616, -46.6561),
(1, 2, '2023-11-03', '08:05', -23.5620, -46.6565);

-- Nota: A data e a hora das presenças devem coincidir com a data da aula e o horário em que o aluno está presente.
