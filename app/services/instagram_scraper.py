from selenium import webdriver  # we're going to use selenium as an automator here that way insta doesn't detect us as a bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import os
# Add the parent directory to the path so we can import from app.models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User, FollowRelationship, Base

import time

class InstagramScraper: 
    def __init__(self):
        from selenium.webdriver.chrome.options import Options
        import os
        
        # Create a chrome_profile directory in your project
        profile_dir = os.path.join(os.getcwd(), "chrome_profile")
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.is_logged_in = False












        
    def login(self, username, password):
        print(f"trying to login as {username}")
        # Navigate to Instagram's login page
        self.driver.get("https://www.instagram.com/accounts/login/")
        
        try:
            # Wait up to 15 seconds for the username input box to appear on the page
            username_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            # Type the username into the input box
            username_input.send_keys(username)

            # Find the password input box and type the password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)

            # Find the submit button and click it to log in
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait 10 seconds for Instagram to process the login
            time.sleep(10)
            
            # Instagram shows popups after login - dismiss them
            # Try to click "Not now" on the "Save Login Info" popup
            try:
                not_now_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                not_now_button.click()
                time.sleep(2)
            except:
                pass  # If popup doesn't appear, that's fine - just continue
            
            # Try to dismiss the notifications popup if it appears
            try:
                not_now_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                not_now_button.click()
                time.sleep(2)
            except:
                pass  # If popup doesn't appear, that's fine
            
            print(f"After login, current URL: {self.driver.current_url}")
            
            # Check if we successfully logged in by seeing if we left the login page
            if "accounts/login" not in self.driver.current_url:
                print("login works")
                self.is_logged_in = True
            else:
                print("login failed")
                self.is_logged_in = False
                
        except Exception as e:
            print(f"Error During login: {e}")
            self.is_logged_in = False

    def get_following(self, username):
        """Gets the list of accounts that the user is following"""
        print(f"Get the follower person username: {username}")

        # Navigate to the user's Instagram profile page
        self.driver.get(f"https://www.instagram.com/{username}/")
        
        # Wait 3 seconds for the profile page to load
        time.sleep(3) 

        try:
            # Find the "following" link on the profile and wait until it's clickable
            # The link has '/following' in its href attribute
            following = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))
            )
            print(f"Found following link")
            
            # Click the following link to open the popup
            following.click()
            print("Clicked following!")
            
            # Wait 5 seconds for the following popup/modal to appear
            time.sleep(5)
            
            print("Starting to scrape usernames...")
            
            # Find the scrollable container inside the popup
            # Instagram puts following list in a div with 'overflow' style
            scroll_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
            )
            
            # Get the initial height of the scrollable area
            # We'll use this to know when we've reached the bottom
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
            
            # Scroll through the popup to load all users
            # Instagram lazy-loads users as you scroll, so we need to scroll to see everyone
            for i in range(10):  # Scroll up to 10 times
                # Scroll to the bottom of the container
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
                
                # Wait 2 seconds for Instagram to load more users
                time.sleep(2)
                
                # Check the new height after scrolling
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
                
                # If height didn't change, we've reached the end - stop scrolling
                if new_height == last_height:
                    break
                    
                # Update last_height for next iteration
                last_height = new_height
            
            # Now extract all the usernames from the popup
            # Find all links (a tags) that have an href attribute
            user_elements = scroll_box.find_elements(By.XPATH, ".//a[contains(@href, '/')]")
            
            # Create an empty list to store usernames
            following_list = []
            
            # Loop through each link we found
            for user in user_elements:
                # Get the href attribute (the URL)
                href = user.get_attribute("href")
                
                # Check if href exists and has enough slashes (valid profile link)
                # Valid profile links look like: https://instagram.com/username/
                if href and href.count("/") >= 4:
                    # Split the URL by "/" and get the username (second to last part)
                    username = href.split("/")[-2]
                    
                    # Only add if username exists and isn't already in our list (no duplicates)
                    if username and username not in following_list:
                        following_list.append(username)
            
            # Print results
            print(f"\nFound {len(following_list)} users you're following:")
            # Print first 10 usernames as a preview
            for user in following_list[:10]:
                print(f"  - {user}")
            
            # Return the complete list of usernames
            return following_list

        except Exception as e:
            # If anything goes wrong, print the error and take a screenshot for debugging
            print(f"An error occurred: {e}")
            self.driver.save_screenshot("debug.png")
            return []  # Return empty list if there was an error
        
    def get_followers(self, username):
        #this is the function we're using to pull the users followers 
        print(f"Get the users followers: {username}")
        self.driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(3) 

        try:
            # Find the "following" link on the profile and wait until it's clickable
            # The link has '/following' in its href attribute
            following = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))
            )
            print(f"Found follower link")
            
            # Click the following link to open the popup
            following.click()
            print("Clicked follower!")
            
            # Wait 5 seconds for the following popup/modal to appear
            time.sleep(5)
            
            print("Starting to scrape usernames...")
            
            # Find the scrollable container inside the popup
            # Instagram puts following list in a div with 'overflow' style
            scroll_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[contains(@style, 'overflow')]"))
            )
            
            # Get the initial height of the scrollable area
            # We'll use this to know when we've reached the bottom
            last_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
            
            # Scroll through the popup to load all users
            # Instagram lazy-loads users as you scroll, so we need to scroll to see everyone
            for i in range(10):  # Scroll up to 10 times
                # Scroll to the bottom of the container
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scroll_box)
                
                # Wait 2 seconds for Instagram to load more users
                time.sleep(2)
                
                # Check the new height after scrolling
                new_height = self.driver.execute_script("return arguments[0].scrollHeight", scroll_box)
                
                # If height didn't change, we've reached the end - stop scrolling
                if new_height == last_height:
                    break
                    
                # Update last_height for next iteration
                last_height = new_height
            
            # Now extract all the usernames from the popup
            # Find all links (a tags) that have an href attribute
            user_elements = scroll_box.find_elements(By.XPATH, ".//a[contains(@href, '/')]")
            
            # Create an empty list to store usernames
            following_list = []
            
            # Loop through each link we found
            for user in user_elements:
                # Get the href attribute (the URL)
                href = user.get_attribute("href")
                
                # Check if href exists and has enough slashes (valid profile link)
                # Valid profile links look like: https://instagram.com/username/
                if href and href.count("/") >= 4:
                    # Split the URL by "/" and get the username (second to last part)
                    username = href.split("/")[-2]
                    
                    # Only add if username exists and isn't already in our list (no duplicates)
                    if username and username not in following_list:
                        following_list.append(username)
            
            # Print results
            print(f"\nFound {len(following_list)} users that are folliwng you:")
            # Print first 10 usernames as a preview
            for user in following_list[:10]:
                print(f"  - {user}")
            
            # Return the complete list of usernames
            return following_list

        except Exception as e:
            # If anything goes wrong, print the error and take a screenshot for debugging
            print(f"An error occurred: {e}")
            self.driver.save_screenshot("debug.png")
            return []  # Return empty list if there was an error
        

    def find_unfollowers(self, following_list, followers_list):
        
        unfollowers = []

        for person in following_list:
            if person not in followers_list:
                unfollowers.append(person)
        return unfollowers
    def save_to_database(self, username, following_list, followers_list):
    # this is where we're going to save the follower/following data to the database
    # this imports the models and sets up the database 
       
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # first we have to make the database connection 
        # this will connect our scraper to the database file instagram_tracker 

        import os 
        db_path = os.path.join(os.path.dirname(__file__), 'instagram_tracker.db')
        engine = create_engine(f'sqlite:///{db_path}')
        print(f"Database will be created at: {db_path}")
        # then we need to create all the tables if they don't exist 
        # it looks at our base models and creates the actual database tables 
        Base.metadata.create_all(engine)
        
        # then we need to create a session which is opening a connection to talk to the database
        # this is how we send commands to the database 
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            # then we need to check if the user already exists in the database 
            # first we ask the database a question using Query
            # then we use filter_by to find the rows where instagram_username matches 
            # then we use first() to get the first result or none if no results
            existing_user = session.query(User).filter_by(insta_user=username).first()
            
            # if the user doesn't exist, we create them 
            if not existing_user:
                print(f"creating the user name for {username}") 
                new_user = User(
                    email=f"{username}@placeholder.com",  # this is just the placeholder name 
                    insta_user=username, 
                    insta_password="encrypted_password",  # this is for password encryption 
                    is_active=True  # this just tells us if the user is up and running 
                )
                # then we add this record to be saved 
                session.add(new_user)
                # then we need to save it to the db 
                session.commit()
                # then we need to set the existing_user to the one we just made 
                existing_user = new_user
                print(f"user {username} saved to the database")
            else:
                print(f"user {username} already exists gng")
            
            # this deletes the old relationships records for this user, we'll replace them with fresh data
            # the delete() removes the records from the database 
            session.query(FollowRelationship).filter_by(user_id=existing_user.id).delete()
            session.commit()
            print("deleted old relationship data")
            
            # save all the following relationships 
            print(f"saving {len(following_list)} following relationships...")
            for username_followed in following_list:
                # checks if they follow you back 
                they_follow_back = username_followed in followers_list
                relationship = FollowRelationship(
                    user_id=existing_user.id,  # link to the user
                    instagram_user_id=username_followed,  # the person being followed
                    username=username_followed, 
                    full_name="",  # we don't have this data yet 
                    profile_pic_url="",  # we don't have this data yet 
                    i_follow_them=True,  # yes, you follow them 
                    they_follow_me=they_follow_back  # true if they're in followers_list 
                )
                session.add(relationship)
            
            # save all changes at once 
            session.commit()
            print(f"successfully saved {len(following_list)} relationships to database")

            # show summary 
            total_relationships = session.query(FollowRelationship).filter_by(user_id=existing_user.id).count()
            print(f"Total relationships in database: {total_relationships}")
        
        except Exception as e:
            # If anything goes wrong, undo changes
            print(f"Error saving to database: {e}")
            session.rollback()
        
        finally:
            # Always close the session when done
            session.close()
            








# This code runs when you execute the script

# This code runs when you execute the script
if __name__ == "__main__":
    scraper = InstagramScraper()
    scraper.login("theoneandonly3034","roriolaniyi123")

    # Get both lists
    following = scraper.get_following("theoneandonly3034")
    followers = scraper.get_followers("theoneandonly3034")

    # Find unfollowers
    unfollowers = scraper.find_unfollowers(following, followers)

    # Print results
    print(f"\n--- RESULTS ---")
    print(f"You follow: {len(following)} people")
    print(f"Follow you: {len(followers)} people")
    print(f"Don't follow back: {len(unfollowers)} people")
    print(f"\nPeople who don't follow you back:")
    for user in unfollowers:
        print(f"  - {user}")

    # NEW: Save to database
    print("\n--- SAVING TO DATABASE ---")
    scraper.save_to_database("theoneandonly3034", following, followers)
    
    input("Press Enter to close browser...")
    scraper.driver.quit()
    