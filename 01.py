#!/usr/bin/env python3


##create function tofetchpage with authentication
from dotenv import load_dotenv
import argparse
import requests
import os
import json

load_dotenv()


def fetch_rav(tool, query):
    ravelry_user = os.getenv('RAVELRY_USER')
    ravelry_password = os.getenv('RAVELRY_PASSWORD')
    url = f"https://api.ravelry.com/projects/{tool}.json?query={query}"
    auth = (ravelry_user, ravelry_password)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()  # Check for any request errors
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None

###run fetch_webpage and print as json output
## added args parser to handle arguments from cmd line
## tool is search and query is search term for now

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch data from Ravelry API")
    parser.add_argument("-tool", type=str, help="The tool to use", required=False)
    parser.add_argument("-query", type=str, help="The query to search", required=False)

    args = parser.parse_args()

    data = fetch_rav(args.tool, args.query)

    if data is not None:
        print(json.dumps(data, indent=4))



### 01.json is a saved json output from | jq > 01.json
