import pyodbc

def create_trading_database():
    # Server settings
    server = '(localdb)\\MSSQLLocalDB'

    # Connection string
    conn = pyodbc.connect(
        Trusted_Connection='Yes',
        Driver='{ODBC Driver 17 for SQL Server}',
        Server=server,
        autocommit=True  # Disable multi-statement transaction
    )
    cursor = conn.cursor()

    # Check if the 'Trading Information' database exists
    db_name = 'Test For Graduation Project'
    cursor.execute("SELECT DB_ID(?)", db_name)
    db_id = cursor.fetchone()[0]

    if db_id is None:
        # Create the 'Trading Information' database
        cursor.execute(f"CREATE DATABASE [{db_name}]")
        print(f"Database '{db_name}' created.")

    # Use the 'Trading Information' database
    cursor.execute(f"USE [{db_name}]")
    print(f"Using the database '{db_name}'.")

    # Check if the specified table exists
    table_name = 'TradeInformation'
    cursor.execute(f"""
        SELECT 1
        FROM sys.tables
        WHERE name = '{table_name}'
    """)
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        # Create the specified table
        cursor.execute(f"""
            CREATE TABLE {table_name} (
                TradeID INT IDENTITY(1,1) PRIMARY KEY,
                TradeTime DATETIME,
                Symbol VARCHAR(10),
                Quantity DECIMAL(18,8),
                MoneyInvested DECIMAL(18,8),
                MoneyReturned DECIMAL(18,8),
                Wallet DECIMAL(18,8)
            )
        """)

        print(f"Table '{table_name}' has been created.")

    return cursor, conn, table_name

def the_rest_of_the_code():
    cursor, conn, table_name = create_trading_database()

    # Insert sample data into the specified table
    cursor.execute(f"""
        INSERT INTO {table_name} (TradeTime, Symbol, Quantity, MoneyInvested, MoneyReturned, Wallet)
        VALUES
            ('2023-05-20 10:30:00', 'BTCTUSD', 0.2, 6000.0, 6012.0, 10012.0), 
            ('2023-05-21 11:45:00', 'ETH', 3.0, 2000.0, 1900.0, 9900.0)
    """)

    print("Data has been inserted.")

    cursor.commit()
    # conn.close()


# Call the function to perform operations on the tables
the_rest_of_the_code()
