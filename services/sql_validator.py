# VALIDATE GENERATED SQL

def validate_sql_query(query):

    upper_query = query.upper()

    blocked_keywords = [
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "TRUNCATE",
        "CREATE"
    ]

    for keyword in blocked_keywords:

        if keyword in upper_query:
            return False, f"Blocked keyword detected: {keyword}"

    if not upper_query.strip().startswith("SELECT"):
        return False, "Only SELECT queries are allowed"

    return True, "SQL query is valid"