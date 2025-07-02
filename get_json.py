import requests
import json

url = "https://jsonplaceholder.typicode.com/todos/1"

try:
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    print(json.dumps(data, indent=4))
except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")
except json.JSONDecodeError:
    print("Error decoding JSON response.")