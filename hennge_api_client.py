import requests
import base64
import csv
import io
import requests

class HenngeApiClient:
    def __init__(self, client_id, client_secret):
        self.auth_endpoint = "https://ap.ssso.hdems.com/oauth/token"
        self.api_endpoint = "https://api.auth.hennge.com"
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def _get_access_token(self):
        if self.access_token:
            return self.access_token
        basic_credentials = f"{self.client_id}:{self.client_secret}"
        basic_credentials_encoded = base64.b64encode(basic_credentials.encode()).decode()

        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'authorization': f'Basic {basic_credentials_encoded}'
        }
        data = {
            'grant_type': 'client_credentials'
        }

        response = requests.post(self.auth_endpoint, headers=headers, data=data)

        if response.status_code == 200:
            self.access_token = response.json().get('access_token')
            return self.access_token
        else:
            raise Exception(f"Failed to obtain access token: {response.status_code} {response.text}")
        
    def _make_api_request(self, endpoint, method='get', post_data=None):
        if post_data is None:
            post_data = {}
        url = f"{self.api_endpoint}{endpoint}"
        print(f"{url}")
        headers = {
            'Authorization': f"Bearer {self._get_access_token()}",
        }

        if method.lower() in ['post', 'put', 'patch'] and post_data:
            response = requests.request(method, url, headers=headers, json=post_data)
        else:
            response = requests.request(method, url, headers=headers)
        if response.status_code in [200, 201]:
            if 'application/json' in response.headers.get('Content-Type', ''):
                return {
                    'content': response.json(),
                    'headers': response.headers
                }
            else:
                return {
                    'content': None,
                    'headers': response.headers
                }
        elif response.status_code == 401:
            print("INVALID TOKEN")
            return None
        elif response.status_code == 404:
            print("404 Not Found")
            return None
        else:
            response.raise_for_status()
    
    def _paginate_through(self, endpoint, method='get', post_data=None):
        if post_data is None:
            post_data = {}
        results = []
        cursor = None
        while True:
            if cursor:
                cursor_param = f"cursor={cursor}"
                url = f"{endpoint}&{cursor_param}" if '?' in endpoint else f"{endpoint}?{cursor_param}"
            else:
                url = endpoint
            if method.lower() == 'get':
                response = self._make_api_request(url)
            else:
                response = self._make_api_request(url, method, post_data)
            if not response:
                break
            cursor = response['content'].get('cursor')
            items = response['content'].get('items', [])
            results.extend(items)
            if not cursor:
                break
            print(results)
        return results

    def get_members(self):
        results = self._paginate_through('/20230822/users', 'get')
        if not results:
            return []
        return results

    # def get_members(self):
    #     endpoint = f"{self.api_endpoint}/20230822/users/download/csv"
    #     headers = {
    #         'Accept': 'application/json',
    #         'Authorization': f'Bearer {self._get_access_token()}'
    #     }
    #     response = requests.get(endpoint, headers=headers)

    #     if response.status_code != 200:
    #         print(f"Failed to download CSV: {response.status_code}")
    #         return []

    #     csv_content = response.content.decode('utf-8')
    #     csv_reader = csv.DictReader(io.StringIO(csv_content))
    #     users = [row for row in csv_reader]
    #     return users