from dotenv import load_dotenv # pip install python-dotenv
import mysql.connector # pip install mysql-connector-python
import requests  # pip install requests
import json
import os
import datetime
load_dotenv()

startTime = datetime.datetime.now() # Start timer to measure run time

# Establishing connection to mysql database
mydb = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE"),
)
mycursor = mydb.cursor()

# Headers used for Blizzard API
headers = {'Authorization': 'Bearer ' + os.getenv('API_ACCESS_TOKEN'),
            'Battlenet-Namespace': 'static-us'}

def dropDatabase(db):
    dropDatabase = "DROP DATABASE IF EXISTS " + db + ";"
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
    dropTable = "DROP TABLE IF EXISTS " + table + ";"
    print("Executing '" + dropTable + "'")
    mycursor.execute(dropTable)
    print("Dropping " + table + " table...")
    mydb.commit()
 
def fetchTable(table):
    fetchTable = "SELECT * FROM " + table + ";"
    print("Executing '" + fetchTable + "'")
    mycursor.execute(fetchTable)
    myResult = mycursor.fetchall()
    return myResult

def createTable(sqlQuery):
    print("Creating table...")
    mycursor.execute(sqlQuery)
    mydb.commit()
    print("Table has been created!")

def getLatestNonNullRow():
    fetchTable = "SELECT COUNT(*) FROM recipes WHERE RecipeIcon IS NOT NULL;"
    mycursor.execute(fetchTable)
    myResult = mycursor.fetchone()
    return myResult[0]



