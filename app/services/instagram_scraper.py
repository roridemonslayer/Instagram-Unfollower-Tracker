import requests #using this to get HTTP requests to post, get etc our data
class InstagramScraper: 
    def __init__(self):
        #t6jtis creates a session to keep cookies (data) between sessions     
        self.session = requests.Session()

        self.session.headers.update({
            'Uset-Agent' :  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.is_logged_in = False

