CREATE DATABASE voting;
\c voting;
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE polls (
    poll_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE poll_options (
    option_id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES polls(poll_id),
    option_text VARCHAR(255) NOT NULL
);

CREATE TABLE votes (
    vote_id SERIAL PRIMARY KEY,
    poll_id INTEGER REFERENCES polls(poll_id),
    option_id INTEGER REFERENCES poll_options(option_id),
    ip_address INET NOT NULL,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


