import requests


class Tenor:
    def __init__(self, api_key):
        self.api_key = api_key

    def search(self, query, per_page=None):
        url = f"https://api.tenor.com/v1/search?q={query}&key={self.api_key}"
        if per_page is not None:
            url = f'{url}&limit={per_page}'
        result = requests.get(url)
        return result.json()
