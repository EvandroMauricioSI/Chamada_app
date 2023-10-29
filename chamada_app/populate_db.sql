
INSERT INTO users (role, username, password, latitude, longitude) VALUES 
('Aluno', 'aluno1', 'senha1', -23.5616, -46.6561),
('Aluno', 'aluno2', 'senha2', -23.5620, -46.6565),
('Professor', 'prof1', 'senha3', -23.5618, -46.6563),
('Professor', 'prof2', 'senha4', -23.5617, -46.6562);

INSERT INTO turmas (nome, professor_id, latitude, longitude) VALUES 
('Turma A', 3, -23.5618, -46.6563),
('Turma B', 4, -23.5617, -46.6562);

INSERT INTO aluno_turma (aluno_id, turma_id) VALUES 
(1, 1),
(1, 2),
(2, 1);

INSERT INTO presencas (aluno_id, turma_id, data, hora, local) VALUES 
(1, 1, '2023-10-29', '09:00', 'Sala A'),
(2, 1, '2023-10-29', '09:05', 'Sala A');
