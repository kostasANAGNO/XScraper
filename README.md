# TwitterScraper

This project based on fetching tweets from Twitter(X) hashtags. Running the code you can see the impact of python's library Selenium in data extraction from web. The first code (HashtagScraperV1) can extract many tweets of a unique hashtag with efficients techniques and save them to a JSON file with the name of selected hashtag and the current timestramp .

# PREREQUISITES
Before running the code, ensure you have the following:

Required Python libraries (listed in requirements.txt)
Get your twitter auth token (Not API key)
Quick text instruction:
Go to your already logged-in twitter
F12 (open dev tools) -> Application -> Cookies -> Twitter.com -> auth_key

# SETUP
Clone the repository or download the project files.
Install the required Python libraries by running the following command:
pip install -r requirements.txt
Open the config.py file and replace the placeholders with your actual API keys:
Set TWITTER_AUTH_TOKEN to your Twitter API authentication token.

# Data Extraction
To extract data from a hashtag and save them to JSON file:
1.Open the HashtagScraperV1.py .
2.Set the Twitter hashtag you want to fetch in the list hashtags in main .
3.Specify the start and end dates for the data range (in YYYY-MM-DD format) , only start_date < end_date .
4.Run the code in your IDE by executing python HashtagScraperV1.py , the code will fetch the data and save them to a JSON file.

# In conclusion 
Json files are easy to read and write and you can easily perform initial data analysis.
If you want to store your data in a local database in this situation in a MySql database you can run HashtagScraperV2.py instead.
1.Install mysql.connector with pip install mysql-connector-python . 
2.Set your root ,user , password , database and table in the search_tweets function .
3.Run the code in your IDE by executing python HashtagScraperV2.py , the code will fetch the data and save them to a JSON file and stores them to your local database . 

