import sqlite3


# EXECUTE SQL QUERY

def execute_sql_query(query):

    try:
        connection = sqlite3.connect("database/sales_database.db")

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