import sys
import os
import logging
from typing import List, Dict, Any, Tuple
import mysql.connector
import json
import random

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.database.db_manager import DatabaseManager
from src.config.constants import Constants

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuestionGenerator:
    def __init__(self):
        self.db_manager = DatabaseManager()
        # 添加题目类型映射
        self.type_mapping = {
            "multiple_choice": "MySQL选择题",
            "true_false": "MySQL判断题",
            "fill_blank": "MySQL填空题",
            "short_answer": "MySQL简答题",
            "programming": "MySQL编程题"
        }
        self.topics = [
            "Basic Commands",
            "Database Design",
            "Table Operations",
            "Data Manipulation",
            "Query Statements",
            "Index Optimization",
            "Transaction Management",
            "Stored Procedures",
            "Triggers",
            "Views",
            "User Management",
            "Backup and Recovery",
            "Performance Optimization"
        ]
        
        # 预定义的题目模板
        self.question_templates = {
            "multiple_choice": {
                "Basic Commands": [
                    {
                        "content": "Which MySQL command is used to create a new database?",
                        "options": [
                            "A) CREATE DATABASE dbname;",
                            "B) NEW DATABASE dbname;",
                            "C) MAKE DATABASE dbname;",
                            "D) GENERATE DATABASE dbname;"
                        ],
                        "correct_answer": "A",
                        "explanation": "CREATE DATABASE is the standard SQL command for creating a new database in MySQL.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/create-database.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "Which command is used to show all databases in MySQL?",
                        "options": [
                            "A) SHOW DATABASES;",
                            "B) LIST DATABASES;",
                            "C) DISPLAY DATABASES;",
                            "D) SELECT DATABASES;"
                        ],
                        "correct_answer": "A",
                        "explanation": "SHOW DATABASES is the correct command to list all databases in MySQL.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/show-databases.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Database Design": [
                    {
                        "content": "Which of the following is the best practice for designing a primary key?",
                        "options": [
                            "A) Use a VARCHAR column with business data",
                            "B) Use an AUTO_INCREMENT integer column",
                            "C) Use multiple columns combining business data",
                            "D) Use timestamp as primary key"
                        ],
                        "correct_answer": "B",
                        "explanation": "Using an AUTO_INCREMENT integer column as primary key provides the best performance and simplicity.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/primary-key-optimization.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What is the recommended practice for storing dates in MySQL?",
                        "options": [
                            "A) Use VARCHAR and store as string",
                            "B) Use INT and store as timestamp",
                            "C) Use DATETIME for full date and time",
                            "D) Use TEXT for maximum flexibility"
                        ],
                        "correct_answer": "C",
                        "explanation": "DATETIME is the recommended type for storing dates as it provides built-in date handling and validation.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/datetime.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Index Optimization": [
                    {
                        "content": "What is the most efficient index type for exact value lookups?",
                        "options": [
                            "A) BTREE index",
                            "B) HASH index",
                            "C) FULLTEXT index",
                            "D) SPATIAL index"
                        ],
                        "correct_answer": "A",
                        "explanation": "BTREE indexes are most efficient for exact value lookups and range queries in MySQL.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/index-btree-hash.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "When should you consider adding an index to a column?",
                        "options": [
                            "A) On every column for maximum performance",
                            "B) Only on columns used in WHERE, JOIN, or ORDER BY",
                            "C) Only on primary key columns",
                            "D) On all foreign key columns regardless of usage"
                        ],
                        "correct_answer": "B",
                        "explanation": "Indexes should be added to columns used in WHERE, JOIN, or ORDER BY clauses for optimal query performance.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/optimization-indexes.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Query Statements": [
                    {
                        "content": "Which JOIN type returns all records from both tables when there is a match?",
                        "options": [
                            "A) INNER JOIN",
                            "B) LEFT JOIN",
                            "C) RIGHT JOIN",
                            "D) FULL JOIN"
                        ],
                        "correct_answer": "A",
                        "explanation": "INNER JOIN returns only the matching records from both tables.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/join.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "Which clause is used to filter groups in a GROUP BY query?",
                        "options": [
                            "A) WHERE",
                            "B) HAVING",
                            "C) FILTER",
                            "D) GROUP FILTER"
                        ],
                        "correct_answer": "B",
                        "explanation": "HAVING clause is used to filter groups after GROUP BY aggregation.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/group-by-modifiers.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Transaction Management": [
                    {
                        "content": "Which statement is used to permanently save transaction changes?",
                        "options": [
                            "A) SAVE",
                            "B) COMMIT",
                            "C) PERSIST",
                            "D) SAVE CHANGES"
                        ],
                        "correct_answer": "B",
                        "explanation": "COMMIT permanently saves all changes made in the current transaction.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/commit.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What is the default transaction isolation level in MySQL?",
                        "options": [
                            "A) READ UNCOMMITTED",
                            "B) READ COMMITTED",
                            "C) REPEATABLE READ",
                            "D) SERIALIZABLE"
                        ],
                        "correct_answer": "C",
                        "explanation": "REPEATABLE READ is the default isolation level in MySQL InnoDB.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/innodb-transaction-isolation-levels.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Performance Optimization": [
                    {
                        "content": "Which of the following helps improve query performance?",
                        "options": [
                            "A) Using SELECT * in all queries",
                            "B) Selecting only needed columns",
                            "C) Always using subqueries",
                            "D) Avoiding indexes"
                        ],
                        "correct_answer": "B",
                        "explanation": "Selecting only needed columns reduces I/O and memory usage, improving query performance.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/optimization-indexes.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What is the recommended way to optimize a slow query?",
                        "options": [
                            "A) Add indexes to all columns",
                            "B) Use EXPLAIN to analyze query execution plan",
                            "C) Always use FORCE INDEX",
                            "D) Increase server memory"
                        ],
                        "correct_answer": "B",
                        "explanation": "EXPLAIN helps understand query execution plan and identify optimization opportunities.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/using-explain.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Table Operations": [
                    {
                        "content": "Which command is used to modify an existing table structure?",
                        "options": [
                            "A) MODIFY TABLE",
                            "B) CHANGE TABLE",
                            "C) ALTER TABLE",
                            "D) UPDATE TABLE"
                        ],
                        "correct_answer": "C",
                        "explanation": "ALTER TABLE is used to modify the structure of an existing table.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/alter-table.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What happens to the data when you TRUNCATE a table?",
                        "options": [
                            "A) Data is backed up automatically",
                            "B) Data is deleted but can be rolled back",
                            "C) Data is permanently deleted and auto-increment is reset",
                            "D) Only some rows are deleted"
                        ],
                        "correct_answer": "C",
                        "explanation": "TRUNCATE permanently removes all data and resets auto-increment counters.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/truncate-table.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Data Manipulation": [
                    {
                        "content": "Which statement is used to modify existing records in a table?",
                        "options": [
                            "A) MODIFY",
                            "B) CHANGE",
                            "C) ALTER",
                            "D) UPDATE"
                        ],
                        "correct_answer": "D",
                        "explanation": "UPDATE statement is used to modify existing records in a table.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/update.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What is the correct way to insert multiple rows in a single query?",
                        "options": [
                            "A) Multiple INSERT statements",
                            "B) INSERT ... VALUES (...), (...), (...)",
                            "C) INSERT MULTIPLE VALUES",
                            "D) MULTI INSERT statement"
                        ],
                        "correct_answer": "B",
                        "explanation": "Using multiple value lists with INSERT is the most efficient way to insert multiple rows.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/insert.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Stored Procedures": [
                    {
                        "content": "What is the correct syntax to create a stored procedure?",
                        "options": [
                            "A) CREATE PROCEDURE name() SELECT * FROM table",
                            "B) CREATE PROCEDURE name() BEGIN SELECT * FROM table; END",
                            "C) MAKE PROCEDURE name() SELECT * FROM table",
                            "D) NEW PROCEDURE name() BEGIN SELECT * FROM table; END"
                        ],
                        "correct_answer": "B",
                        "explanation": "CREATE PROCEDURE with BEGIN...END block is the correct syntax.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/create-procedure.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "How do you call a stored procedure?",
                        "options": [
                            "A) EXECUTE procedure_name",
                            "B) CALL procedure_name",
                            "C) RUN procedure_name",
                            "D) START procedure_name"
                        ],
                        "correct_answer": "B",
                        "explanation": "CALL is the correct command to execute a stored procedure.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/call.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Triggers": [
                    {
                        "content": "When can a trigger be executed?",
                        "options": [
                            "A) Only after INSERT",
                            "B) Only before DELETE",
                            "C) Before or after INSERT, UPDATE, or DELETE",
                            "D) Only during UPDATE"
                        ],
                        "correct_answer": "C",
                        "explanation": "Triggers can be executed before or after INSERT, UPDATE, or DELETE operations.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/trigger-syntax.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What are OLD and NEW references in triggers?",
                        "options": [
                            "A) They refer to backup tables",
                            "B) They refer to the previous and new values of columns",
                            "C) They are optional parameters",
                            "D) They refer to different databases"
                        ],
                        "correct_answer": "B",
                        "explanation": "OLD refers to the values before the change, NEW refers to the values after the change.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/trigger-syntax.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Views": [
                    {
                        "content": "What is a view in MySQL?",
                        "options": [
                            "A) A physical copy of a table",
                            "B) A stored query that acts like a virtual table",
                            "C) A backup of a table",
                            "D) A temporary table"
                        ],
                        "correct_answer": "B",
                        "explanation": "A view is a stored query that can be treated as if it were a table.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/views.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What is an updatable view?",
                        "options": [
                            "A) A view that can be modified using triggers",
                            "B) A view that allows INSERT, UPDATE, and DELETE operations",
                            "C) A view that updates automatically",
                            "D) A view that requires manual refresh"
                        ],
                        "correct_answer": "B",
                        "explanation": "An updatable view allows modifications to the underlying tables through the view.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/view-updatability.html",
                        "version_info": "MySQL 5.7+"
                    }
                ],
                "Backup and Recovery": [
                    {
                        "content": "Which tool is commonly used for logical backups in MySQL?",
                        "options": [
                            "A) mysqlbackup",
                            "B) mysqldump",
                            "C) backup",
                            "D) dbbackup"
                        ],
                        "correct_answer": "B",
                        "explanation": "mysqldump is the standard tool for creating logical backups in MySQL.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html",
                        "version_info": "MySQL 5.7+"
                    },
                    {
                        "content": "What is the advantage of using binary log backups?",
                        "options": [
                            "A) They are easier to create",
                            "B) They allow point-in-time recovery",
                            "C) They take less space",
                            "D) They are faster to restore"
                        ],
                        "correct_answer": "B",
                        "explanation": "Binary logs enable point-in-time recovery by recording all changes to the database.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/binary-log.html",
                        "version_info": "MySQL 5.7+"
                    }
                ]
            },
            "true_false": {
                "Basic Commands": [
                    {
                        "content": "The CREATE DATABASE command is used to create a new database in MySQL.",
                        "correct_answer": True,
                        "explanation": "CREATE DATABASE is indeed the correct command to create a new database in MySQL.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/create-database.html"
                    },
                    {
                        "content": "The SHOW TABLES command will display all databases in MySQL.",
                        "correct_answer": False,
                        "explanation": "SHOW TABLES shows tables in the current database, not databases. Use SHOW DATABASES to list all databases.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/show-tables.html"
                    }
                ],
                "Database Design": [
                    {
                        "content": "Using VARCHAR as a primary key is considered best practice in MySQL.",
                        "correct_answer": False,
                        "explanation": "Using an AUTO_INCREMENT integer column is the best practice for primary keys, not VARCHAR.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/primary-key-optimization.html"
                    },
                    {
                        "content": "DATETIME is the recommended data type for storing full date and time values in MySQL.",
                        "correct_answer": True,
                        "explanation": "DATETIME is indeed recommended for storing dates as it provides built-in date handling and validation.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/datetime.html"
                    }
                ]
            },
            "fill_blank": {
                "Basic Commands": [
                    {
                        "content": "To create a new database in MySQL, use the command: _____ DATABASE database_name;",
                        "correct_answer": "CREATE",
                        "explanation": "CREATE DATABASE is the standard SQL command for creating a new database.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/create-database.html"
                    },
                    {
                        "content": "To list all databases in MySQL, use the command: _____ DATABASES;",
                        "correct_answer": "SHOW",
                        "explanation": "SHOW DATABASES is the command to list all databases in MySQL.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/show-databases.html"
                    }
                ],
                "Table Operations": [
                    {
                        "content": "To modify an existing table structure, use the _____ TABLE command.",
                        "correct_answer": "ALTER",
                        "explanation": "ALTER TABLE is used to modify the structure of an existing table.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/alter-table.html"
                    }
                ],
                "Query Statements": [
                    {
                        "content": "To filter groups in a GROUP BY query, use the _____ clause.",
                        "correct_answer": "HAVING",
                        "explanation": "HAVING clause is used to filter groups after GROUP BY aggregation.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/group-by-modifiers.html"
                    },
                    {
                        "content": "To join two tables and return only matching records, use _____ JOIN.",
                        "correct_answer": "INNER",
                        "explanation": "INNER JOIN returns only the records that have matches in both tables.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/join.html"
                    }
                ],
                "Transaction Management": [
                    {
                        "content": "To permanently save transaction changes, use the _____ command.",
                        "correct_answer": "COMMIT",
                        "explanation": "COMMIT permanently saves all changes made in the current transaction.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/commit.html"
                    },
                    {
                        "content": "To undo transaction changes before commit, use _____.",
                        "correct_answer": "ROLLBACK",
                        "explanation": "ROLLBACK undoes all changes made in the current transaction.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/commit.html"
                    }
                ],
                "Index Optimization": [
                    {
                        "content": "The most efficient index type for exact value lookups is _____ index.",
                        "correct_answer": "BTREE",
                        "explanation": "BTREE indexes are most efficient for exact value lookups and range queries.",
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/index-btree-hash.html"
                    }
                ]
            },
            "short_answer": {
                "Basic Commands": [
                    {
                        "content": "Explain the difference between DROP DATABASE and DROP TABLE commands in MySQL.",
                        "model_answer": "DROP DATABASE permanently deletes an entire database including all its tables and data. DROP TABLE only deletes a specific table from the current database. Both commands cannot be rolled back without a backup.",
                        "key_points": [
                            "DROP DATABASE deletes entire database",
                            "DROP TABLE deletes specific table",
                            "Both are permanent operations",
                            "Cannot be rolled back without backup"
                        ],
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/drop-database.html"
                    },
                    {
                        "content": "What is the purpose of the USE command in MySQL?",
                        "model_answer": "The USE command is used to select a specific database as the default (current) database for subsequent operations. All unqualified table references will be interpreted as belonging to this database.",
                        "key_points": [
                            "Selects default database",
                            "Affects subsequent operations",
                            "Applies to unqualified table references"
                        ],
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/use.html"
                    }
                ],
                "Query Statements": [
                    {
                        "content": "Explain the difference between WHERE and HAVING clauses in MySQL.",
                        "model_answer": "WHERE filters individual rows before grouping, while HAVING filters groups after GROUP BY aggregation. WHERE can't use aggregate functions, but HAVING can. WHERE is processed before GROUP BY, HAVING is processed after.",
                        "key_points": [
                            "WHERE filters rows before grouping",
                            "HAVING filters groups after grouping",
                            "WHERE can't use aggregates",
                            "HAVING can use aggregates",
                            "Different processing order"
                        ],
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/group-by-handling.html"
                    }
                ],
                "Transaction Management": [
                    {
                        "content": "Explain the ACID properties in MySQL transactions.",
                        "model_answer": "ACID stands for Atomicity (transactions are all-or-nothing), Consistency (database remains valid after transaction), Isolation (transactions are independent), and Durability (committed changes are permanent). These properties ensure reliable transaction processing.",
                        "key_points": [
                            "Atomicity - all or nothing",
                            "Consistency - database validity",
                            "Isolation - transaction independence",
                            "Durability - permanent changes"
                        ],
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/mysql-acid.html"
                    }
                ],
                "Performance Optimization": [
                    {
                        "content": "Describe three ways to optimize MySQL query performance.",
                        "model_answer": "1. Use appropriate indexes on columns used in WHERE, JOIN, and ORDER BY clauses. 2. Select only needed columns instead of using SELECT *. 3. Use EXPLAIN to analyze and optimize query execution plans. Additional optimizations include proper table design, avoiding subqueries when possible, and using connection pooling.",
                        "key_points": [
                            "Use appropriate indexes",
                            "Select specific columns",
                            "Use EXPLAIN for analysis",
                            "Proper table design",
                            "Avoid subqueries",
                            "Use connection pooling"
                        ],
                        "doc_reference": "https://dev.mysql.com/doc/refman/8.0/en/optimization-indexes.html"
                    }
                ]
            },
            "programming": {
                "Basic Operations": [
                    {
                        "content": "Write a MySQL script to create a database named 'library' and create a table named 'books' with the following columns: id (auto-increment primary key), title (varchar), author (varchar), publication_year (year), and isbn (varchar).",
                        "solution": """
CREATE DATABASE library;
USE library;
CREATE TABLE books (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publication_year YEAR,
    isbn VARCHAR(13)
);""",
                        "test_cases": [
                            "SHOW DATABASES LIKE 'library';",
                            "USE library;",
                            "SHOW TABLES LIKE 'books';",
                            "DESCRIBE books;"
                        ],
                        "hints": [
                            "Start with CREATE DATABASE",
                            "Don't forget to USE the database",
                            "Use appropriate data types",
                            "Consider constraints like NOT NULL"
                        ]
                    }
                ],
                "Data Manipulation": [
                    {
                        "content": "Write a MySQL script to insert sample data into the books table and then write a query to find all books published after 2000.",
                        "solution": """
INSERT INTO books (title, author, publication_year, isbn)
VALUES 
('MySQL Guide', 'John Doe', 2020, '1234567890123'),
('Database Design', 'Jane Smith', 1999, '9876543210987'),
('SQL Basics', 'Bob Wilson', 2015, '4567890123456');

SELECT * FROM books WHERE publication_year > 2000;""",
                        "test_cases": [
                            "SELECT COUNT(*) FROM books;",
                            "SELECT * FROM books WHERE publication_year > 2000;"
                        ],
                        "hints": [
                            "Use INSERT INTO for adding data",
                            "Specify columns in INSERT",
                            "Use WHERE for filtering"
                        ]
                    }
                ],
                "Query Optimization": [
                    {
                        "content": "Write a MySQL script to create an index on the author column of the books table and then write a query to demonstrate its use.",
                        "solution": """
CREATE INDEX idx_author ON books(author);
EXPLAIN SELECT * FROM books WHERE author = 'John Doe';""",
                        "test_cases": [
                            "SHOW INDEX FROM books;",
                            "EXPLAIN SELECT * FROM books WHERE author = 'John Doe';"
                        ],
                        "hints": [
                            "Use CREATE INDEX syntax",
                            "Index name should be meaningful",
                            "Use EXPLAIN to verify index usage"
                        ]
                    }
                ],
                "Stored Procedures": [
                    {
                        "content": "Write a stored procedure that accepts a year parameter and returns all books published in that year.",
                        "solution": """
DELIMITER //
CREATE PROCEDURE get_books_by_year(IN pub_year YEAR)
BEGIN
    SELECT * FROM books WHERE publication_year = pub_year;
END //
DELIMITER ;

CALL get_books_by_year(2020);""",
                        "test_cases": [
                            "SHOW PROCEDURE STATUS WHERE Db = 'library';",
                            "CALL get_books_by_year(2020);"
                        ],
                        "hints": [
                            "Use DELIMITER to change statement delimiter",
                            "Define input parameter with IN keyword",
                            "Don't forget to change delimiter back"
                        ]
                    }
                ]
            }
        }
        
    def get_question_template(self, question_type: str, topic: str = None) -> Dict:
        """获取题目模板"""
        if question_type not in self.question_templates:
            raise ValueError(f"未知的题目类型: {question_type}")
        
        templates = self.question_templates[question_type]
        if topic is None:
            # 随机选择一个主题
            topic = random.choice(list(templates.keys()))
        elif topic not in templates:
            raise ValueError(f"未知的主题: {topic}")
        
        # 从选定主题中随机选择一个模板
        return random.choice(templates[topic])

    def insert_question(self, question_type: str, template: Dict) -> bool:
        """插入题目到数据库"""
        try:
            # 获取题目类型ID
            db_type_name = self.type_mapping.get(question_type)
            if not db_type_name:
                raise ValueError(f"未知的题目类型: {question_type}")
                
            type_id = self.db_manager.fetch_one(
                "SELECT type_id FROM question_types WHERE type_name = %s",
                (db_type_name,)
            )
            if not type_id:
                raise ValueError(f"未找到题目类型: {db_type_name}")
            type_id = type_id['type_id']

            # 随机选择难度级别
            difficulty_level = self.db_manager.fetch_one(
                "SELECT level_id FROM difficulty_levels ORDER BY RAND() LIMIT 1"
            )
            difficulty_id = difficulty_level['level_id']

            # 插入题目
            question_id = self.db_manager.insert(
                "INSERT INTO questions (type_id, difficulty_level, content) VALUES (%s, %s, %s)",
                (type_id, difficulty_id, template["content"])
            )
            
            if question_id is None:
                raise ValueError("插入题目失败：无法获取question_id")

            # 根据题目类型处理选项和答案
            if question_type == "multiple_choice":
                # 处理选择题选项
                for option in template["options"]:
                    is_correct = option.startswith(template["correct_answer"] + ")")
                    self.db_manager.insert(
                        "INSERT INTO multiple_choice_options (question_id, option_content, is_correct) VALUES (%s, %s, %s)",
                        (question_id, option, is_correct)
                    )
            elif question_type == "true_false":
                # 处理判断题答案
                self.db_manager.insert(
                    "INSERT INTO answers (question_id, answer_content, explanation) VALUES (%s, %s, %s)",
                    (question_id, str(template["correct_answer"]), template["explanation"])
                )
            elif question_type == "fill_blank":
                # 处理填空题答案
                self.db_manager.insert(
                    "INSERT INTO answers (question_id, answer_content, explanation) VALUES (%s, %s, %s)",
                    (question_id, template["correct_answer"], template["explanation"])
                )
            elif question_type == "short_answer":
                # 处理简答题答案
                self.db_manager.insert(
                    "INSERT INTO answers (question_id, answer_content, explanation) VALUES (%s, %s, %s)",
                    (question_id, template["model_answer"], json.dumps(template["key_points"]))
                )
            elif question_type == "programming":
                # 处理编程题答案和测试用例
                self.db_manager.insert(
                    "INSERT INTO answers (question_id, answer_content, explanation) VALUES (%s, %s, %s)",
                    (question_id, template["solution"], json.dumps({
                        "test_cases": template["test_cases"],
                        "hints": template["hints"]
                    }))
                )
            
            return True
        except Exception as e:
            logger.error(f"题目生成失败: {str(e)}")
            return False

    def generate_questions(self, question_type: str, count: int) -> Tuple[int, int]:
        """生成指定数量的题目"""
        success_count = 0
        failure_count = 0
        
        logger.info(f"开始生成{question_type}题目，目标数量：{count}")
        
        for i in range(1, count + 1):
            try:
                template = self.get_question_template(question_type)
                if self.insert_question(question_type, template):
                    success_count += 1
                    logger.info(f"成功生成第 {success_count} 道{question_type}题目")
                else:
                    failure_count += 1
                    logger.error(f"第 {i} 道{question_type}题目生成失败")
                
                if i % 10 == 0:
                    logger.info(f"{question_type}进度: {i}/{count}, 成功: {success_count}, 失败: {failure_count}")
            
            except Exception as e:
                failure_count += 1
                logger.error(f"第 {i} 道{question_type}题目生成失败")
        
        logger.info(f"{question_type}题目生成完成. 成功: {success_count}, 失败: {failure_count}")
        return success_count, failure_count

def main():
    generator = QuestionGenerator()
    total_success = 0
    total_failure = 0

    # 生成不同类型的题目
    question_counts = {
        "multiple_choice": 500,
        "true_false": 400,
        "fill_blank": 300,
        "short_answer": 200,
        "programming": 100
    }

    for q_type, count in question_counts.items():
        success, failure = generator.generate_questions(q_type, count)
        total_success += success
        total_failure += failure

    logger.info(f"所有题目生成完成. 总成功: {total_success}, 总失败: {total_failure}")

if __name__ == "__main__":
    main() 