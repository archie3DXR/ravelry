#!/usr/bin/env python3


##create function tofetchpage with authentication

import sys
import argparse
import requests
import json


def fetch_rav(tool, query):
    url = f"https://api.ravelry.com/projects/{tool}.json?query={query}"
    auth = (
        "read-03d7ddeb63ba350c7f9149d489013054",
        "3x4ic3upMHHOV83s140UGpOKH9inPN+2Vvr6VmWw",
    )
    response = requests.get(url, auth=auth)
    ravelrydata = response.json()
    data = json.dumps(ravelrydata, indent=4)
    print(data)


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

    fetch_rav(args.tool, args.query)

### 01.json is a saved json output from | jq > 01.json
