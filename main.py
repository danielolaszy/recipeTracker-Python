# from re import I
from dotenv import load_dotenv
load_dotenv()
from requests.exceptions import HTTPError
import requests  # pip install requests
import os
import shutil
from pathlib import Path
import mysql.connector

import datetime
startTime = datetime.datetime.now()

mydb = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)
mycursor = mydb.cursor()
headers = {'Authorization': 'Bearer ' + os.getenv('API_ACCESS_TOKEN')}

def dropDatabase(db):
    dropDatabase = "DROP DATABASE IF EXISTS " + db
    print("Executing '" + dropDatabase + "'")
    mycursor.execute(dropDatabase)
    print("Dropping " + db + "...")
    mydb.commit()

def createDatabase(db):
    createDatabase = "CREATE SCHEMA " + db + ";"
    print("Executing '" + createDatabase + "'")
    mycursor.execute(createDatabase)
    print("Creating " + db + " database...")
    mydb.commit()

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

def createTable(sqlQuery):
    print("Creating table...")
    mycursor.execute(sqlQuery)
    mydb.commit()
    print("Table has been created!")

def main():
    # sql queries to pass into the createTable function
    tableProfessions = """CREATE TABLE Professions (
                            ProfessionId int NOT NULL,
                            ProfessionName varchar(255) NOT NULL,
                            PRIMARY KEY (ProfessionId)
                            );
                            """
    tableSkillTiers = """CREATE TABLE SkillTiers (
                            SkillTierId int NOT NULL,
                            SkillTierName varchar(255) NOT NULL,
                            ProfessionId int NOT NULL,
                            PRIMARY KEY (SkillTierId),
                            FOREIGN KEY (ProfessionId) REFERENCES Professions(ProfessionId)
                            );
                            """
    tableRecipes = """CREATE TABLE Recipes (
                        RecipeId int NOT NULL,
                        RecipeName varchar(255) NOT NULL,
                        RecipeIcon varchar(255) DEFAULT NULL,
                        SkillTierId int NOT NULL,
                        PRIMARY KEY (RecipeId),
                        FOREIGN KEY (SkillTierId) REFERENCES SkillTiers(SkillTierId)
                        );
                        """
    # Dropping tables if exist
    tables = ["Recipes", "SkillTiers", "Professions"]
    for table in tables: 
        dropTable(table)

    # Creating tables
    createTable(tableProfessions)
    createTable(tableSkillTiers)
    createTable(tableRecipes)

    # Populating tables
    apiGetProfessions()
    apiGetSkillTiers()
    apiGetRecipes()
    apiGetRecipeIcons()


def apiGetProfessions():
    print("Getting professions from the blizzard api...")
    request = 'https://us.api.blizzard.com/data/wow/profession/index?namespace=static-us&locale=en_US'
    response = requests.get(request, headers=headers)
    jsonResponse = response.json().get('professions')
    for profession in jsonResponse:
        mycursor.execute("INSERT INTO Professions (ProfessionId, ProfessionName) VALUES (%s, %s)",tuple((profession["id"], profession["name"])))
    mycursor.execute("DELETE FROM Professions WHERE ProfessionId IN (794, 2777, 2787, 2791, 2811)")
    mydb.commit()
    print("Found all professions...")

def apiGetSkillTiers():
    fetchProfessionIds = "SELECT ProfessionId FROM Professions"
    mycursor.execute(fetchProfessionIds)
    table = mycursor.fetchall()

    for row in table:
        print("Getting skill tiers for profession " + str(row[0]) + " from the blizzard api...")
        request = 'https://us.api.blizzard.com/data/wow/profession/'+ str(row[0]) +'?namespace=static-us&locale=en_US'
        response = requests.get(request, headers=headers)
        skillTiers = response.json().get("skill_tiers")
        professionId = response.json().get("id")
        for tier in skillTiers:
            print("Found " + str(tier["name"]))
            mycursor.execute("INSERT INTO SkillTiers (SkillTierId, SkillTierName, ProfessionId) VALUES (%s, %s, %s)",tuple((tier["id"], tier["name"], professionId)))
            mydb.commit() 
    print("Obtained skill tiers for all professions in db...")

def apiGetRecipes():
    fetchProfessionIds = "SELECT ProfessionId, SkillTierId, SkillTierName  FROM SkillTiers"
    mycursor.execute(fetchProfessionIds)
    table = mycursor.fetchall()

    for row in table:

            request = 'https://us.api.blizzard.com/data/wow/profession/' + str(row[0]) + '/skill-tier/' + str(row[1]) + '?namespace=static-us&locale=en_US'
            response = requests.get(request, headers=headers)

            skillTierId = response.json().get('id')
            categories = response.json().get('categories')
            professionTierName = response.json().get('name')

            professionRecipeNumber = 0
            if categories is not None:
                for category in categories:
                    recipes = category["recipes"]
                    professionRecipeNumber += len(recipes)
                    for recipe in recipes:
                        print("Found " + str(recipe["name"]) + ":" + str(recipe["id"]))
                        mycursor.execute("INSERT INTO Recipes (RecipeId, RecipeName, SkillTierId) VALUES (%s, %s, %s)",tuple((recipe["id"], recipe["name"], skillTierId)))
                        mydb.commit() 
                print("\033[1m" + "Found " + str(professionRecipeNumber) + " recipes for " + str(professionTierName) + "!\n" + "\033[0m")
    print("Obtained recipes for all skill tiers for all professions in db...")

def apiGetRecipeIcons():
    mycursor.execute("SELECT RecipeId, RecipeName FROM Recipes")
    table = mycursor.fetchall()

    
    dirPath = "./icons/recipes/"
    print("Checking if '" + dirPath + "' exists...")
    if os.path.exists(dirPath):
        print("Dirctory '" + dirPath + "' found!")
        print("Deleting '" + dirPath + "'")
        shutil.rmtree(dirPath)
        print("Creating '" + dirPath + "'")
        os.makedirs(dirPath)
    else:
        print("Dirctory '" + dirPath + "not found...")
        print("Creating '" + dirPath + "'")
        os.makedirs(dirPath)
    
    for row in table[:5]:
        print("Querying Blizzard API for the RecipeIcon of " + str(row[0]))
        request = 'https://us.api.blizzard.com/data/wow/media/recipe/' + str(row[0]) + '?namespace=static-us&locale=en_US'
        response = requests.get(request, headers=headers)
        recipeIconUrl = response.json().get('assets')[0]['value']
        recipeIconFileName = recipeIconUrl[47:]

        # Committing found icon file name to the database
        print("Updating RecipeIcon column with " + recipeIconFileName + " where RecipeId is " + str(row[0]))
        mycursor.execute("update Recipes set RecipeIcon=%s where RecipeId=%s",tuple((recipeIconFileName,row[0])))
        mydb.commit() 

        #  Downloading recipe icon from the url found in the api query
        print("Downloading " + recipeIconFileName + "to path " + dirPath)
        recipeIconImgData = requests.get(recipeIconUrl).content
        with open(dirPath + recipeIconFileName, "wb") as handler:
            handler.write(recipeIconImgData)

main()
print(datetime.datetime.now() - startTime)


# Trainer
# Vendor
# World Drop
# Raid Drop
# Dungeon Drop
