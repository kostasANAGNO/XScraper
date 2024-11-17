# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from datetime import datetime, timedelta
import re
import json
import mysql.connector
import time
import logging
from langdetect import detect, LangDetectException
from config import TWITTER_AUTH_TOKEN #in config file there is our Twitter(X) authentication token

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class TwitterExtractor:
    def __init__(self, headless=True, max_tweets=500):
        self.headless = headless
        self.max_tweets = max_tweets
        self.driver = self._start_chrome(headless)
        self.set_token()
        self.data = []

    def _start_chrome(self, headless):
        options = Options()
        options.add_argument('--sandbox')
        options.headless = headless
        driver = webdriver.Chrome(options=options)
        driver.get("https://twitter.com")
        return driver

    def set_token(self, auth_token=TWITTER_AUTH_TOKEN):
        if not auth_token or auth_token == "YOUR_TWITTER_AUTH_TOKEN_HERE":
            raise ValueError("Access token is missing. Please configure it properly.")
        expiration = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        cookie_script = f"document.cookie = 'auth_token={auth_token}; expires={expiration}; path=/';"
        self.driver.execute_script(cookie_script)

    def search_tweets(self, hashtags, start_date, end_date):
        for hashtag in hashtags:
            # Clear the data list for the new hashtag
            self.data = []
            
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date_dt = datetime.strptime(end_date, "%Y-%m-%d")
            delta = timedelta(minutes=30)  # Use of 30 minutes gap

            while current_date < end_date_dt:
                next_date = current_date + delta
                if next_date > end_date_dt:
                    next_date = end_date_dt

                start_str = current_date.strftime("%Y-%m-%d_%H:%M:%S_UTC")
                end_str = next_date.strftime("%Y-%m-%d_%H:%M:%S_UTC")

                logger.info(f"Searching tweets for #{hashtag} from {start_str} to {end_str}")

                try:
                    self.driver.get(f"https://twitter.com/search?q=%23{hashtag}%20since%3A{start_str}%20until%3A{end_str}&src=typed_query&f=live")
                    self.fetch_tweets(current_date, next_date)
                except WebDriverException as e:
                    logger.error(f"Error fetching tweets: {e}")
                    time.sleep(600)  # Sleep for 5 minutes before retrying
                    self.driver.get(f"https://twitter.com/search?q=%23{hashtag}%20since%3A{start_str}%20until%3A{end_str}&src=typed_query&f=live")
                    self.fetch_tweets(current_date, next_date)

                current_date = next_date
                time.sleep(150)  # Add delay between each request within the same hashtag

            logger.info(f"Completed searching for #{hashtag}, saving data and sleeping before next hashtag.")
            self._save_to_json(hashtag)
            self.save_to_mysql(
                host="######",#host maybe 'localhost'
                user="#####",#User in our local database maybe 'root'
                password="######",#database account password
                database="####",#database name maybe mydatabase
                table="#####"  # Using a single table for all hashtags
            )
            time.sleep(300)  # Add delay between different hashtags

    def fetch_tweets(self, start_date, end_date):
        collected_tweets = 0
        consecutive_no_new_tweets = 0  # Counter if there aren't new tweets

        while collected_tweets < self.max_tweets:
            try:
                time.sleep(3)  # delay for loading
                tweets = self.driver.find_elements(By.XPATH, '//article[@role="article"]')
                if not tweets:  # if there aren't new tweets , we exit 
                    logger.info("No more tweets found, stopping extraction.")
                    break
                
                new_tweets_collected = 0  # Counter for the tweets we collected in this extraction
                
                for tweet in tweets:
                    tweet_data = self._extract_tweet_data(tweet)
                    if not tweet_data or tweet_data in self.data:
                        continue
                    tweet_date = datetime.strptime(tweet_data['date'], "%Y-%m-%d %H:%M:%S")
                    if start_date <= tweet_date <= end_date:
                        self.data.append(tweet_data)
                        collected_tweets += 1
                        new_tweets_collected += 1
                        if collected_tweets >= self.max_tweets:
                            logger.info(f"Collected {collected_tweets} tweets, stopping extraction.")
                            return
                    elif tweet_date < start_date:
                        logger.info("Reached start date, exiting")
                        return

                if new_tweets_collected == 0:
                    consecutive_no_new_tweets += 1
                    if consecutive_no_new_tweets >= 3:  # if there aren't new tweets in the last three scrolls, we stop the extraction
                        logger.info("No new tweets collected in the last 3 scrolls, stopping extraction.")
                        break
                else:
                    consecutive_no_new_tweets = 0  # Reset the counter if we collected new tweets

                if collected_tweets < self.max_tweets:
                    self._scroll_down()
            except NoSuchElementException as e:
                logger.error(f"Error extracting tweets: {e}")
                break

    def _extract_tweet_data(self, tweet):
        try:
            # Extract tweet ID from the URL
            tweet_url = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]').get_attribute('href')
            tweet_id = tweet_url.split('/')[-1]
            
            text = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
            author_name = tweet.find_element(By.XPATH, './/div[@dir="ltr"]/span').text
            author_handle = tweet.find_element(By.XPATH, './/div[@dir="ltr"]/span[contains(text(), "@")]').text
            date_element = tweet.find_element(By.XPATH, './/time')
            date = date_element.get_attribute('datetime') if date_element else None
            if date:
                date = datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d %H:%M:%S")
            try:
                lang = detect(text)
            except LangDetectException:
                lang = ""
            url = tweet.find_element(By.XPATH, './/a[@role="link"]').get_attribute('href')
            mentioned_urls = [a.get_attribute('href') for a in tweet.find_elements(By.XPATH, './/a[@role="link"]')]
            is_retweet = 'retweeted' in tweet.get_attribute('class')
            media_type = 'image' if tweet.find_elements(By.XPATH, './/img') else 'text'
            images_urls = [img.get_attribute('src') for img in tweet.find_elements(By.XPATH, './/img')]

            # We find the counts for replies , retweets and likes
            num_reply = self.__get_tweet_num_reply(tweet)
            num_retweet = self.__get_tweet_num_retweet(tweet)
            num_like = self.__get_tweet_num_like(tweet)

            tweet_data = {
                "id": tweet_id,
                "text": text,
                "author_name": author_name,
                "author_handle": author_handle,
                "date": date,
                "lang": lang,
                "url": url,
                "mentioned_urls": mentioned_urls,
                "is_retweet": is_retweet,
                "media_type": media_type,
                "images_urls": images_urls,
                "num_reply": num_reply,
                "num_retweet": num_retweet,
                "num_like": num_like,
            }
            logger.debug(f"Extracted tweet data: {tweet_data}")
            return tweet_data
        except NoSuchElementException as e:
            logger.error(f"Error extracting tweet data: {e}")
            return {}

    def __get_tweet_num_reply(self, tweet):
        try:
            num = tweet.find_element(By.CSS_SELECTOR, "button[data-testid='reply']").get_attribute("innerText")
            return self.convert_to_number(num)
        except (NoSuchElementException, ValueError):
            return 0

    def __get_tweet_num_retweet(self, tweet):
        try:
            num = tweet.find_element(By.CSS_SELECTOR, "button[data-testid='retweet']").get_attribute("innerText")
            return self.convert_to_number(num)
        except (NoSuchElementException, ValueError):
            return 0

    def __get_tweet_num_like(self, tweet):
        try:
            num = tweet.find_element(By.CSS_SELECTOR, "button[data-testid='like']").get_attribute("innerText")
            return self.convert_to_number(num)
        except (NoSuchElementException, ValueError):
            return 0

    def convert_to_number(self, num_str):
        if 'K' in num_str:
            return int(float(num_str.replace('K', '').replace(',', '')) * 1000)
        elif 'M' in num_str:
            return int(float(num_str.replace('M', '').replace(',', '')) * 1000000)
        else:
            return int(num_str.replace(',', ''))

    def _scroll_down(self):
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)  # increasing the delay for load more tweets

    def _save_to_json(self, hashtag):
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{hashtag}_tweets_{current_time}.json"
        with open(f"{filename}", "w", encoding='utf-8') as file:
            json.dump(self.data, file, ensure_ascii=False, indent=4)
        logger.info(f"Data saved to {filename}")

    def save_to_mysql(self, host, user, password, database, table):
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = connection.cursor()

        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table} (
            id VARCHAR(50),
            text TEXT,
            author_name VARCHAR(255),
            author_handle VARCHAR(255),
            date DATETIME,
            lang VARCHAR(10),
            url VARCHAR(255),
            mentioned_urls TEXT,
            is_retweet BOOLEAN,
            media_type VARCHAR(50),
            images_urls TEXT,
            num_reply INT,
            num_retweet INT,
            num_like INT
        )
        """
        cursor.execute(create_table_query)

        insert_query = f"""
        INSERT INTO {table} 
        (id, text, author_name, author_handle, date, lang, url, mentioned_urls, is_retweet, media_type, images_urls, num_reply, num_retweet, num_like) 
        VALUES 
        (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        for tweet in self.data:
            data_tuple = (
                tweet.get("id", ""),
                tweet.get("text", ""),
                tweet.get("author_name", ""),
                tweet.get("author_handle", ""),
                tweet.get("date", ""),
                tweet.get("lang", ""),
                tweet.get("url", ""),
                json.dumps(tweet.get("mentioned_urls", [])),
                tweet.get("is_retweet", False),
                tweet.get("media_type", ""),
                json.dumps(tweet.get("images_urls", [])),
                tweet.get("num_reply", 0),
                tweet.get("num_retweet", 0),
                tweet.get("num_like", 0),
            )
            try:
                cursor.execute(insert_query, data_tuple)
            except mysql.connector.errors.ProgrammingError as e:
                logger.error(f"Error inserting data into MySQL: {e}")
                logger.error(f"Data tuple: {data_tuple}")

        connection.commit()
        connection.close()
        logger.info(f"Data saved to MySQL table {table}")

    def close_browser(self):
        self.driver.quit()
        logger.info("Browser closed")

if __name__ == "__main__":
    hashtags = ["Election2024"]  #Add the hashtags we want to search for
    scraper = TwitterExtractor(headless=True, max_tweets=2000)  # Ceil for tweets in a single extraction is 2000 tweets

    start_date = datetime.strptime("2024-01-01", "%Y-%m-%d")
    end_date = datetime.strptime("2024-12-30", "%Y-%m-%d")

    while start_date < end_date:
        next_day = start_date + timedelta(days=1)
        scraper.search_tweets(
            hashtags=hashtags,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=next_day.strftime("%Y-%m-%d"),
        )
        start_date = next_day
        time.sleep(600)  # Add delay between different days to avoid rate limits

    scraper.close_browser()
