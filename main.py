from re import I
from dotenv import load_dotenv
load_dotenv()
from requests.exceptions import HTTPError
import requests  # pip install requests
import os
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



def professionsTable():
    # dropDatabase("recipetracker")
    # createDatabase("recipetracker")
    dropTable("skill_tier")
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
        print("Getting skill tiers for profession " + str(id[0]) + " from the blizzard api...")
        request = 'https://us.api.blizzard.com/data/wow/profession/'+ str(id[0]) +'?namespace=static-us'
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
    mycursor.execute("CREATE TABLE `recipetracker`.`recipes` ( `id` INT NOT NULL, `name` VARCHAR(255) NOT NULL, `icon` VARCHAR(255), `skill_tier_id` INT NOT NULL, PRIMARY KEY (`id`), INDEX `skill_tier_id_idx` (`skill_tier_id` ASC) VISIBLE, CONSTRAINT `skill_tier_id` FOREIGN KEY (`skill_tier_id`) REFERENCES `recipetracker`.`skill_tier` (`id`) ON DELETE NO ACTION ON UPDATE NO ACTION)")
    sqlAddRecipes= "INSERT INTO `recipes` (`id`, `name`, `skill_tier_id`) VALUES (%s, %s, %s);"
    mycursor.executemany(sqlAddRecipes, apiGetRecipes())
    print("Committing recipes to db...")
    mydb.commit()

def apiGetRecipes():
    fetchProfessionIds = "SELECT profession_id, id, name  FROM skill_tier"
    mycursor.execute(fetchProfessionIds)
    myResult = mycursor.fetchall()
    apiRecipes = []
    for profession in myResult:
        if profession[1] not in (2551, 2552, 2553, 2554, 2555, 2556, 2558, 2559, 2560, 2561, 2562, 2563, 2564, 2566,  2567, 2585, 2586, 2587, 2588, 2589, 2590, 2591, 2592, 2754, 2760, 2761, 2762):
            request = 'https://us.api.blizzard.com/data/wow/profession/' + str(profession[0]) + '/skill-tier/' + str(profession[1]) + '?namespace=static-us'
            response = requests.get(request, headers=headers)
            skillTierId = response.json().get('id')
            professionName = response.json().get('name')
            categories = response.json().get('categories')
            for category in categories:
                print("Getting recipes for category: " + str(category["name"]["en_US"]))
                recipes = category["recipes"]
                for recipe in recipes:
                    print("Appending " + str(recipe["name"]["en_US"]) + " to the list...")
                    apiRecipes.append(tuple((recipe["id"], recipe["name"]["en_US"], skillTierId)))
    print("Obtained recipes for all skill tiers for all professions in db...")
    return apiRecipes


# def getRecipeIcon():
#     mycursor.execute("SELECT id, name FROM recipes")
#     myResult = mycursor.fetchall()
#     recipeFileName = ""
#     recipeIcons = []
#     for recipe in myResult[:3]:
#         print("\nGetting " + str(recipe[0]) + ":" + str(recipe[1]) + " from the blizzard api...")
#         request = 'https://us.api.blizzard.com/data/wow/media/recipe/' + str(recipe[0]) + '?namespace=static-us'
#         response = requests.get(request, headers=headers)
#         recipeIconUrl = response.json().get('assets')[0]['value']
#         recipeFileName = recipeIconUrl[47:-4]
#         recipeIcons.append(tuple((str(recipe[1]), recipeFileName)))
#         recipeFileExtension = ".jpg"
#         print("Downloading image for " + str(recipe[0]) + ":" + recipeFileName)
#         iconData = requests.get(recipeIconUrl).content
#         print("Saving " + recipeFileName + recipeFileExtension + " to the directory...")
#         with open(recipeFileName+recipeFileExtension, "wb") as handler:
#             handler.write(iconData)
#     print(recipeIcons)
#     print(len(recipeIcons))
#     sqlAddRecipeIcon= "INSERT INTO `recipes` (`name`, `icon` ) VALUES (%s, %s);"
#     mycursor.executemany(sqlAddRecipeIcon,recipeIcons)
#     mydb.commit()

# def apiGetCrafted():
#     mycursor.execute("SELECT id, name FROM recipes")
#     myResult = mycursor.fetchall()
    
