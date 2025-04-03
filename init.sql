CREATE TABLE hallucination_evaluations (
        id SERIAL PRIMARY KEY,
        context TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        result TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);