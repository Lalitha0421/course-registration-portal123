import oracledb

def get_connection():
    connection = oracledb.connect(
        user="LALITHA",
        password="MyNewPassword123",
        dsn="localhost:1521/XEPDB1"
    )
    return connection


import oracledb

