#!/usr/bin/env python3

from dotenv import load_dotenv
import argparse
import requests
import os
import json
import sqlite3

load_dotenv()

# Setting up the database


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

# Fetch yarn with search query


def fetch_rav(query):
    ravelry_user = os.getenv('RAVELRY_USER')
    ravelry_password = os.getenv('RAVELRY_PASSWORD')
    url = f"https://api.ravelry.com/yarns/search.json?query={query}"
    auth = (ravelry_user, ravelry_password)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()  # Check for any request errors
        data = response.json()
        return data["yarns"][:10]  # Return only the first 10 results
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None

# Fetch yarn by ID


def fetch_yarn_by_id(id):
    ravelry_user = os.getenv('RAVELRY_USER')
    ravelry_password = os.getenv('RAVELRY_PASSWORD')
    url = f"https://api.ravelry.com/yarns/{id}.json"
    auth = (ravelry_user, ravelry_password)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None

# Process yarn data


def process_yarn_data(yarn_data):
    yarn_attributes = []

    yarn = yarn_data["yarn"]

    yarn_id = yarn["id"]
    name = yarn["name"]
    weight = yarn["grams"]
    yardage = yarn["yardage"]
    company_name = yarn["yarn_company"]["name"]

    # Append the extracted attributes as a tuple
    yarn_attributes.append((yarn_id, name, company_name, weight,
                           weight * 0.00220462, yardage * 0.9144, yardage, weight / (yardage * 0.9144)))

    return yarn_attributes


# Parse arguments and fetch data
if __name__ == "__main__":
    setup_database()

    parser = argparse.ArgumentParser(description="Fetch data from Ravelry API")
    parser.add_argument("-query", type=str,
                        help="The query to search", required=False)
    parser.add_argument("-id", type=int, help="The yarn id", required=False)

    args = parser.parse_args()

    if args.query:

        data = fetch_rav(args.query)
        if data is not None:
            for yarn in data:  # Loop through each yarn in the data
                print(
                    f"Yarn ID: {yarn['id']} | {yarn['yarn_company_name']} - {yarn['name']}")

        else:
            print("No yarns found.")

    if args.id:
        yarn_data = fetch_yarn_by_id(args.id)
        if yarn_data is not None:
            yarn_attributes = process_yarn_data(yarn_data)

            # Connect to the database
            conn = sqlite3.connect('yarn_db.sqlite')
            cursor = conn.cursor()

            # Insert into the table
            for yarn_attr in yarn_attributes:
                cursor.execute(
                    "SELECT COUNT(*) FROM yarns WHERE id = ?", (yarn_attr[0],)
                )
                if cursor.fetchone()[0] > 0:
                    cursor.execute(
                        "UPDATE yarns SET name = ?, brand = ?, weight_grams = ?, weight_lbs = ?, length_meters = ?, length_yards = ?, weight_per_unit_length = ? WHERE id = ?",
                        (yarn_attr[1], yarn_attr[2], yarn_attr[3], yarn_attr[4], yarn_attr[5], yarn_attr[6], yarn_attr[7], yarn_attr[0]))
                else:
                    cursor.execute(
                        "INSERT INTO yarns (id, name, brand, weight_grams, weight_lbs, length_meters, length_yards, weight_per_unit_length) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        yarn_attr)

            conn.commit()
            conn.close()
