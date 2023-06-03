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
            weight_grams INTEGER,
            length_meters INTEGER,
            length_yards INTEGER,
            weight_per_unit_length FLOAT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS colorways (
            yarn_id INTEGER,
            colorway TEXT,
            num_skeins FLOAT,
            FOREIGN KEY (yarn_id) REFERENCES yarns (id)
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


def process_yarn_data(yarn_data, colorway_skeins):
    yarn_attributes = []

    yarn = yarn_data["yarn"]

    yarn_id = yarn["id"]
    brand = yarn["yarn_company"]["name"]
    name = yarn["name"]
    weight = yarn["grams"]
    yardage = yarn["yardage"]
    total_meterage = yardage * 0.9144

    yarn_attributes.append((yarn_id, brand, name, weight, round(yardage * 0.9144, 1),
                            yardage, round(weight / (yardage * 0.9144), 2)))

    return yarn_attributes, colorway_skeins


def view_database():
    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM yarns")
    yarn_rows = cursor.fetchall()

    table = PrettyTable()
    table.field_names = ["id", "brand", "name", "weight_grams",
                         "length_meters", "length_yards", "weight_per_unit_length", "colorway_skeins"]

    for yarn_row in yarn_rows:
        yarn_id = yarn_row[0]
        cursor.execute(
            "SELECT colorway, num_skeins FROM colorways WHERE yarn_id = ?", (yarn_id,))
        colorway_rows = cursor.fetchall()

        colorway_skeins = "\n".join(
            [f"{colorway}: {num_skeins} skeins ({num_skeins * yarn_row[4]} meters)" for colorway, num_skeins in colorway_rows])

        table.add_row(yarn_row[0:3] + yarn_row[3:] + (colorway_skeins,))

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
        "DELETE FROM colorways WHERE yarn_id = ?", (yarn_id,)
    )
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

        yarn_data = fetch_yarn_by_id(yarn_id)
        if yarn_data is not None:
            colorway_skeins = []
            while True:
                colorway = click.prompt(
                    "Enter the colorway of the yarn (or 'done' to finish)", type=str)
                if colorway.lower() == "done":
                    break
                num_skeins = click.prompt(
                    "Enter the number of skeins", type=float)
                colorway_skeins.append((colorway, num_skeins))

            yarn_attributes, colorway_skeins = process_yarn_data(
                yarn_data, colorway_skeins)

            conn = sqlite3.connect('yarn_db.sqlite')
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO yarns (id, brand, name, weight_grams, length_meters, length_yards, weight_per_unit_length) VALUES (?, ?, ?, ?, ?, ?, ?)",
                yarn_attributes[0]
            )
            yarn_id = yarn_attributes[0][0]

            for colorway, num_skeins in colorway_skeins:
                cursor.execute(
                    "INSERT INTO colorways (yarn_id, colorway, num_skeins) VALUES (?, ?, ?)",
                    (yarn_id, colorway, num_skeins)
                )

            conn.commit()
            conn.close()


@cli.command()
def edit():
    view_database()  # Display the existing records
    yarn_id = click.prompt("Enter the yarn id to edit", type=int)

    conn = sqlite3.connect('yarn_db.sqlite')
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM yarns WHERE id = ?", (yarn_id,)
    )
    yarn_row = cursor.fetchone()

    if yarn_row:
        print(f"Editing yarn with ID: {yarn_id}")
        print(f"Current colorways for yarn '{yarn_row[2]}':")
        cursor.execute(
            "SELECT colorway, num_skeins FROM colorways WHERE yarn_id = ?", (
                yarn_id,)
        )
        colorway_rows = cursor.fetchall()
        for colorway_row in colorway_rows:
            print(
                f"Colorway: {colorway_row[0]}, Num Skeins: {colorway_row[1]}")

        while True:
            action = click.prompt(
                "Select an action: (a)dd, (e)dit, (r)emove, (d)one", type=str)
            if action.lower() == "a":
                colorway = click.prompt("Enter the new colorway", type=str)
                num_skeins = click.prompt(
                    "Enter the number of skeins", type=float)
                cursor.execute(
                    "INSERT INTO colorways (yarn_id, colorway, num_skeins) VALUES (?, ?, ?)",
                    (yarn_id, colorway, num_skeins)
                )
                conn.commit()
                print("Colorway added successfully!")
            elif action.lower() == "e":
                colorway = click.prompt("Enter the colorway to edit", type=str)
                new_num_skeins = click.prompt(
                    "Enter the new number of skeins", type=float)
                cursor.execute(
                    "UPDATE colorways SET num_skeins = ? WHERE yarn_id = ? AND colorway = ?",
                    (new_num_skeins, yarn_id, colorway)
                )
                conn.commit()
                print("Colorway updated successfully!")
            elif action.lower() == "r":
                colorway = click.prompt(
                    "Enter the colorway to remove", type=str)
                cursor.execute(
                    "DELETE FROM colorways WHERE yarn_id = ? AND colorway = ?",
                    (yarn_id, colorway)
                )
                conn.commit()
                print("Colorway removed successfully!")
            elif action.lower() == "d":
                break
            else:
                print("Invalid action. Please try again.")

    else:
        print(f"No yarn found with ID: {yarn_id}")

    conn.close()


if __name__ == "__main__":
    setup_database()
    cli()
