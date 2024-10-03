-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS voting;

-- Use the voting database
USE voting;

-- Users table
CREATE TABLE IF NOT EXISTS Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Email VARCHAR(255) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Polls table
CREATE TABLE IF NOT EXISTS Polls (
    PollID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT NOT NULL,
    Title VARCHAR(255) NOT NULL,
    Description TEXT,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID)
);

-- Choices table
CREATE TABLE IF NOT EXISTS Choices (
    ChoiceID INT PRIMARY KEY AUTO_INCREMENT,
    PollID INT NOT NULL,
    ChoiceText VARCHAR(255) NOT NULL,
    FOREIGN KEY (PollID) REFERENCES Polls(PollID)
);

-- Votes table
CREATE TABLE IF NOT EXISTS Votes (
    VoteID INT PRIMARY KEY AUTO_INCREMENT,
    ChoiceID INT NOT NULL,
    VoterIP VARCHAR(45) NOT NULL,
    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ChoiceID) REFERENCES Choices(ChoiceID)
);

-- Constraint to ensure each poll has between 2 and 5 choices
-- Note: This constraint will be added only if it doesn't already exist
DELIMITER //
CREATE PROCEDURE AddConstraintIfNotExists()
BEGIN
    IF NOT EXISTS (
        SELECT * FROM information_schema.TABLE_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = 'voting'
        AND CONSTRAINT_NAME = 'chk_choice_count'
        AND TABLE_NAME = 'Polls'
    ) THEN
        ALTER TABLE Polls
        ADD CONSTRAINT chk_choice_count
        CHECK (
            (SELECT COUNT(*) FROM Choices WHERE PollID = Polls.PollID) BETWEEN 2 AND 5
        );
    END IF;
END //
DELIMITER ;

CALL AddConstraintIfNotExists();
DROP PROCEDURE IF EXISTS AddConstraintIfNotExists;
