-- Tabela de usuários
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    role TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    latitude REAL,
    longitude REAL
);

-- Tabela de turmas
CREATE TABLE turmas (
    id INTEGER PRIMARY KEY,
    nome TEXT NOT NULL,
    professor_id INTEGER,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    FOREIGN KEY (professor_id) REFERENCES users(id)
);

-- Tabela para associar alunos a turmas
CREATE TABLE aluno_turma (
    aluno_id INTEGER,
    turma_id INTEGER,
    PRIMARY KEY (aluno_id, turma_id),
    FOREIGN KEY (aluno_id) REFERENCES users(id),
    FOREIGN KEY (turma_id) REFERENCES turmas(id)
);

-- Tabela para registrar presenças
CREATE TABLE presencas (
    id INTEGER PRIMARY KEY,
    aluno_id INTEGER,
    turma_id INTEGER,
    data TEXT NOT NULL,
    hora TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    FOREIGN KEY (aluno_id) REFERENCES users(id),
    FOREIGN KEY (turma_id) REFERENCES turmas(id)
);

CREATE TABLE Aulas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    turma_id INTEGER NOT NULL,
    data TEXT NOT NULL, -- SQLite não possui tipo DATE, TEXT é comum para armazenar datas
    horaAbertura TEXT NOT NULL,
    horaFechamento TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    FOREIGN KEY (turma_id) REFERENCES turmas(id)
);