def mainProgram():
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
                        SourceType varchar(255) DEFAULT NULL,
                        Source varchar(255) DEFAULT NULL,
                        SourceZone varchar(255) DEFAULT NULL,
                        SourceFaction varchar(255) DEFAULT NULL,
                        SkillTierId int NOT NULL,
                        PRIMARY KEY (RecipeId),
                        FOREIGN KEY (SkillTierId) REFERENCES SkillTiers(SkillTierId)
                        );
                        """
    # Dropping tables if exist
    # tables = ["Recipes", "SkillTiers", "Professions"]
    # for table in tables: 
    #     dropTable(table)

    # # Creating tables
    # createTable(tableProfessions)
    # createTable(tableSkillTiers)
    # createTable(tableRecipes)

    # # Get initial professions from Blizzard API
    # apiGetProfessions()

    # mycursor.execute("SELECT ProfessionId FROM Professions")
    # professionsTable = mycursor.fetchall()
    # for row in professionsTable:
    #     apiGetSkillTiers(row[0])

    # mycursor.execute("SELECT ProfessionId, SkillTierId, SkillTierName FROM SkillTiers")
    # skillTiersTable = mycursor.fetchall()
    # for row in skillTiersTable:
    #     apiGetRecipes(row[0], row[1])

    # jsonGetRecipes()

    latestRow = getLatestNonNullRow()
    print(latestRow)

    # Get recipes from database
    mycursor.execute("SELECT RecipeId, RecipeName FROM Recipes") 
    recipesTable = mycursor.fetchall()
    # Get recipe from recipes
    for row in recipesTable[latestRow:]:
        apiGetRecipeIcons(row[0]) # Get recipe icon



def apiGetProfessions():
    print("Getting professions from the blizzard api...")
    request = 'https://us.api.blizzard.com/data/wow/profession/index?locale=en_US'
    response = requests.get(request, headers=headers)
    jsonResponse = response.json().get('professions')
    for profession in jsonResponse:
        mycursor.execute("INSERT INTO Professions (ProfessionId, ProfessionName) VALUES (%s, %s)",tuple((profession["id"], profession["name"])))
    mycursor.execute("DELETE FROM Professions WHERE ProfessionId IN (794, 2777, 2787, 2791, 2811)")
    mydb.commit()
    print("Found all professions...")

def apiGetSkillTiers(professionId):
    print("Getting skill tiers for profession " + str(professionId) + " from the blizzard api...")
    request = 'https://us.api.blizzard.com/data/wow/profession/'+ str(professionId) +'?locale=en_US'
    response = requests.get(request, headers=headers)
    skillTiers = response.json().get("skill_tiers")
    professionId = response.json().get("id")
    for tier in skillTiers:
        print("Found " + str(tier["name"]))
        mycursor.execute("INSERT INTO SkillTiers (SkillTierId, SkillTierName, ProfessionId) VALUES (%s, %s, %s)",tuple((tier["id"], tier["name"], professionId)))
        mydb.commit() 
    print("Obtained skill tiers for all professions in db...")

def apiGetRecipes(professionId, skillTierId):
    request = 'https://us.api.blizzard.com/data/wow/profession/' + str(professionId) + '/skill-tier/' + str(skillTierId) + '?locale=en_US'
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

def apiGetRecipeIcons(recipeId):   
    dirPath = "./icons/recipes/"
    # print("Checking if '" + dirPath + "' exists...")
    # if os.path.exists(dirPath):
    #     print("Dirctory '" + dirPath + "' found!")
    #     print("Deleting '" + dirPath + "'")
    #     shutil.rmtree(dirPath)
    #     print("Creating '" + dirPath + "'")
    #     os.makedirs(dirPath)
    # else:
    #     print("Dirctory '" + dirPath + "not found...")
    #     print("Creating '" + dirPath + "'")
    #     os.makedirs(dirPath)
    
    print("\nQuerying Blizzard API for the RecipeIcon of " + str(recipeId))
    request = 'https://us.api.blizzard.com/data/wow/media/recipe/' + str(recipeId) + '?locale=en_US'
    response = requests.get(request, headers=headers)
    recipeIconUrl = response.json().get('assets')[0]['value']
    recipeIconFileName = recipeIconUrl[47:]

    # Committing found icon file name to the database
    print("Updating RecipeIcon column with " + recipeIconFileName + " where RecipeId is " + str(recipeId))
    mycursor.execute("update Recipes set RecipeIcon=%s where RecipeId=%s",tuple((recipeIconFileName,recipeId)))
    mydb.commit() 

    #  Downloading recipe icon from the url found in the api query
    print("Downloading " + recipeIconFileName + " to path " + dirPath)
    recipeIconImgData = requests.get(recipeIconUrl).content
    with open(dirPath + recipeIconFileName, "wb") as handler:
        handler.write(recipeIconImgData)

def jsonGetRecipes():
    fileName = "recipes.json"
    print("Opening " + fileName + "...")
    recipesJson = open(fileName)
    recipes = json.load(recipesJson)
    print("Found " + str(len(recipes)) + " items in " + fileName + "!")
    for recipe in recipes:
        print("Found " + recipe["name"])
        if "id" in recipe:
            recipeId = recipe["id"]
        else:
            recipeId = None

        if "name" in recipe:
            recipeName = recipe["name"]
        else:
            recipeName = None

        if "prof" in recipe:
            recipeProf = recipe["prof"]
        else:
            recipeProf = None 

        if "icon" in recipe:
            recipeIcon = recipe["icon"]
        else:
            recipeIcon = None

        if "faction" in recipe:
            recipeFaction = recipe["faction"]
        else:
            recipeFaction = None    

        if "patch" in recipe:
            if recipe["patch"] == "1.x":
                recipeExpansion = "World of Warcraft"
            elif recipe["patch"] == "2.x":
                recipeExpansion = "The Burning Crusade"
            elif recipe["patch"] == "3.x":
                recipeExpansion = "Wrath of the Lich King"
            elif recipe["patch"] == "4.x":
                recipeExpansion = "Cataclysm"
            elif recipe["patch"] == "5.0":
                recipeExpansion = "Mists of Pandaria"
            elif recipe["patch"] == "6.x":
                recipeExpansion = "Warlords of Draenor"
            elif recipe["patch"] == "7.x":
                recipeExpansion = "Legion"
            elif recipe["patch"] == "8.x" or "8.0" or "8.1" or "8.3":
                recipeExpansion = "Battle for Azeroth"
            elif recipe["patch"] == "9.x" or "9.0" or "9.1" or "9.3":
                recipeExpansion = "Shadowlands"
        else:
            recipeExpansion = None       

        if "rarity" in recipe:
            recipeRarity = recipe["rarity"]
        else:
            recipeRarity = None    

        if "seen" in recipe:
            recipeSeen = recipe["seen"]
        else:
            recipeSeen = None

        if "sourceicon" in recipe:
            recipeSourceIcon = recipe["sourceicon"]
        else:
            recipeSourceIcon = None

        if "source" in recipe:
            recipeSource = recipe["source"]
        else:
            recipeSource = None

        if "sourcezone" in recipe:
            recipeSourceZone = recipe["sourcezone"]
        else:
            recipeSourceZone = None

        if "sourcefaction" in recipe:
            recipeSourceFaction = recipe["sourcefaction"]
        else:
            recipeSourceFaction = None

        if "sourcestanding" in recipe:
            recipeSourceStanding = recipe["sourcestanding"]
        else:
            recipeSourceStanding = None

        mycursor.execute("INSERT INTO Recipes (id, name, prof, icon, faction, expansion, rarity, seen, sourcetype, source, sourcezone, sourcefaction, sourcestanding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",tuple((recipeId, recipeName, recipeProf, recipeIcon, recipeFaction, recipeExpansion, recipeRarity, recipeSeen, recipeSourceIcon, recipeSource, recipeSourceZone, recipeSourceFaction, recipeSourceStanding)))
        mydb.commit() 

    print("Closing " + fileName + "...")
    recipesJson.close()

tableRecipes = """CREATE TABLE Recipes (
                    id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    prof VARCHAR(255) NOT NULL,
                    icon VARCHAR(255),
                    faction INT,
                    expansion VARCHAR(255),
                    rarity DECIMAL(6,5),
                    seen INT,
                    sourcetype VARCHAR(255),
                    source VARCHAR(255),
                    sourcezone VARCHAR(255),
                    sourcefaction VARCHAR(255),
                    sourcestanding VARCHAR(255),
                    PRIMARY KEY (id));
                    """

# mainProgram()
dropTable("Recipes")
createTable(tableRecipes)
jsonGetRecipes()

print(datetime.datetime.now() - startTime) # End timer to measure run time


# https://render.worldofwarcraft.com/us/icons/56/