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

INSERT INTO presencas (aluno_id, turma_id, data, hora, latitude, longitude) VALUES 
(1, 1, '2023-10-29', '09:00', -23.5616, -46.6561),
(2, 1, '2023-10-29', '09:05', -23.5620, -46.6565);

INSERT INTO Aulas (turma_id, data, horaAbertura, horaFechamento, latitude, longitude) VALUES
(1, '2023-11-03', '08:00', '12:00', -23.5618, -46.6563),
(2, '2023-11-04', '09:00', '13:00', -23.5617, -46.6562),
(3, '2023-11-05', '10:00', '14:00', -23.5618, -46.6563),
(4, '2023-11-06', '11:00', '15:00', -23.5617, -46.6562),
(5, '2023-11-07', '12:00', '16:00', -23.5616, -46.6561);
