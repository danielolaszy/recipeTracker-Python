<!-- ABOUT THE PROJECT -->

## About The Project

[![Product Name Screen Shot][product-screenshot]](https://github.com/Voiidv2/wowRecipeTracker)

This Python project allows you to populate a mysql database from a json file from Data for Azeroth

## Getting Started

In order to get started with the code you'll need to have Python 3.9.6+. To get the project running locally, follow these simple steps.

### Prerequisites

- Python
- API credentials from [develop.battle.net](https://develop.battle.net/)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/Voiidv2/RecipeTrackerDB.git
   ```
2. Install python packages via pip
   ```sh
   pip install requests python-dotenv mysql-connector-python
   ```
3. Fill out the `.env` file
   ```JS
   MYSQL_HOST=
   MYSQL_USER=
   MYSQL_PASSWORD=
   MYSQL_DATABASE=
   API_ACCESS_TOKEN=
   ```

<!-- ACKNOWLEDGEMENTS -->

## Acknowledgements

- [Requests](https://docs.python-requests.org/en/master/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)
- [mysql-connector-python](https://github.com/mysql/mysql-connector-python)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[product-screenshot]: images/screenshot.png
