import requests #using this to get HTTP requests to post, get etc our data
class InstagramScraper: 
    def __init__(self):
        #t6jtis creates a session to keep cookies (data) between sessions     
        self.session = requests.Session()
        
