USE mysql_exercise_db;

-- Drop existing tables
DROP TABLE IF EXISTS question_tag_relations;
DROP TABLE IF EXISTS question_tags;
DROP TABLE IF EXISTS user_answer_history;
DROP TABLE IF EXISTS answers;
DROP TABLE IF EXISTS multiple_choice_options;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS question_types;
DROP TABLE IF EXISTS difficulty_levels;

-- Create question types table
CREATE TABLE question_types (
    type_id INT PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create difficulty levels table
CREATE TABLE difficulty_levels (
    level_id INT PRIMARY KEY,
    level_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create questions table
CREATE TABLE questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    type_id INT NOT NULL,
    difficulty_level INT NOT NULL,
    content TEXT NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50) DEFAULT 'system',
    updated_by VARCHAR(50) DEFAULT 'system',
    INDEX idx_type_difficulty (type_id, difficulty_level),
    INDEX idx_create_time (create_time),
    INDEX idx_is_active (is_active)
);

-- Create options table
CREATE TABLE multiple_choice_options (
    option_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    option_content TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT FALSE,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_question_correct (question_id, is_correct),
    INDEX idx_is_active (is_active)
);

-- Create answers table
CREATE TABLE answers (
    answer_id INT AUTO_INCREMENT PRIMARY KEY,
    question_id INT NOT NULL,
    answer_content TEXT NOT NULL,
    explanation TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(50) DEFAULT 'system',
    updated_by VARCHAR(50) DEFAULT 'system',
    INDEX idx_question (question_id),
    INDEX idx_is_active (is_active)
);

-- Create user answer history table
CREATE TABLE user_answer_history (
    history_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    question_id INT NOT NULL,
    user_answer TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL,
    answer_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_question (user_id, question_id),
    INDEX idx_answer_time (answer_time),
    INDEX idx_question_id (question_id)
);

-- Create question tags table
CREATE TABLE question_tags (
    tag_id INT AUTO_INCREMENT PRIMARY KEY,
    tag_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    INDEX idx_tag_name (tag_name),
    INDEX idx_is_active (is_active)
);

-- Create question-tag relations table
CREATE TABLE question_tag_relations (
    question_id INT NOT NULL,
    tag_id INT NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (question_id, tag_id),
    INDEX idx_tag (tag_id)
);

-- Insert difficulty levels
INSERT INTO difficulty_levels (level_id, level_name, description) VALUES 
(1, 'Beginner', 'Basic questions suitable for beginners'),
(2, 'Elementary', 'Requires understanding of basic concepts'),
(3, 'Intermediate', 'Requires comprehensive knowledge'),
(4, 'Advanced', 'Requires deep understanding and experience'),
(5, 'Expert', 'Requires professional-level knowledge');

-- Insert question types
INSERT INTO question_types (type_id, type_name, description) VALUES 
(1, '选择题', 'Select the correct answer from multiple options'),
(2, '判断题', 'Judge whether the statement is true or false'),
(3, '填空题', 'Fill in the blank with the correct answer'),
(4, '简答题', 'Provide a brief answer to the question'),
(5, 'MySQL设计题', 'Design database or write complex SQL');