#     craftedItems = []
#     craftedAllianceItems = []
#     craftedHordeItems = []
#     for recipe in myResult:
#         print(recipe[0])
#     i=-1
#     n=-1
    # for recipe in myResult[:5]:
    #     request = 'https://us.api.blizzard.com/data/wow/recipe/' + str(recipe[0]) + '?namespace=static-us&locale=en_US'
    #     response = requests.get(request, headers=headers)
    #     recipeId = response.json().get("id")
    #     craftedItem = response.json().get("crafted_item")
    #     craftedAlliance = response.json().get("alliance_crafted_item")
    #     craftedHorde = response.json().get("horde_crafted_item")
    #     if craftedAlliance is not None or craftedHorde is not None:
    #         if len(craftedAllianceItems) > 0 and len(craftedHordeItems) > 0:
    #             if craftedAlliance.get("id") == craftedAllianceItems[i][2] or craftedHorde.get("id") == craftedHordeItems[i][2]:
    #                 print(i + ": Faction item already exists... skipping...")
    #                 continue
    #         print(i + ": Appending crafted item " + str(craftedAlliance.get("name")) + ":" + str(craftedAlliance.get("id")) + " with recipeId:" + str(recipeId) +" to craftedAllianceItems...")
    #         craftedAllianceItems.append(tuple((recipeId,craftedAlliance.get("name"),craftedAlliance.get("id"))))
    #         print(i + ": Appending crafted item " + str(craftedHorde.get("name")) + ":" + str(craftedHorde.get("id")) + " with recipeId:" + str(recipeId) +" to craftedHordeItems...")
    #         craftedHordeItems.append(tuple((recipeId,craftedHorde.get("name"),craftedHorde.get("id"))))
    #         i += 1
    #     elif craftedItem is not None:
    #         if len(craftedItems) > 0:
    #             if craftedItem.get("id") == craftedItems[n][2]:
    #                 print(n + ": Crafted item already exists... skipping...")
    #                 continue
    #         print("Appending crafted item " + str(craftedItem.get("name")) + ":" + str(craftedItem.get("id")) + " with recipeId:" + str(recipeId) +" to craftedItems...")
    #         craftedItems.append(tuple((recipeId,craftedItem.get("name"),craftedItem.get("id"))))
    #         n += 1
        
        
    print("Obtained crafted items for all recipe id in db...")
    return craftedItems, craftedAllianceItems, craftedHordeItems

craftedItems, craftedAllianceItems, craftedHordeItems = apiGetCrafted()

def craftedTable():
    dropTable("crafted")
    print("Creating craftede table...")
    mycursor.execute("""CREATE TABLE `recipetracker`.`crafted` (
                            `id` INT NOT NULL,
                            `name` VARCHAR(45) NOT NULL,
                            `crafted_recipe_id` INT NOT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `idcrafted_UNIQUE` (`id` ASC) VISIBLE,
                            INDEX `crafted_recipe_id_idx` (`crafted_recipe_id` ASC) VISIBLE,
                            CONSTRAINT `crafted_recipe_id`
                                FOREIGN KEY (`crafted_recipe_id`)
                                REFERENCES `recipetracker`.`recipes` (`id`)
                                ON DELETE NO ACTION
                                ON UPDATE NO ACTION);
""")
    sqlAddCrafted= "INSERT INTO `crafted` (`crafted_recipe_id`, `name`, `id`) VALUES (%s, %s, %s);"
    mycursor.executemany(sqlAddCrafted, craftedItems)
    print("Committing crafted to db...")
    mydb.commit()

def craftedAllianceTable():
    dropTable("crafted_alliance")
    print("Creating crafted_alliance table...")
    mycursor.execute("""CREATE TABLE `recipetracker`.`crafted_alliance` (
                            `id` INT NOT NULL,
                            `name` VARCHAR(255) NOT NULL,
                            `crafted_alliance_recipe_id` INT NOT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE,
                            INDEX `crafted_alliance_recipe_id_idx` (`crafted_alliance_recipe_id` ASC) VISIBLE,
                            CONSTRAINT `crafted_alliance_recipe_id`
                                FOREIGN KEY (`crafted_alliance_recipe_id`)
                                REFERENCES `recipetracker`.`recipes` (`id`)
                                ON DELETE NO ACTION
                                ON UPDATE NO ACTION);
""")
    sqlAddCraftedAlliance= "INSERT INTO `crafted_alliance` (`crafted_alliance_recipe_id`, `name`, `id`) VALUES (%s, %s, %s);"
    mycursor.executemany(sqlAddCraftedAlliance, craftedAllianceItems)
    print("Committing crafted_alliance to db...")
    mydb.commit()

def craftedHordeTable():
    dropTable("crafted_horde")
    print("Creating crafted_horde table...")
    mycursor.execute("""CREATE TABLE `recipetracker`.`crafted_horde` (
                            `id` INT NOT NULL,
                            `name` VARCHAR(255) NOT NULL,
                            `crafted_horde_recipe_id` INT NOT NULL,
                            PRIMARY KEY (`id`),
                            UNIQUE INDEX `id_UNIQUE` (`id` ASC) VISIBLE,
                            INDEX `crafted_horde_recipe_id_idx` (`crafted_horde_recipe_id` ASC) VISIBLE,
                            CONSTRAINT `crafted_horde_recipe_id`
                                FOREIGN KEY (`crafted_horde_recipe_id`)
                                REFERENCES `recipetracker`.`recipes` (`id`)
                                ON DELETE NO ACTION
                                ON UPDATE NO ACTION);
""")
    sqlAddCraftedHorde= "INSERT INTO `crafted_horde` (`crafted_horde_recipe_id`, `name`, `id`) VALUES (%s, %s, %s);"
    mycursor.executemany(sqlAddCraftedHorde, craftedHordeItems)
    print("Committing crafted_horde to db...")
    mydb.commit()





        

# craftedTable()
# craftedAllianceTable()
# craftedHordeTable()


print(datetime.datetime.now() - startTime)
