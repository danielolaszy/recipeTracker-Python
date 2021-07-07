from dotenv import load_dotenv
load_dotenv()
from requests.exceptions import HTTPError
import requests  # pip install requests
import os
import mysql.connector

mydb = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)
mycursor = mydb.cursor()
headers = {'Authorization': 'Bearer ' + os.getenv('API_ACCESS_TOKEN')}


def dropTables(table):
    dropTable = "DROP TABLE IF EXISTS " + table
    print("Executing '" + dropTable + "'")
    mycursor.execute(dropTable)
    print("Dropping " + table + " table...")
    mydb.commit()

def professionsTable():
    dropTables("professions")
    print("Creating professions table...")
    mycursor.execute("CREATE TABLE `professions` (`id` INT NOT NULL, `name` VARCHAR(45) NOT NULL, PRIMARY KEY (`id`))")
    sqlAddProfession = "INSERT INTO `professions` (`id`, `name`) VALUES (%s, %s)"
    sqlDeleteProfessions = "DELETE FROM `professions` WHERE id IN (2777, 2787, 2791, 2811)"
    print("Executing mysql queries...")
    mycursor.executemany(sqlAddProfession, apiGetProfessions())
    mycursor.execute(sqlDeleteProfessions)
    print("Committing to db...")
    mydb.commit()

def apiGetProfessions():
    apiProfessions = []
    print("Getting professions from the blizzard api...")
    request = 'https://us.api.blizzard.com/data/wow/profession/index?namespace=static-us'
    response = requests.get(request, headers=headers)
    jsonResponse = response.json().get('professions')
    for profession in jsonResponse:
        apiProfessions.append(tuple((profession["id"], profession["name"]["en_US"])))
    print("Obtained professions...")
    return apiProfessions

def apiGetSkillTiers():
    apiSkillTiers = []
    print("Getting professions from the blizzard api...")
    request = 'https://us.api.blizzard.com/data/wow/profession/index?namespace=static-us'
    response = requests.get(request, headers=headers)
    jsonResponse = response.json().get('professions')
    for profession in jsonResponse:
        apiProfessions.append(tuple((profession["id"], profession["name"]["en_US"])))
    print("Obtained professions...")
    return apiProfessions    

professionsTable()
