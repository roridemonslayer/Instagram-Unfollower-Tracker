import requests #using this to get HTTP requests to post, get etc our data
class InstagramScraper: 
    def __init__(self):
        #t6jtis creates a session to keep cookies (data) between sessions
        #and to make requests   
        self.session = requests.Session()
        self.is_logged_in = False #this js like ios saying the user hasn't logged in
    def login(self, username, password):
        print(f"trying to login as {username}")
        #we use self.session.get to keep cookies between requests. 
        login_information = self.session.get("https://www.instagram.com/accounts/login/")

#how do i check if a request was succesfull
 #what are http status codes?
 #how i access the status cdoe form my request 
        if login_information.status_code== 200:
            #so if it runs and the session wroks to get the user info we get 200 and return True
            print("It works")
            page_content = login_information.text #this is being used to get the HTML token cotent
            #csrf is cross-site-requestt-forgery-protetction . it stops hackers fromjust trying mutliple insta users and passwords to get into the website 
            #they'd need to make it much harder for hackers

        if "csrf" in page_content: 
            print("found it")
            csrf_start = page_content.find("csrf")
            print("it appears around:" , csrf_start)
            print(page_content[csrf_start-50:csrf_start+150])
        else:
            print("No CSRF token found")
            print(page_content[:2000]) #prints the firtst 500 characters of whats there.
            


if __name__ == "__main__":
    scraper = InstagramScraper()
    scraper.login("test_username", "test_password")