from selenium import webdriver #we're going to use selenium as an automator here that way insta doesn't detect us as a bot
from selenium.webdriver.common.by import By 
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
import time
class InstagramScraper: 
    def __init__(self):
        #t6jtis creates a session to keep cookies (data) between sessions
        #and to make requests   
        self.driver = webdriver.Chrome()
        self.is_logged_in = False #this js like ios saying the user hasn't logged in
    def login(self, username, password):
        print(f"trying to login as {username}")
        #we use self.session.get to keep cookies between requests. 
        self.driver.get("https://www.instagram.com/accounts/login/")
        
   

        try:
            username_input = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "username" ))
            )
            username_input.send_keys(username) #this types the username

            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)

            #next it needs to the the login vbutton to click 
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            #wait for the login to compelete
            WebDriverWait(self.diver, 15).until(
                EC.url_change("https://www.instagram.com/accounts/login/")
            )

            #this then checks if we're logged in by looking at the url 
            if "accounts/login" not in self.driver.current_url:
                print("login works")
                self.is_logged_in = True
            else:
                print("login failed- recheck user/pass")
                self.is_logged_in = True 
        except Exception as e:
            print(f"Error During login: {e}")
            self.is_logged_in = False

if __name__ == "__main__":
    scraper = InstagramScraper()
    scraper.login("USERNAME","PASSWORD")
    input("Press Enter to close browser...")
    scraper.driver.quit()