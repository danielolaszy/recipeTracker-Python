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


def dropTable(table):
    dropTable = "DROP TABLE IF EXISTS " + table
    print("Executing '" + dropTable + "'")
    mycursor.execute(dropTable)
    print("Dropping " + table + " table...")
    mydb.commit()

def fetchTable(table):
    fetchTable = "SELECT * FROM " + table
    print("Executing '" + fetchTable + "'")
    mycursor.execute(fetchTable)
    myResult = mycursor.fetchall()
    return myResult



def professionsTable():
    dropTable("professions")
    print("Creating professions table...")
    mycursor.execute("CREATE TABLE `professions` (`id` INT NOT NULL, `name` VARCHAR(45) NOT NULL, PRIMARY KEY (`id`))")
    sqlAddProfession = "INSERT INTO `professions` (`id`, `name`) VALUES (%s, %s)"
    sqlDeleteProfessions = "DELETE FROM `professions` WHERE id IN (794, 2777, 2787, 2791, 2811)"
    print("Executing mysql queries...")
    mycursor.executemany(sqlAddProfession, apiGetProfessions())
    mycursor.execute(sqlDeleteProfessions)
    print("Committing professions to db...")
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


def skillTierTable():
    dropTable("skill_tier")
    print("Creating skill_tier table...")
    mycursor.execute("CREATE TABLE `skill_tier` (`id` INT NOT NULL, `name` VARCHAR(255) NOT NULL, `profession_id` INT NULL, PRIMARY KEY (`id`), INDEX `profession_id_idx` (`profession_id` ASC) VISIBLE, CONSTRAINT `profession_id` FOREIGN KEY (`profession_id`) REFERENCES `professions` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION)")
    sqlAddSkillTiers= "INSERT INTO `skill_tier` (`id`, `name`, `profession_id`) VALUES (%s, %s, %s)"
    mycursor.executemany(sqlAddSkillTiers, apiGetSkillTiers())
    print("Committing skill_tiers to db...")
    mydb.commit()

def apiGetSkillTiers():
    fetchProfessionIds = "SELECT id FROM professions"
    mycursor.execute(fetchProfessionIds)
    myResult = mycursor.fetchall()
    apiSkillTiers = []
    for id in myResult:
        id = str(id).replace("(","").replace(")","").replace(",","")
        print("Getting skill tiers for profession "+id+" from the blizzard api...")
        request = 'https://us.api.blizzard.com/data/wow/profession/'+ id +'?namespace=static-us'
        response = requests.get(request, headers=headers)
        skillTiers = response.json().get("skill_tiers")
        professionId = response.json().get("id")
        for tier in skillTiers:
            print("Appending " + str(tier["name"]["en_US"]) + " to the list...")
            apiSkillTiers.append(tuple((tier["id"], tier["name"]["en_US"], professionId)))
    print("Obtained skill tiers for all professions in db...")
    return apiSkillTiers


def recipesTable():
    dropTable("recipes")
    print("Creating recipes table...")
    mycursor.execute("CREATE TABLE `recipes` ( `id` INT NOT NULL, `name` VARCHAR(255) NULL, `skill_tier_id` INT NOT NULL, PRIMARY KEY (`id`), INDEX `skill_tier_id_idx` (`skill_tier_id` ASC) VISIBLE, CONSTRAINT `skill_tier_id` FOREIGN KEY (`skill_tier_id`) REFERENCES `skill_tier` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION)")



    # sqlAddSkillTiers= "INSERT INTO `skill_tier` (`id`, `name`, `profession_id`) VALUES (%s, %s, %s)"
    # mycursor.executemany(sqlAddSkillTiers, apiGetSkillTiers())
    print("Committing recipes to db...")
    mydb.commit()

recipesTable()