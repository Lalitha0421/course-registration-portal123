import oracledb

# Create connection
connection = oracledb.connect(
    user="LALITHA",
    password="MyNewPassword123",
    dsn="localhost:1521/XEPDB1"
)

# Create cursor
cursor = connection.cursor()

# Test query
cursor.execute("SELECT table_name FROM user_tables")

# Print tables
for table in cursor:
    print(table[0])

# Close connection
cursor.close()
connection.close()