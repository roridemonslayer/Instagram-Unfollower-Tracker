from selenium import webdriver  # we're going to use selenium as an automator here that way insta doesn't detect us as a bot
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class InstagramScraper: 
    def __init__(self):
        # Creates a Chrome browser instance that Selenium will control
        # This keeps cookies between requests so Instagram remembers we're logged in
        self.driver = webdriver.Chrome()
        self.is_logged_in = False # Tracks whether the user has successfully logged in
    
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
        










# This code runs when you execute the script
if __name__ == "__main__":
    # Create an instance of InstagramScraper
    scraper = InstagramScraper()
    
    # Log in with your credentials
    scraper.login("theoneandonly3034","roriolaniyi123")
    
    # Get the list of people you're following
    scraper.get_following("theoneandonly3034")
    scraper.get_followers("theoneandonly3034")
    
    # Keep the browser open until you press Enter
    input("Press Enter to close browser...")
    
    # Close the browser
    scraper.driver.quit()