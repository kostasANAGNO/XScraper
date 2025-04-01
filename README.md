
# XkeywordScraper

This project is designed for scraping tweets from Twitter (now X) based on specific hashtags. The code utilizes Python's **Selenium** library for efficient web scraping. The first script (**KeywordScraperV1**) extracts tweets related to  given keywords and saves them in a JSON file. The JSON file is named using the keywords and the current timestamp.

## PREREQUISITES

Before running the code, make sure you have the following:

- The required Python libraries (listed in `requirements.txt`)
- Your **Twitter Authentication Token** (not the API key)

### Quick Text Instruction:

1. Log in to Twitter.
2. Press **F12** (to open Developer Tools).
3. Navigate to **Application > Cookies > twitter.com > auth_key** to get the authentication token.

## SETUP

1. Clone the repository or download the project files.
2. Install the required Python libraries by running:
   ```bash
   pip install -r requirements.txt
   ```
3. Open the `config.py` file and replace the placeholders with your actual Twitter authentication token:
   - Set the `TWITTER_AUTH_TOKEN` to your Twitter API authentication token.

## Data Extraction

To extract tweets from some keywords and save them to a JSON file:

1. Open `keywordScraperV1.py`.
2. Set the Twitter keywords you want to scrape in the `keywords` list inside the `main` function.
3. Specify the **start** and **end dates** for the data range (in **YYYY-MM-DD** format). Ensure that `start_date` is earlier than `end_date`.
4. Run the script in your IDE by executing:
   ```bash
   python KeywordsScraperV1.py
   ```
   The script will fetch tweets and save them to a JSON file named after the hashtag and timestamp.

## Alternative: Storing Data in MySQL

If you prefer to store the data in a local MySQL database instead of a JSON file, you can use **KeywordScraperV2.py**.

1. Install MySQL connector:
   ```bash
   pip install mysql-connector-python
   ```
2. In the `search_tweets` function, set your MySQL connection parameters (e.g., `root`, `user`, `password`, `database`, `table`).
3. Run the script in your IDE by executing:
   ```bash
   python KeywordScraperV2.py
   ```
   This will scrape tweets and save them both in a JSON file and a local MySQL database.

## Conclusion

The JSON format makes it easy to read and write the data, enabling quick initial data analysis. You can extend the functionality to perform more advanced analyses or store the data in different formats.

## Project Overview

This is an individual project aimed at gaining familiarity with tools and libraries used for web scraping, specifically the Selenium library. Selenium is one of the most accessible and secure libraries for web scraping in Python, making it a valuable tool for various data extraction tasks. The project was created to enhance practical knowledge of handling web scraping challenges, utilizing automation to extract meaningful data from social media platforms like Twitter.

Personal email: k.anagnostou200328@gmail.com

