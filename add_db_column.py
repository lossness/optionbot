import sqlite3
import os

DEFAULT_PATH = os.path.join(os.path.dirname(__file__), 'database.sqlite3')


def db_connect(db_path=DEFAULT_PATH):
    con = sqlite3.connect(db_path)
    return con


con = db_connect()
cur = con.cursor()

addColumn = "ALTER TABLE trades ADD COLUMN time TEXT"

cur.execute(addColumn)

# Add a new column to teacher table

addColumn = "ALTER TABLE error_trades ADD COLUMN time TEXT"

cur.execute(addColumn)

# Retrieve the SQL statment for the tables and check the schema

masterQuery = "select * from sqlite_master"

cur.execute(masterQuery)

tableList = cur.fetchall()

for table in tableList:

    print("Database Object Type: %s" % (table[0]))

    print("Database Object Name: %s" % (table[1]))

    print("Table Name: %s" % (table[2]))

    print("Root page: %s" % (table[3]))

    print("**SQL Statement**: %s" % (table[4]))

# close the database connection
if (con):
    con.close()