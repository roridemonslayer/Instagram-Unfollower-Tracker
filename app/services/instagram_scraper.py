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
#what this is doing is looking for security token in HTML looking for csrf
        if "csrf" in page_content: 
            print("found it")
            csrf_start = page_content.find("csrf")
            print("it appears around:" , csrf_start)
            print(page_content[csrf_start-50:csrf_start+150])
        
        else:
            print("No CSRF token found")
            print(page_content[:2000]) #prints the firtst 500 characters of whats there.
        #the made point is to the extract the token value from this pattern
    #find where the csrf_token starts 
    
        start_text = '"csrf_token":"' #what this is doing is finding where the csrf token exfsists in ur html 
        start_pos = page_content.find(start_text)
        #then we calcualte where the token starts at 
        token_start = start_pos + len(start_text)
        token_end = page_content.find( '"', token_start)
        token = page_content[token_start : token_end]
        #extract token value
       

        print(f" Extracted token : {token}")

         #extract login data like the password, username, and token
        login_data = {
            'username' : username, 
            'password' : password, 
            'csrfmiddlewaretoken' : token
        } 
        #this is jsut for succesful authenrication to precent cross site request. 
        headers = {
            'X-CSRFToken' : token, #this is telling insta like here is the secrutiy token you gave me and it matches it with the login page. also for preveting CSRF attacks
            'X-Requested-With' : 'XMLHttpRequest', #tellis insta this is an AJAZ request from javsscript. insta knows to send bac the JSON instead of ht,l to make the request look like it came from a real browser
            'Referer' : "https://www.instagram.com/accounts/login/", #this indicates the URL of yhe page thats intitaitn the requests
            'Content-Type' : "application/x-www-form-urlencoded" #this is statign the type of data beign sent, tells insta im sending form data, 
        }
        login_response = self.session.post(
            'https://www.instagram.com/accounts/login/ajax/'
        )



if __name__ == "__main__":
    scraper = InstagramScraper()
    scraper.login("test_username", "test_password")