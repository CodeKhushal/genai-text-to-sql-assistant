import sqlite3
import os

# EXECUTE SQL QUERY

def execute_sql_query(query):

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "..", "database", "sales_database.db")
        db_path = os.path.normpath(db_path)

        connection = sqlite3.connect(db_path)

        cursor = connection.cursor()

        cursor.execute(query)

        results = cursor.fetchall()

        column_names = [description[0] for description in cursor.description]

        connection.close()

        # Handle empty results
        if not results:
            return {
                "success": True,
                "message": "No results found.",
                "data": []
            }

        # Format results
        formatted_results = []

        for row in results:

            row_dict = {}

            for index, value in enumerate(row):
                row_dict[column_names[index]] = value

            formatted_results.append(row_dict)

        return {
            "success": True,
            "message": "Query executed successfully.",
            "data": formatted_results
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e),
            "data": []
        }