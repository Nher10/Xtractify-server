import json
import os
import subprocess
import time

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


# Function to run the Scrapy spider
def run_spider(query):
    subprocess.run(
        ["scrapy", "crawl", "amazon_search_product", "-a", f"keyword={query}"]
    )


# Function to read the scraped data from JSON file
def read_data():
    while True:
        if "searchItem.json" in os.listdir("."):
            try:
                with open("searchItem.json", "r") as file:
                    scraped_data = json.load(file)
                return scraped_data
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                print("Waiting for valid JSON data...")
                time.sleep(1)
        else:
            print(
                "searchItem.json not found. Waiting for the spider to generate the file..."
            )
            time.sleep(1)


# Flask route to fetch the scraped data
@app.route("/", methods=["GET"])
def get_data():
    query = request.args.get("query")  # Get the query parameter from the URL
    run_spider(query)
    scraped_data = read_data()
    return jsonify(scraped_data)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
