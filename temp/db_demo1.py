# with engine.connect() as conn:
#     result = conn.execute(text("SELECT * FROM buyer"))
    # rows = result.all()  # Store the result(all rows) in a variable rows
    # print(type(rows)) # Type of result.all()
    # print(rows) # All rows in table
    # print(rows[0]) # First row in table
    
    
    # rows1 = result.fetchall()  # Fetch all rows
    # # Get column names
    # columns = result.keys()
    # # Convert rows to a list of dictionaries
    # dict_rows = [dict(zip(columns, row)) for row in rows1]
    # print(type(dict_rows))  # Type of result.all()
    # print(dict_rows)  # All rows in table as a list of dictionaries
    # if dict_rows:
    #     print(dict_rows[0])  # First row in table as a dictionary