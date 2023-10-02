import os

from time import time

from sqlalchemy import create_engine
import pandas as pd

# Create a function that will create a DB connection to our postgres DB and  ingestion into it

def db_conn_ingestion(user, password, host, port, db, table_name, csv_file, execution_date):
    # Create a function that will create a DB connection to our postgres DB and  ingestion into it

    print(port, host, table_name, csv_file, execution_date)

    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")
    engine.connect()

    print("connection was made successfully ")

    start_time = time()
    df_iter = pd.read_csv(csv_file, encoding="unicode_escape", iterator=True,  chunksize=100000)


    df = next(df_iter)

    # Change the two date_time columns into actual date_time objects
    df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
    df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

    #Creates a table with certain headers only the column headers
    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    df.to_sql(name=table_name, con=engine, if_exists='append')

    end_time = time()
    print("Inserted the initial chunk into the table at about %.3f seconds" % (end_time - start_time))

    while True:

       start_time = time()

       try:
           df = next(df_iter)

           df.lpep_pickup_datetime = pd.to_datetime(df.lpep_pickup_datetime)
           df.lpep_dropoff_datetime = pd.to_datetime(df.lpep_dropoff_datetime)

           df.to_sql(name=table_name, con=engine, if_exists='append')

           end_time = time()
           print("Insertion for this chunk was successfull at complete at about %.3f seconds" % (end_time - start_time))

       except StopIteration:
           print('Loading has ended')
           break
