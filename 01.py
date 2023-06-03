#!/usr/bin/env python3


##create function tofetchpage with authentication
from dotenv import load_dotenv
import sys
import argparse
import requests
import json
import sqlite3
import os

load_dotenv()


ravelry_user = os.getenv('RAVELRY_USER')
ravelry_password = os.getenv('RAVELRY_PASSWORD')

def fetch_rav(tool, query):
    url = f"https://api.ravelry.com/projects/{tool}.json?query={query}"
    auth = (
        os.getenv('RAVELRY_USER'),
        os.getenv('RAVELRY_PASSWORD')
    )
    response = requests.get(url, auth=auth)
    data = response.json()

    return data


###run fetch_webpage and print as json output
## added args parser to handle arguments from cmd line
## tool is search and query is search term for now

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Greet the specified person")
    parser.add_argument("-tool", type=str, help="The person to greet", required=False)
    parser.add_argument(
        "-query", type=str, help="The age of the person", required=False
    )

    args = parser.parse_args()

    # fetch ravelry data as json
    data = fetch_rav(args.tool, args.query)

    print(data["projects"][0]["tag_names"])


### 01.json is a saved json output from | jq > 01.json
