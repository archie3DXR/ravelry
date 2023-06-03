#!/usr/bin/env python3
import click
from dotenv import load_dotenv
import requests
import os
import json
import sqlite3
from prettytable import PrettyTable

load_dotenv()


def setup_database():
    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS yarns (
            id INTEGER PRIMARY KEY,
            name TEXT,
            brand TEXT,
            weight_grams FLOAT,
            length_meters FLOAT,
            length_yards FLOAT,
            weight_per_unit_length FLOAT
        )
    """)
    conn.commit()
    conn.close()


def fetch_rav(query):
    ravelry_user = os.getenv('RAVELRY_USER')
    ravelry_password = os.getenv('RAVELRY_PASSWORD')
    url = f"https://api.ravelry.com/yarns/search.json?query={query}"
    auth = (ravelry_user, ravelry_password)

    try:
        response = requests.get(url, auth=auth)
        response.raise_for_status()
        data = response.json()
        return data["yarns"][:10]
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return None


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


def process_yarn_data(yarn_data):
    yarn_attributes = []

    yarn = yarn_data["yarn"]

    yarn_id = yarn["id"]
    name = yarn["name"]
    weight = yarn["grams"]
    yardage = yarn["yardage"]
    company_name = yarn["yarn_company"]["name"]

    yarn_attributes.append((yarn_id,
                            name,
                            company_name,
                            round(weight, 2),
                            round(yardage * 0.9144, 2),
                            round(yardage, 2),
                            round(weight / (yardage * 0.9144), 2)))

    return yarn_attributes


def view_database():
    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM yarns")

    rows = cursor.fetchall()

    table = PrettyTable()
    table.field_names = ["id", "name", "brand", "weight_grams",
                         "length_meters", "length_yards", "weight_per_unit_length"]

    for row in rows:
        table.add_row(row)

    print(table)

    conn.close()


@click.group()
def cli():
    pass


@cli.command()
def search():
    query = click.prompt("Enter your search query")
    data = fetch_rav(query)
    if data is not None:
        for i, yarn in enumerate(data):
            print(
                f"{i+1}. Yarn ID: {yarn['id']} | {yarn['yarn_company_name']} - {yarn['name']}")

        selection = click.prompt("\nSelect the yarn number", type=int)
        yarn_id = data[selection - 1]['id']

        yarn_data = fetch_yarn_by_id(yarn_id)
        if yarn_data is not None:
            yarn_attributes = process_yarn_data(yarn_data)

            conn = sqlite3.connect('yarn_db.sqlite')
            cursor = conn.cursor()

            for yarn_attr in yarn_attributes:
                cursor.execute(
                    "SELECT COUNT(*) FROM yarns WHERE id = ?", (yarn_attr[0],)
                )
                if cursor.fetchone()[0] > 0:
                    cursor.execute(
                        "UPDATE yarns SET name = ?, brand = ?, weight_grams = ?, length_meters = ?, length_yards = ?, weight_per_unit_length = ? WHERE id = ?",
                        (yarn_attr[1], yarn_attr[2], yarn_attr[3], yarn_attr[4], yarn_attr[5], yarn_attr[6], yarn_attr[0]))
                else:
                    cursor.execute(
                        "INSERT INTO yarns (id, name, brand, weight_grams, length_meters, length_yards, weight_per_unit_length) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        yarn_attr)

            conn.commit()
            conn.close()


@cli.command()
def view():
    view_database()


@cli.command()
def delete():
    view_database()  # Display the existing records
    yarn_id = click.prompt("Enter the yarn id to delete", type=int)

    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM yarns WHERE id = ?", (yarn_id,)
    )
    conn.commit()

    print(f"Deleted yarn with ID: {yarn_id}")
    conn.close()


if __name__ == "__main__":
    setup_database()
    cli()


# ________Not Inc_________________________________


@cli.command()
def add():
    yarn_id = click.prompt("Enter the yarn id", type=int)
    yarn_data = fetch_yarn_by_id(yarn_id)
    if yarn_data is not None:
        yarn_attributes = process_yarn_data(yarn_data)

        conn = sqlite3.connect('yarn_db.sqlite')
        cursor = conn.cursor()

        for yarn_attr in yarn_attributes:
            cursor.execute(
                "SELECT COUNT(*) FROM yarns WHERE id = ?", (yarn_attr[0],)
            )
            if cursor.fetchone()[0] > 0:
                cursor.execute(
                    "UPDATE yarns SET name = ?, brand = ?, weight_grams = ?, length_meters = ?, length_yards = ?, weight_per_unit_length = ? WHERE id = ?",
                    (yarn_attr[1], yarn_attr[2], yarn_attr[3], yarn_attr[4], yarn_attr[5], yarn_attr[6], yarn_attr[0]))
            else:
                cursor.execute(
                    "INSERT INTO yarns (id, name, brand, weight_grams, length_meters, length_yards, weight_per_unit_length) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    yarn_attr)

        conn.commit()
        conn.close()
