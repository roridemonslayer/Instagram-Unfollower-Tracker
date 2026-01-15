# Import Selenium library - this lets us control a web browser automatically
from selenium import webdriver
# Import tools to locate elements on web pages (like buttons, text boxes)
from selenium.webdriver.common.by import By
# Import WebDriverWait - makes Selenium wait for elements to appear on page
from selenium.webdriver.support.ui import WebDriverWait
# Import expected_conditions - defines what conditions to wait for (like "element is clickable")
from selenium.webdriver.support import expected_conditions as EC
# Import Keys - lets us send keyboard keys like Enter, Page Down, Escape
from selenium.webdriver.common.keys import Keys
# Import sys and os - system libraries for file paths and system operations
import sys
import os
# Add the parent directory to Python's search path so we can import our database models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our database models (User and FollowRelationship tables)
from models.user import User, FollowRelationship, Base
# Import time library - lets us pause execution with time.sleep()
import time

# Define our Instagram scraper class - this contains all the scraping logic
class InstagramScraper: 
    def __init__(self):
        """Initialize the scraper - this runs when you create a new InstagramScraper object"""
        # Import Chrome options - lets us customize how Chrome behaves
        from selenium.webdriver.chrome.options import Options
        
        # Create a folder to store Chrome profile data (cookies, login info, etc.)
        profile_dir = os.path.join(os.getcwd(), "chrome_profile")
        # If the folder doesn't exist, create it
        if not os.path.exists(profile_dir):
            os.makedirs(profile_dir)
        
        # Create a Chrome options object to configure the browser
        chrome_options = Options()
        # Tell Chrome to use our profile directory (this saves your login between runs)
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
        # Disable sandbox mode (required for some systems)
        chrome_options.add_argument("--no-sandbox")
        # Use /tmp instead of /dev/shm for shared memory (prevents crashes on low-memory systems)
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Create a Chrome browser instance with our custom options
        self.driver = webdriver.Chrome(options=chrome_options)
        # Set login status to False initially (we haven't logged in yet)
        self.is_logged_in = False
        
    def login(self, username, password):
        """Log into Instagram with the provided username and password"""
        # Print status message to console
        print(f"Attempting to login as {username}")
        # Navigate to Instagram's login page
        self.driver.get("https://www.instagram.com/accounts/login/")
        
        try:
            # Wait up to 15 seconds for the username input box to appear on the page
            # This is necessary because pages load gradually
            username_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            # Type the username into the input box
            username_input.send_keys(username)

            # Find the password input box (it's already on the page, so no need to wait)
            password_input = self.driver.find_element(By.NAME, "password")
            # Type the password into the password box
            password_input.send_keys(password)

            # Find the login submit button using XPath (a way to locate elements)
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            # Click the login button
            login_button.click()
            
            # Wait 10 seconds for Instagram to process the login
            time.sleep(10)
            
            # Instagram shows popup dialogs after login - we need to dismiss them
            # Try to click "Not now" on the "Save Login Info" popup
            try:
                # Find the "Not now" button (text could be "Not now" or "Not Now")
                not_now_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                # Click it to dismiss the popup
                not_now_button.click()
                # Wait 2 seconds for the popup to close
                time.sleep(2)
            except:
                # If the popup doesn't appear, that's fine - just continue
                pass
            
            # Try to dismiss the notifications popup if it appears
            try:
                # Find another "Not now" button (for notifications)
                not_now_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                # Click it
                not_now_button.click()
                # Wait 2 seconds
                time.sleep(2)
            except:
                # If this popup doesn't appear either, that's fine
                pass
            
            # Check if login was successful by looking at the current URL
            # If we're still on the login page, login failed
            if "accounts/login" not in self.driver.current_url:
                print("✓ Login successful")
                # Set the login flag to True
                self.is_logged_in = True
            else:
                print("✗ Login failed")
                # Set the login flag to False
                self.is_logged_in = False
                
        except Exception as e:
            # If anything goes wrong during login, print the error
            print(f"Error during login: {e}")
            # Set login status to False
            self.is_logged_in = False

    def _find_scroll_container(self):
        """Try multiple ways to find the scrollable container in Instagram's modal"""
        # Instagram changes their HTML structure frequently, so we try multiple selectors
        # Each selector is a different way to find the scrollable div
        selectors = [
            # Selector 1: Find a div with role="dialog" that contains a div with "overflow" in its style
            "//div[@role='dialog']//div[contains(@style, 'overflow')]",
            # Selector 2: Find a div inside a dialog with class containing "_aano"
            "//div[@role='dialog']//div[@class and contains(@class, '_aano')]",
            # Selector 3: Find a div with class containing "isgrP" (old Instagram class)
            "//div[@role='dialog']//div[contains(@class, 'isgrP')]",
            # Selector 4: Just find any dialog div (least specific, last resort)
            "//div[@role='dialog']",
            # Selector 5: Find any div with class containing "x1n2onr6"
            "//div[contains(@class, 'x1n2onr6')]",
            # Selector 6: Find any div with class "_aano" (not just inside dialogs)
            "//div[contains(@class, '_aano')]"
        ]
        
        # Try each selector one by one
        for selector in selectors:
            try:
                # Try to find an element using this selector
                element = self.driver.find_element(By.XPATH, selector)
                # If we found it, print success message
                print(f"✓ Found container with selector: {selector}")
                # Return the element we found
                return element
            except:
                # If this selector didn't work, move on to the next one
                continue
        
        # If none of the selectors worked, print error message
        print("❌ Could not find scroll container with any selector!")
        # Return None to indicate failure
        return None

    def get_following(self, username, max_following=None):
        """Gets the list of accounts that a user is following"""
        # Print a header to show we're starting the following scrape
        print(f"\n{'='*60}")
        print(f"Getting following list for: {username}")
        print(f"{'='*60}")
        # Navigate to the user's Instagram profile page
        self.driver.get(f"https://www.instagram.com/{username}/")
        # Wait 5 seconds for the profile page to fully load
        time.sleep(5)

        try:
            # Try to read how many accounts the user follows from their profile
            try:
                # Find the "following" link element
                following_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/following')]")
                # Get the text from that element (e.g., "1,234 following")
                expected_text = following_elem.text
                # Print it so we know what to expect
                print(f"🎯 Profile shows: {expected_text}")
            except:
                # If we can't read the count, that's okay - just continue
                print("⚠️  Could not read following count")
            
            # Wait up to 15 seconds for the "following" button to be clickable
            following = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))
            )
            # Click the "following" button to open the modal popup
            following.click()
            print("✓ Clicked following button")
            # Wait 10 seconds for the modal to fully load and populate
            time.sleep(10)
            
            # Take a screenshot for debugging purposes (saved as following_modal_structure.png)
            self.driver.save_screenshot("following_modal_structure.png")
            print("📸 Screenshot saved")
            
            # Try to find the scrollable container inside the modal
            scroll_box = self._find_scroll_container()
            # If we couldn't find the scroll container, we can't continue
            if not scroll_box:
                print("❌ CRITICAL: Cannot find scroll container!")
                # Return an empty list
                return []
            
            # Create a set to store unique usernames (sets automatically remove duplicates)
            following_set = set()
            # Counter for how many times we've scrolled
            scroll_count = 0
            # Maximum number of scrolls to attempt (prevents infinite loops)
            max_scrolls = 3000
            # Counter for how many consecutive scrolls found no new users
            stale_count = 0
            
            print("\n🔄 Starting scroll process...")
            print("=" * 60)
            
            # Get the initial height of the page (used to detect if scrolling is working)
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Main scrolling loop - keep scrolling until we hit max_scrolls or get stuck
            while scroll_count < max_scrolls:
                # EXTRACTION PHASE: Get all usernames currently visible on the page
                try:
                    # Find ALL <a> (link) elements on the entire page
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    # Loop through each link
                    for link in links:
                        try:
                            # Get the href attribute (the URL the link points to)
                            href = link.get_attribute("href")
                            # Check if href exists and contains "instagram.com/"
                            if href and "instagram.com/" in href:
                                # Split the URL to extract the username
                                # Example: "https://instagram.com/username/" becomes ["https:", "", "username", ""]
                                parts = href.split("instagram.com/")[-1].split("/")
                                # The username is the first part after instagram.com/
                                if len(parts) > 0:
                                    potential_username = parts[0]
                                    # Filter out non-profile links (posts, explore page, etc.)
                                    # Check if the username doesn't contain these keywords
                                    if potential_username and not any(x in potential_username for x in 
                                        ['explore', 'direct', 'accounts', 'p', 'reels', 'tv', '?', '=']):
                                        # Check if username is a reasonable length (1-30 characters)
                                        if len(potential_username) > 0 and len(potential_username) < 31:
                                            # Add the username to our set (duplicates are automatically ignored)
                                            following_set.add(potential_username)
                        except:
                            # If there's any error processing this link, skip it and move on
                            continue
                except Exception as e:
                    # If there's an error in the entire extraction phase, print it
                    print(f"Error in extraction: {e}")
                
                # Store the current count before scrolling
                current_count = len(following_set)
                
                # SCROLLING PHASE: Scroll the modal using multiple methods
                
                # SCROLL METHOD 1: Use JavaScript to scroll the dialog's scrollable div
                try:
                    self.driver.execute_script("""
                        // Find the dialog element
                        var dialog = document.querySelector('div[role="dialog"]');
                        if (dialog) {
                            // Find the scrollable div inside the dialog
                            var scrollable = dialog.querySelector('div[style*="overflow"]');
                            if (scrollable) {
                                // Scroll to the bottom of that div
                                scrollable.scrollTop = scrollable.scrollHeight;
                            }
                        }
                    """)
                except:
                    # If this method fails, that's okay - we have backup methods
                    pass
                
                # SCROLL METHOD 2: Send a Page Down keyboard event to the body
                try:
                    # Find the body element
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    # Send the Page Down key to it
                    body.send_keys(Keys.PAGE_DOWN)
                except:
                    # If this fails, continue with other methods
                    pass
                
                # SCROLL METHOD 3: Use JavaScript to scroll the entire window
                # This scrolls the whole page (not just the modal)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # Wait 2 seconds for Instagram to load more content after scrolling
                time.sleep(2)
                
                # Check if we found any new users after scrolling
                new_count = len(following_set)
                if new_count > current_count:
                    # We found new users! Reset the stale counter
                    stale_count = 0
                    # Every 20 scrolls, print a progress update
                    if scroll_count % 20 == 0:
                        print(f"📊 Scroll #{scroll_count}: Found {new_count} accounts")
                else:
                    # No new users found, increment the stale counter
                    stale_count += 1
                
                # Check if we've been stuck (no new users) for 20 consecutive scrolls
                if stale_count >= 20:
                    print(f"\n⚠️  Stuck at {new_count} accounts after 20 attempts")
                    
                    # AGGRESSIVE FINAL ATTEMPT - try really hard to get more users
                    print("🔥 Trying aggressive final scroll...")
                    # Do 30 rapid scroll attempts
                    for i in range(30):
                        # JavaScript to scroll ALL divs in ALL dialogs
                        self.driver.execute_script("""
                            // Find all dialog elements
                            var dialogs = document.querySelectorAll('div[role="dialog"]');
                            // For each dialog...
                            dialogs.forEach(function(dialog) {
                                // Find all divs inside it
                                var scrollables = dialog.querySelectorAll('div');
                                // Scroll each div to the bottom
                                scrollables.forEach(function(s) {
                                    s.scrollTop = s.scrollHeight;
                                });
                            });
                        """)
                        # Also send Page Down key
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                        # Short wait between scroll attempts
                        time.sleep(0.5)
                    
                    # Wait 3 seconds for content to load after aggressive scrolling
                    time.sleep(3)
                    
                    # Extract usernames one more time after aggressive scrolling
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and "instagram.com/" in href:
                                parts = href.split("instagram.com/")[-1].split("/")
                                if len(parts) > 0:
                                    potential_username = parts[0]
                                    if potential_username and not any(x in potential_username for x in 
                                        ['explore', 'direct', 'accounts', 'p', 'reels', 'tv', '?', '=']):
                                        if len(potential_username) > 0 and len(potential_username) < 31:
                                            following_set.add(potential_username)
                        except:
                            continue
                    
                    # Check if we got any new users from aggressive scrolling
                    final_count = len(following_set)
                    if final_count == new_count:
                        # Still stuck - give up
                        print(f"✓ Confirmed: Cannot get more than {final_count} accounts")
                        print(f"⚠️  Instagram is blocking us - this is a rate limit issue")
                        # Break out of the while loop
                        break
                    else:
                        # We got more users! Keep going
                        print(f"✓ Got {final_count - new_count} more! Continuing...")
                        # Reset stale counter
                        stale_count = 0
                
                # Increment scroll counter
                scroll_count += 1
                
                # If we've reached the max limit specified by user, stop
                if max_following and len(following_set) >= max_following:
                    break
            
            # Convert the set to a list (lists are easier to work with)
            following_list = list(following_set)
            
            # Filter out common non-username values that might have been captured
            following_list = [u for u in following_list if u not in 
                ['', 'instagram', 'login', 'accounts', 'explore', 'direct']]
            
            # Print final results
            print(f"\n{'='*60}")
            print(f"✅ FINAL RESULT: {len(following_list)} accounts found")
            print(f"{'='*60}")
            
            # Save the list to a text file for verification/debugging
            with open("following_list_debug.txt", "w") as f:
                # Write each username on its own line, sorted alphabetically
                for user in sorted(following_list):
                    f.write(f"{user}\n")
            print("📝 Saved to: following_list_debug.txt")
            
            # Close the modal by sending Escape key
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except:
                # If closing fails, that's okay - continue anyway
                pass
            
            # Return the list of usernames
            return following_list

        except Exception as e:
            # If any error occurs in the entire function, catch it here
            print(f"❌ ERROR: {e}")
            # Print the full error traceback for debugging
            import traceback
            traceback.print_exc()
            # Try to take a screenshot of the error state
            self.driver.save_screenshot("following_error_detailed.png")
            # Return an empty list since we failed
            return []

    def get_followers(self, username, max_followers=None):
        """Gets the list of accounts that follow a user - works exactly like get_following()"""
        # Print header
        print(f"\n{'='*60}")
        print(f"Getting followers for: {username}")
        print(f"{'='*60}")
        # Navigate to user's profile
        self.driver.get(f"https://www.instagram.com/{username}/")
        # Wait for page to load
        time.sleep(5)
        
        try:
            # Try to read the follower count from the profile
            try:
                followers_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/followers')]")
                expected_text = followers_elem.text
                print(f"🎯 Profile shows: {expected_text}")
            except:
                print("⚠️  Could not read follower count")
            
            # Wait for and click the followers button
            followers_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))
            )
            followers_btn.click()
            print("✓ Clicked followers button")
            # Wait for modal to load
            time.sleep(10)
            
            # Take screenshot for debugging
            self.driver.save_screenshot("followers_modal_structure.png")
            print("📸 Screenshot saved")
            
            # Find the scrollable container
            scroll_box = self._find_scroll_container()
            if not scroll_box:
                print("❌ CRITICAL: Cannot find scroll container!")
                return []
            
            # Initialize variables (same as get_following)
            followers_set = set()
            scroll_count = 0
            max_scrolls = 3000
            stale_count = 0
            
            print("\n🔄 Starting scroll process...")
            print("=" * 60)
            
            # Main scrolling loop (identical logic to get_following)
            while scroll_count < max_scrolls:
                # Extract all visible usernames
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and "instagram.com/" in href:
                                parts = href.split("instagram.com/")[-1].split("/")
                                if len(parts) > 0:
                                    potential_username = parts[0]
                                    if potential_username and not any(x in potential_username for x in 
                                        ['explore', 'direct', 'accounts', 'p', 'reels', 'tv', '?', '=']):
                                        if len(potential_username) > 0 and len(potential_username) < 31:
                                            followers_set.add(potential_username)
                        except:
                            continue
                except:
                    pass
                
                current_count = len(followers_set)
                
                # Multiple scroll methods
                try:
                    self.driver.execute_script("""
                        var dialog = document.querySelector('div[role="dialog"]');
                        if (dialog) {
                            var scrollable = dialog.querySelector('div[style*="overflow"]');
                            if (scrollable) {
                                scrollable.scrollTop = scrollable.scrollHeight;
                            }
                        }
                    """)
                except:
                    pass
                
                try:
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                except:
                    pass
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                time.sleep(2)
                
                # Check for progress
                new_count = len(followers_set)
                if new_count > current_count:
                    stale_count = 0
                    if scroll_count % 20 == 0:
                        print(f"📊 Scroll #{scroll_count}: Found {new_count} followers")
                else:
                    stale_count += 1
                
                # If stuck, try aggressive scrolling
                if stale_count >= 20:
                    print(f"\n⚠️  Stuck at {new_count} followers")
                    print("🔥 Final aggressive attempt...")
                    
                    for i in range(30):
                        self.driver.execute_script("""
                            var dialogs = document.querySelectorAll('div[role="dialog"]');
                            dialogs.forEach(function(dialog) {
                                var scrollables = dialog.querySelectorAll('div');
                                scrollables.forEach(function(s) {
                                    s.scrollTop = s.scrollHeight;
                                });
                            });
                        """)
                        self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.PAGE_DOWN)
                        time.sleep(0.5)
                    
                    time.sleep(3)
                    
                    # Extract one more time
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and "instagram.com/" in href:
                                parts = href.split("instagram.com/")[-1].split("/")
                                if len(parts) > 0:
                                    potential_username = parts[0]
                                    if potential_username and not any(x in potential_username for x in 
                                        ['explore', 'direct', 'accounts', 'p', 'reels', 'tv', '?', '=']):
                                        if len(potential_username) > 0 and len(potential_username) < 31:
                                            followers_set.add(potential_username)
                        except:
                            continue
                    
                    final_count = len(followers_set)
                    if final_count == new_count:
                        print(f"✓ Confirmed: Stuck at {final_count} followers")
                        print(f"⚠️  Instagram rate limiting detected")
                        break
                    else:
                        stale_count = 0
                
                scroll_count += 1
                
                if max_followers and len(followers_set) >= max_followers:
                    break
            
            # Convert set to list
            followers_list = list(followers_set)
            # Filter out non-usernames
            followers_list = [u for u in followers_list if u not in 
                ['', 'instagram', 'login', 'accounts', 'explore', 'direct']]
            
            # Print results
            print(f"\n{'='*60}")
            print(f"✅ FINAL RESULT: {len(followers_list)} followers found")
            print(f"{'='*60}")
            
            # Save to file
            with open("followers_list_debug.txt", "w") as f:
                for user in sorted(followers_list):
                    f.write(f"{user}\n")
            print("📝 Saved to: followers_list_debug.txt")
            
            # Close modal
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except:
                pass
            
            return followers_list
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("followers_error_detailed.png")
            return []

    def find_unfollowers(self, following_list, followers_list):
        """Find accounts you follow that don't follow you back"""
        # Use list comprehension to filter: for each person you follow, check if they're NOT in your followers
        return [u for u in following_list if u not in followers_list]

    def save_to_database(self, username, following_list, followers_list):
        """Save all the follower/following data to the SQLite database"""
        # Import SQLAlchemy - this is our database library
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Build the path to the database file
        db_path = os.path.join(os.path.dirname(__file__), 'instagram_tracker.db')
        # Create a database engine (connection to the database)
        engine = create_engine(f'sqlite:///{db_path}')
        # Create all tables if they don't exist (based on our models)
        Base.metadata.create_all(engine)
        # Create a session factory
        Session = sessionmaker(bind=engine)
        # Create a session (this is like opening a connection to the database)
        session = Session()

        try:
            # Check if this user already exists in the database
            existing_user = session.query(User).filter_by(insta_user=username).first()
            
            # If user doesn't exist, create them
            if not existing_user:
                new_user = User(
                    email=f"{username}@placeholder.com",  # Placeholder email
                    insta_user=username,
                    insta_password="encrypted_password",  # Placeholder password
                    is_active=True
                )
                # Add the new user to the session
                session.add(new_user)
                # Save the user to the database
                session.commit()
                # Update our variable to point to the new user
                existing_user = new_user
                print(f"✓ User {username} created")
            else:
                print(f"✓ User {username} exists")
            
            # Delete all old relationship records for this user (we'll replace with fresh data)
            session.query(FollowRelationship).filter_by(user_id=existing_user.id).delete()
            # Save the deletion
            session.commit()
            
            # Create a new relationship record for each account the user follows
            for username_followed in following_list:
                # Check if they follow you back (are they in your followers list?)
                they_follow_back = username_followed in followers_list
                # Create a relationship object
                relationship = FollowRelationship(
                    user_id=existing_user.id,  # Link to the user
                    instagram_user_id=username_followed,  # The account being followed
                    username=username_followed,
                    full_name="",  # We don't scrape this (yet)
                    profile_pic_url="",  # We don't scrape this (yet)
                    i_follow_them=True,  # Yes, you follow them (they're in your following list)
                    they_follow_me=they_follow_back  # True if they follow you back
                )
                # Add this relationship to the session
                session.add(relationship)
            
            # Save all relationships to the database at once (efficient!)
            session.commit()
            print(f"✓ Saved {len(following_list)} relationships to database")
        
        except Exception as e:
            # If anything goes wrong, print the error
            print(f"Database error: {e}")
            # Rollback (undo) any changes we made
            session.rollback()
        finally:
            # Always close the session when done (like closing a file)
            session.close()

    def print_database_summary(self, username):
        """Query the database and print a nice summary of follower stats"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Connect to the database
        db_path = os.path.join(os.path.dirname(__file__), 'instagram_tracker.db')
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            # Find the user in the database
            user = session.query(User).filter_by(insta_user=username).first()
            if not user:
                print("User not found")
                return
            
            # Get all relationships for this user
            relationships = session.query(FollowRelationship).filter_by(user_id=user.id).all()
            
            # Filter relationships into categories using list comprehensions
            # following = accounts where i_follow_them is True
            following = [r for r in relationships if r.i_follow_them]
            # mutual = accounts where both i_follow_them AND they_follow_me are True
            mutual = [r for r in relationships if r.i_follow_them and r.they_follow_me]
            # not_following_back = accounts where you follow them but they don't follow you
            not_following_back = [r for r in relationships if r.i_follow_them and not r.they_follow_me]
            
            # Print a nice formatted summary
            print("\n" + "="*60)
            print(f"📊 INSTAGRAM STATS FOR @{username}")
            print("="*60)
            print(f"You follow:           {len(following)} accounts")
            print(f"Follow you back:      {len(mutual)} accounts")
            print(f"Don't follow back:    {len(not_following_back)} accounts")
            print("="*60)
            
            # If there are accounts not following back, list them
            if not_following_back:
                print(f"\n❌ ACCOUNTS NOT FOLLOWING YOU BACK ({len(not_following_back)}):")
                # Show first 50 accounts
                for r in not_following_back[:50]:
                    print(f"   • @{r.username}")
                # If there are more than 50, show a summary
                if len(not_following_back) > 50:
                    print(f"   ... and {len(not_following_back) - 50} more")
            
            print("\n" + "="*60)
            
        except Exception as e:
            # If any error occurs, print it
            print(f"Error: {e}")
        finally:
            # Always close the database session
            session.close()

# This code runs when you execute the script directly (not when importing it)
if __name__ == "__main__":
    # Create a new InstagramScraper object
    scraper = InstagramScraper()
    
    # Log into Instagram with your credentials
    scraper.login("roriforrealzz", "Godisgood123!")
    
    # Check if login was successful
    if not scraper.is_logged_in:
        print("Login failed!")
        # Close the browser
        scraper.driver.quit()
        # Exit the program
        exit()
    
    # Get the list of accounts you're following
    following = scraper.get_following("roriforrealzz")
    # Get the list of accounts that follow you
    followers = scraper.get_followers("roriforrealzz")
    
    # Find who doesn't follow you back
    unfollowers = scraper.find_unfollowers(following, followers)
    print(f"\n🚨 {len(unfollowers)} people don't follow you back")
    
    # Save all the data to the database
    scraper.save_to_database("roriforrealzz", following, followers)
    # Print a summary from the database
    scraper.print_database_summary("roriforrealzz")
    
    # Print warning about Instagram rate limiting
    print("\n⚠️  NOTE: Instagram heavily rate-limits scrapers.")
    print("If you only got 12 accounts, Instagram is blocking the modal from loading.")
    print("Try again in a few hours or from a different IP address.")
    
    # Wait for user to press Enter before closing
    input("\nPress Enter to close...")
    # Close the browser
    scraper.driver.quit()