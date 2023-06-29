#To be used in all files other than main.py
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine, inspect, MetaData, Table

engine = create_engine('sqlite:///mydatabase.db')
#creates db engine, handles the connection and communication with the database server.

Session = sessionmaker(bind=engine)
#creates a Session class, allows you to create individual session instances later to perform db ops

Base = declarative_base()
#All python classes representing db tables will inherit from the Base class

inspector = inspect(engine)

#USE THIS TO DELETE ALL TABLES(import MetaData from sqlalchemy):
"""metadata = MetaData()
metadata.reflect(bind=engine)
metadata.drop_all(bind=engine)"""

"""
USE THIS TO DELETE SELECT TABLES

conn = engine.connect()

# Create a metadata object
metadata = MetaData(bind=engine)

# Define the table you want to delete
table_name = 'Solved'
table = Table(table_name, metadata, autoload=True)

# Drop the table
table.drop()

# Commit the changes and close the connection
conn.close()"""