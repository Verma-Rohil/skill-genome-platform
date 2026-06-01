import pymysql
import os

def init_database():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    if not os.path.exists(schema_path):
        print(f"Error: schema.sql not found at {schema_path}")
        return

    print("Connecting to MySQL...")
    # Connect without specifying database to create it first
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password="MySQL_Root_2026!",
        autocommit=True
    )

    try:
        with conn.cursor() as cursor:
            # Read schema file
            with open(schema_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Split statements by semicolon, ignoring comments and empty lines
            statements = []
            current_statement = []
            
            for line in sql_content.splitlines():
                stripped_line = line.strip()
                if not stripped_line or stripped_line.startswith("--"):
                    continue
                
                current_statement.append(line)
                if stripped_line.endswith(";"):
                    statements.append("\n".join(current_statement))
                    current_statement = []

            print(f"Parsed {len(statements)} SQL statements. Executing...")
            
            for i, stmt in enumerate(statements):
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"Error executing statement {i+1}:\n{stmt}\nError: {e}")
                    raise e
            
            print("Database and schema initialized successfully!")
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
