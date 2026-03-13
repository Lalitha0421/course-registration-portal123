from config import get_connection


def get_user_by_login(login_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, login_id, password_hash, role
        FROM users
        WHERE login_id = :login_id
    """, login_id=login_id)

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return user