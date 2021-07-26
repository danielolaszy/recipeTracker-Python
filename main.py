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

def makeDir(dirPath):
    print("Checking if '" + dirPath + "' exists...")
    if os.path.exists(dirPath):
        print("Dirctory '" + dirPath + "' found!")
        print("Doing nothing.")
    else:
        print("Dirctory '" + dirPath + "not found...")
        print("Creating '" + dirPath + "'")
        os.makedirs(dirPath)

def apiGetRealms():
    regions = ["US", "EU", "KR", "TW",]
    for region in regions:
        print("Getting realms for " + region)
        request = 'https://' + region + '.api.blizzard.com/data/wow/realm/index?namespace=dynamic-' + region + '&locale=en_US'
        response = requests.get(request, headers=headers)
        realms = response.json().get("realms")
        for realm in realms:
            print("Found realm: " + realm["name"])
            realmId = realm["id"]
            realmName = realm["name"]
            realmSlug = realm["slug"]
            mycursor.execute("INSERT INTO realms (id, region, name, slug) VALUES (%s, %s, %s, %s)",tuple((realm["id"], region, realm["name"], realm["slug"])))
            mydb.commit() 

def getIcon(dirPath, fileName):
    fileExt = ".jpg"
    iconUrl = "https://render.worldofwarcraft.com/us/icons/56/" + fileName + fileExt
    print("Downloading " + fileName + fileExt + "...")
    iconImgData = requests.get(iconUrl).content
    with open(dirPath + fileName + fileExt, "wb") as handler:
        handler.write(iconImgData)
    print("Saving " + fileName + "...")

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
            recipeExpansion = recipe["patch"]
        else:
            recipeExpansion = None 

        if "unobtainable" in recipe:
            recipeUnobtainable = recipe["unobtainable"]
        else:
            recipeUnobtainable = None  

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
   

        mycursor.execute("INSERT INTO Recipes (id, name, prof, icon, faction, expansion, unobtainable, rarity, seen, sourcetype, source, sourcezone, sourcefaction, sourcestanding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",tuple((recipeId, recipeName, recipeProf, recipeIcon,recipeFaction, recipeExpansion, recipeUnobtainable, recipeRarity, recipeSeen, recipeSourceIcon, recipeSource, recipeSourceZone, recipeSourceFaction, recipeSourceStanding)))
        mydb.commit() 

    print("Closing " + fileName + "...")
    recipesJson.close()

def fixRecipes():

    sqlStatements = [
    "UPDATE `recipes` SET `expansion` = 'World of Warcraft' WHERE (`expansion` = '1.x');",
    "UPDATE `recipes` SET `expansion` = 'The Burning Crusade' WHERE (`expansion` = '2.x');",
    "UPDATE `recipes` SET `expansion` = 'Wrath of the Lich King' WHERE (`expansion` = '3.x')",
    "UPDATE `recipes` SET `expansion` = 'Cataclysm' WHERE (`expansion` = '4.x');",
    "UPDATE `recipes` SET `expansion` = 'Mists of Pandaria' WHERE (`expansion` = '5.x' OR `expansion` = '5.0');",
    "UPDATE `recipes` SET `expansion` = 'Warlords of Draenor' WHERE (`expansion` = '6.x');",
    "UPDATE `recipes` SET `expansion` = 'Legion' WHERE (`expansion` = '7.x');",
    "UPDATE `recipes` SET `expansion` = 'Battle for Azeroth' WHERE (`expansion` = '8.x' OR `expansion` = '8.0' OR `expansion` = '8.1' OR `expansion` = '8.3');",
    "UPDATE `recipes` SET `expansion` = 'Shadowlands' WHERE (`expansion` = '9.x' OR `expansion` = '9.0' OR `expansion` = '9.1' OR `expansion` = '9.3');",
    "DELETE FROM recipes WHERE expansion IS NULL;",
    "UPDATE recipes SET sourcetype = sourcezone WHERE sourcezone IS NOT NULL;", 
    "UPDATE recipes SET sourcetype = 'trainer' WHERE source  = 'Trainer';",
    "UPDATE recipes SET sourcetype = 'unobtainable' WHERE unobtainable = '1';",
    "UPDATE recipes SET sourcetype = 'unobtainable' WHERE unobtainable = '2';",
    ]

    for statement in sqlStatements:
        mycursor.execute(statement)
        mydb.commit()





def makeDb():
    # sql statement to create the table
    tableRecipes = """CREATE TABLE recipes (
                    id INT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    prof VARCHAR(255) NOT NULL,
                    icon VARCHAR(255),
                    faction INT,
                    expansion VARCHAR(255),
                    unobtainable INT,
                    rarity DECIMAL(10,7),
                    seen INT,
                    sourcetype VARCHAR(255),
                    source VARCHAR(255),
                    sourcezone VARCHAR(255),
                    sourcefaction VARCHAR(255),
                    sourcestanding VARCHAR(255),
                    PRIMARY KEY (id));
                    """

    tableRealms = """CREATE TABLE realms (
                    id INT NOT NULL,
                    region VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    slug VARCHAR(255) NOT NULL,
                    PRIMARY KEY (id));"""

    # Dropping tables if exist
    dropTable("recipes")
    dropTable("realms")

    # Creating table
    createTable(tableRecipes)
    createTable(tableRealms)

    apiGetRealms()

    # Populate recipes table from recipes.json
    jsonGetRecipes()

    # Altering table
    fixRecipes()

    # Creating directory to download icons to
    # makeDir("./icons/recipes/")

    # Getting unique icons from recipes table
    # mycursor.execute("SELECT DISTINCT icon FROM recipes")
    # recipesTable = mycursor.fetchall()
    # for row in recipesTable:
    #     getIcon("./icons/recipes/", row[0]) # Get icon for every recipe in recipesTable

makeDb()
# fixRecipes()

print(datetime.datetime.now() - startTime) # End timer to measure run time