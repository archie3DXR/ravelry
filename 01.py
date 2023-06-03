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
            brand TEXT,
            name TEXT,
            colorway TEXT,
            weight_grams FLOAT,
            length_meters FLOAT,
            length_yards FLOAT,
            weight_per_unit_length FLOAT,
            num_skeins FLOAT,
            total_meterage FLOAT
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


def process_yarn_data(yarn_data, num_skeins):
    yarn_attributes = []

    yarn = yarn_data["yarn"]

    yarn_id = yarn["id"]
    name = yarn["name"]
    weight = yarn["grams"]
    yardage = yarn["yardage"]
    company_name = yarn["yarn_company"]["name"]
    total_meterage = num_skeins * round(yardage * 0.9144, 0)

    yarn_attributes.append((yarn_id, name, company_name, colorway, round(weight, 0), round(yardage * 0.9144, 0),
                            round(yardage, 0), round(weight / (yardage * 0.9144), 0), round(num_skeins, 2), round(total_meterage, 0)))

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
        for i, yarn in enumerate(data[:15]):  # Display only the top 15 results
            print(
                f"{i+1}. Yarn ID: {yarn['id']} | {yarn['yarn_company_name']} - {yarn['name']}")


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


@cli.command()
def add():
    query = click.prompt("Enter your search query")
    data = fetch_rav(query)
    if data is not None:
        for i, yarn in enumerate(data):
            print(
                f"{i+1}. Yarn ID: {yarn['id']} | {yarn['yarn_company_name']} - {yarn['name']}")

        selection = click.prompt("\nSelect the yarn number", type=int)
        yarn_id = data[selection - 1]['id']

        num_skeins = click.prompt("Enter the number of skeins", type=float)
        # new prompt for colorway
        colorway = click.prompt("Enter the colorway of the yarn", type=str)
        yarn_data = fetch_yarn_by_id(yarn_id)
        if yarn_data is not None:
            yarn_attributes = process_yarn_data(
                yarn_data, num_skeins, colorway)

            conn = sqlite3.connect('yarn_db.sqlite')
            cursor = conn.cursor()

            for yarn_attr in yarn_attributes:
                cursor.execute(
                    "SELECT COUNT(*) FROM yarns WHERE id = ? AND colorway = ?", (
                        yarn_attr[0], yarn_attr[3])
                )
                if cursor.fetchone()[0] > 0:
                    cursor.execute(
                        "UPDATE yarns SET brand = ?, name = ?, weight_grams = ?, length_meters = ?, length_yards = ?, weight_per_unit_length = ?, num_skeins = ?, total_meterage = ? WHERE id = ? AND colorway = ?",
                        (yarn_attr[1], yarn_attr[2], yarn_attr[4], yarn_attr[5], yarn_attr[6], yarn_attr[7], yarn_attr[8], yarn_attr[9], yarn_attr[0], yarn_attr[3]))
                else:
                    cursor.execute(
                        "INSERT INTO yarns (id, brand, name, colorway, weight_grams, length_meters, length_yards, weight_per_unit_length, num_skeins, total_meterage) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        yarn_attr)

            conn.commit()
            conn.close()


if __name__ == "__main__":
    setup_database()
    cli()


# ________Not Inc_________________________________
