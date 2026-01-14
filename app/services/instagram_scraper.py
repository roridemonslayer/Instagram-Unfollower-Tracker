from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User, FollowRelationship, Base
import time

class InstagramScraper: 
    def __init__(self):
        from selenium.webdriver.chrome.options import Options
        
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
        print(f"Attempting to login as {username}")
        self.driver.get("https://www.instagram.com/accounts/login/")
        
        try:
            username_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(username)

            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)

            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            time.sleep(10)
            
            # Dismiss popups
            try:
                not_now_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                not_now_button.click()
                time.sleep(2)
            except:
                pass
            
            try:
                not_now_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]")
                not_now_button.click()
                time.sleep(2)
            except:
                pass
            
            if "accounts/login" not in self.driver.current_url:
                print("✓ Login successful")
                self.is_logged_in = True
            else:
                print("✗ Login failed")
                self.is_logged_in = False
                
        except Exception as e:
            print(f"Error during login: {e}")
            self.is_logged_in = False

    def _find_scroll_container(self):
        """Try multiple ways to find the scrollable container"""
        selectors = [
            "//div[@role='dialog']//div[contains(@style, 'overflow')]",
            "//div[@role='dialog']//div[@class and contains(@class, '_aano')]",
            "//div[@role='dialog']//div[contains(@class, 'isgrP')]",
            "//div[@role='dialog']",
            "//div[contains(@class, 'x1n2onr6')]",
            "//div[contains(@class, '_aano')]"
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                print(f"✓ Found container with selector: {selector}")
                return element
            except:
                continue
        
        print("❌ Could not find scroll container with any selector!")
        return None

    def get_following(self, username, max_following=None):
        """Gets following list - NEW APPROACH"""
        print(f"\n{'='*60}")
        print(f"Getting following list for: {username}")
        print(f"{'='*60}")
        self.driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(5)

        try:
            # Get expected count
            try:
                following_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/following')]")
                expected_text = following_elem.text
                print(f"🎯 Profile shows: {expected_text}")
            except:
                print("⚠️  Could not read following count")
            
            # Click following button
            following = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/following')]"))
            )
            following.click()
            print("✓ Clicked following button")
            time.sleep(10)  # Longer wait
            
            # Take screenshot to see what we're working with
            self.driver.save_screenshot("following_modal_structure.png")
            print("📸 Screenshot saved")
            
            # Try to find the scroll container
            scroll_box = self._find_scroll_container()
            if not scroll_box:
                print("❌ CRITICAL: Cannot find scroll container!")
                return []
            
            # Get all usernames using multiple methods
            following_set = set()
            scroll_count = 0
            max_scrolls = 3000
            stale_count = 0
            
            print("\n🔄 Starting scroll process...")
            print("=" * 60)
            
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while scroll_count < max_scrolls:
                # METHOD 1: Find all profile links
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            href = link.get_attribute("href")
                            if href and "instagram.com/" in href:
                                # Extract username from URL
                                parts = href.split("instagram.com/")[-1].split("/")
                                if len(parts) > 0:
                                    potential_username = parts[0]
                                    # Filter out non-usernames
                                    if potential_username and not any(x in potential_username for x in 
                                        ['explore', 'direct', 'accounts', 'p', 'reels', 'tv', '?', '=']):
                                        if len(potential_username) > 0 and len(potential_username) < 31:
                                            following_set.add(potential_username)
                        except:
                            continue
                except Exception as e:
                    print(f"Error in extraction: {e}")
                
                current_count = len(following_set)
                
                # SCROLL METHOD 1: Scroll the dialog
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
                
                # SCROLL METHOD 2: Send Page Down key
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.PAGE_DOWN)
                except:
                    pass
                
                # SCROLL METHOD 3: JavaScript scroll
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                time.sleep(2)  # Wait for content to load
                
                # Check progress
                new_count = len(following_set)
                if new_count > current_count:
                    stale_count = 0
                    if scroll_count % 20 == 0:
                        print(f"📊 Scroll #{scroll_count}: Found {new_count} accounts")
                else:
                    stale_count += 1
                
                # Check if we're stuck
                if stale_count >= 20:
                    print(f"\n⚠️  Stuck at {new_count} accounts after 20 attempts")
                    
                    # AGGRESSIVE FINAL ATTEMPT
                    print("🔥 Trying aggressive final scroll...")
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
                                            following_set.add(potential_username)
                        except:
                            continue
                    
                    final_count = len(following_set)
                    if final_count == new_count:
                        print(f"✓ Confirmed: Cannot get more than {final_count} accounts")
                        print(f"⚠️  Instagram is blocking us - this is a rate limit issue")
                        break
                    else:
                        print(f"✓ Got {final_count - new_count} more! Continuing...")
                        stale_count = 0
                
                scroll_count += 1
                
                if max_following and len(following_set) >= max_following:
                    break
            
            following_list = list(following_set)
            
            # Filter out common non-usernames
            following_list = [u for u in following_list if u not in 
                ['', 'instagram', 'login', 'accounts', 'explore', 'direct']]
            
            print(f"\n{'='*60}")
            print(f"✅ FINAL RESULT: {len(following_list)} accounts found")
            print(f"{'='*60}")
            
            # Save to file
            with open("following_list_debug.txt", "w") as f:
                for user in sorted(following_list):
                    f.write(f"{user}\n")
            print("📝 Saved to: following_list_debug.txt")
            
            # Close modal
            try:
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            except:
                pass
            
            return following_list

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            self.driver.save_screenshot("following_error_detailed.png")
            return []

    def get_followers(self, username, max_followers=None):
        """Gets followers - NEW APPROACH"""
        print(f"\n{'='*60}")
        print(f"Getting followers for: {username}")
        print(f"{'='*60}")
        self.driver.get(f"https://www.instagram.com/{username}/")
        time.sleep(5)
        
        try:
            # Get expected count
            try:
                followers_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/followers')]")
                expected_text = followers_elem.text
                print(f"🎯 Profile shows: {expected_text}")
            except:
                print("⚠️  Could not read follower count")
            
            # Click followers
            followers_btn = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/followers')]"))
            )
            followers_btn.click()
            print("✓ Clicked followers button")
            time.sleep(10)
            
            self.driver.save_screenshot("followers_modal_structure.png")
            print("📸 Screenshot saved")
            
            scroll_box = self._find_scroll_container()
            if not scroll_box:
                print("❌ CRITICAL: Cannot find scroll container!")
                return []
            
            followers_set = set()
            scroll_count = 0
            max_scrolls = 3000
            stale_count = 0
            
            print("\n🔄 Starting scroll process...")
            print("=" * 60)
            
            while scroll_count < max_scrolls:
                # Extract all usernames
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
                
                new_count = len(followers_set)
                if new_count > current_count:
                    stale_count = 0
                    if scroll_count % 20 == 0:
                        print(f"📊 Scroll #{scroll_count}: Found {new_count} followers")
                else:
                    stale_count += 1
                
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
            
            followers_list = list(followers_set)
            followers_list = [u for u in followers_list if u not in 
                ['', 'instagram', 'login', 'accounts', 'explore', 'direct']]
            
            print(f"\n{'='*60}")
            print(f"✅ FINAL RESULT: {len(followers_list)} followers found")
            print(f"{'='*60}")
            
            with open("followers_list_debug.txt", "w") as f:
                for user in sorted(followers_list):
                    f.write(f"{user}\n")
            print("📝 Saved to: followers_list_debug.txt")
            
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
        return [u for u in following_list if u not in followers_list]

    def save_to_database(self, username, following_list, followers_list):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        db_path = os.path.join(os.path.dirname(__file__), 'instagram_tracker.db')
        engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        try:
            existing_user = session.query(User).filter_by(insta_user=username).first()
            
            if not existing_user:
                new_user = User(
                    email=f"{username}@placeholder.com",
                    insta_user=username,
                    insta_password="encrypted_password",
                    is_active=True
                )
                session.add(new_user)
                session.commit()
                existing_user = new_user
                print(f"✓ User {username} created")
            else:
                print(f"✓ User {username} exists")
            
            session.query(FollowRelationship).filter_by(user_id=existing_user.id).delete()
            session.commit()
            
            for username_followed in following_list:
                they_follow_back = username_followed in followers_list
                relationship = FollowRelationship(
                    user_id=existing_user.id,
                    instagram_user_id=username_followed,
                    username=username_followed,
                    full_name="",
                    profile_pic_url="",
                    i_follow_them=True,
                    they_follow_me=they_follow_back
                )
                session.add(relationship)
            
            session.commit()
            print(f"✓ Saved {len(following_list)} relationships to database")
        
        except Exception as e:
            print(f"Database error: {e}")
            session.rollback()
        finally:
            session.close()

    def print_database_summary(self, username):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        db_path = os.path.join(os.path.dirname(__file__), 'instagram_tracker.db')
        engine = create_engine(f'sqlite:///{db_path}')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            user = session.query(User).filter_by(insta_user=username).first()
            if not user:
                print("User not found")
                return
            
            relationships = session.query(FollowRelationship).filter_by(user_id=user.id).all()
            
            following = [r for r in relationships if r.i_follow_them]
            mutual = [r for r in relationships if r.i_follow_them and r.they_follow_me]
            not_following_back = [r for r in relationships if r.i_follow_them and not r.they_follow_me]
            
            print("\n" + "="*60)
            print(f"📊 INSTAGRAM STATS FOR @{username}")
            print("="*60)
            print(f"You follow:           {len(following)} accounts")
            print(f"Follow you back:      {len(mutual)} accounts")
            print(f"Don't follow back:    {len(not_following_back)} accounts")
            print("="*60)
            
            if not_following_back:
                print(f"\n❌ ACCOUNTS NOT FOLLOWING YOU BACK ({len(not_following_back)}):")
                for r in not_following_back[:50]:
                    print(f"   • @{r.username}")
                if len(not_following_back) > 50:
                    print(f"   ... and {len(not_following_back) - 50} more")
            
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            session.close()

if __name__ == "__main__":
    scraper = InstagramScraper()
    
    scraper.login("roriforrealzz", "Godisgood123!")
    
    if not scraper.is_logged_in:
        print("Login failed!")
        scraper.driver.quit()
        exit()
    
    following = scraper.get_following("roriforrealzz")
    followers = scraper.get_followers("roriforrealzz")
    
    unfollowers = scraper.find_unfollowers(following, followers)
    print(f"\n🚨 {len(unfollowers)} people don't follow you back")
    
    scraper.save_to_database("roriforrealzz", following, followers)
    scraper.print_database_summary("roriforrealzz")
    
    print("\n⚠️  NOTE: Instagram heavily rate-limits scrapers.")
    print("If you only got 12 accounts, Instagram is blocking the modal from loading.")
    print("Try again in a few hours or from a different IP address.")
    
    input("\nPress Enter to close...")
    scraper.driver.quit()