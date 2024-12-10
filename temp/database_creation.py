from sqlalchemy import create_engine, text

username = 'root'
password = ''
host = 'localhost'
dbname = 'cp3'

# Connection string
connect_db = f'mysql+mysqldb://{username}:{password}@{host}/{dbname}'

# Connecting
engine = create_engine(connect_db)

# SQL Insert query
insert_query = text("""
INSERT INTO buyer (name, email, password, phone) VALUES
('John Doe', 'john.doe@example.com', 'password123', '555-1234'),
('Jane Smith', 'jane.smith@example.com', 'password456', '555-5678'),
('Emily Johnson', 'emily.johnson@example.com', 'password789', '555-8765'),
('Michael Brown', 'michael.brown@example.com', 'password000', '555-4321'),
('Jessica Davis', 'jessica.davis@example.com', 'password111', '555-6789'),
('David Wilson', 'david.wilson@example.com', 'password222', '555-3456'),
('Sarah Moore', 'sarah.moore@example.com', 'password333', '555-7890'),
('Chris Taylor', 'chris.taylor@example.com', 'password444', '555-2345'),
('Laura Anderson', 'laura.anderson@example.com', 'password555', '555-5670'),
('James Thomas', 'james.thomas@example.com', 'password666', '555-8901')
""")

with engine.connect() as conn:
    # Execute the insert query
    conn.execute(insert_query)
    # Commit the transaction
    conn.execute(text("COMMIT"))
