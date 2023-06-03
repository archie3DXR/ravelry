#!/usr/bin/env python3


from dotenv import load_dotenv
import argparse
import requests
import os
import json
import sqlite3
load_dotenv()


def setup_database():
    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()


def setup_database():
    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()

    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS yarns (
            id INTEGER PRIMARY KEY,
            name TEXT,
            brand TEXT,
            weight_grams FLOAT,
            weight_lbs FLOAT,
            length_meters FLOAT,
            length_yards FLOAT,
            weight_per_unit_length FLOAT
        )
    """)
    conn.commit()
    conn.close()


# create function to fetchpage with authentication


def fetch_rav(query):
    ravelry_user = os.getenv('RAVELRY_USER')
    ravelry_password = os.getenv('RAVELRY_PASSWORD')
    url = f"https://api.ravelry.com/yarns/search.json?query={query}"
    auth = (ravelry_user, ravelry_password)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()  # Check for any request errors
        data = response.json()

        # Connect to the database
        conn = sqlite3.connect('yarn_db.sqlite')
        cursor = conn.cursor()

        # Insert the data into the database
        for yarn in data['yarns']:
            cursor.execute("""
                INSERT INTO yarns (name, brand, weight_grams, weight_lbs, length_meters, length_yards, weight_per_unit_length)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (yarn['name'], yarn['brand'], yarn['weight']['grams'], yarn['weight']['lbs'], yarn['length']['meters'], yarn['length']['yards'], yarn['weight_per_unit_length']))

        conn.commit()
        conn.close()

        return data
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None


# run fetch_webpage and print as json output
# added args parser to handle arguments from cmd line
# tool is search and query is search term for now

if __name__ == "__main__":
    setup_database()

    # The rest of your code...

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch data from Ravelry API")
    parser.add_argument("-tool", type=str,
                        help="The tool to use", required=False)
    parser.add_argument("-query", type=str,
                        help="The query to search", required=False)

    args = parser.parse_args()

    # fetch ravelry data as json
    data = fetch_rav(args.query)
    print(json.dumps(data, indent=4))

# if data is not None:
#     print(json.dumps(data, indent=4))


# 01.json is a saved json output from | jq > 01.json
