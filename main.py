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

def createProfessionsTable():
    mycursor.execute("CREATE TABLE `professions` (`id` INT NOT NULL, `name` VARCHAR(45) NOT NULL, PRIMARY KEY (`id`))")


def populateProfessionsTable():
    sqlAddProfession = "INSERT INTO `professions` (`id`, `name`) VALUES (%s, %s)"
    mycursor.executemany(sqlAddProfession, apiGetProfessions())
    print("Committing to db...")
    mydb.commit()
    

# def apiGetProfessions():
#     apiProfessions = {}
#     print("Getting professions from the blizzard api...")
#     request = 'https://us.api.blizzard.com/data/wow/profession/index?namespace=static-us'
#     response = requests.get(request, headers=headers)
#     jsonResponse = response.json().get('professions')
#     for profession in jsonResponse:
#         # print("Populating the dictionary")
#         apiProfessions[profession["id"]] = profession["name"]["en_US"]
#     print("Obtained the professions...")
#     return apiProfessions

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

populateProfessionsTable()
