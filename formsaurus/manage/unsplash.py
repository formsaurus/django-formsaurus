import requests

class Unsplash:
    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
    
    def search(self, query, page=None, per_page=None):
        url = f'https://api.unsplash.com/search/photos?query={query}&client_id={self.access_key}'
        if per_page is not None:
            url = f'{url}&per_page={per_page}'
        if page is not None:
            url = f'{url}&page={page}'
        result = requests.get(url)
        return result.json()