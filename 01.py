#!/usr/bin/env python3


##create function tofetchpage with authentication

import sys
import requests
import json


def fetch_webpage():
    url = "https://api.ravelry.com/projects/search.json?query=puppycat"
    auth = (
        "read-03d7ddeb63ba350c7f9149d489013054",
        "3x4ic3upMHHOV83s140UGpOKH9inPN+2Vvr6VmWw",
    )
    response = requests.get(url, auth=auth)
    ravelry_things = response.json()
    return ravelry_things


##run fetch_webpage and print as json output

if __name__ == "__main__":
    webpage = fetch_webpage()
    # print(webpage)
    print(json.dumps(webpage, indent=4))


## 01.json is a saved json output from | jq > 01.json
