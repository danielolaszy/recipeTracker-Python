from dotenv import load_dotenv
load_dotenv()
import os
import mysql.connector

mydb = mysql.connector.connect(
host=os.getenv("MYSQL_HOST"),
user=os.getenv("MYSQL_USER"),
password=os.getenv("MYSQL_PASSWORD"),
)

print(mydb)  
