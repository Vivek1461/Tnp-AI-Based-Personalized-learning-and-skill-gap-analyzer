CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    student_id TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    skill_name TEXT
);

CREATE TABLE user_skills (
    user_id INT,
    skill_id INT,
    score INT
);

CREATE TABLE career_paths (
    id SERIAL PRIMARY KEY,
    role_name TEXT
);

CREATE TABLE roadmaps (
    id SERIAL PRIMARY KEY,
    user_id INT,
    roadmap JSON
);

CREATE TABLE login_sessions (
    id SERIAL PRIMARY KEY,
    user_id INT,
    token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL
);