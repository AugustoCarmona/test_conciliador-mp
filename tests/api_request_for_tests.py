import requests

def get_single_pay(api_url, payment):
    api_url = f'{api_url}{payment}'
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()['results'][0]
