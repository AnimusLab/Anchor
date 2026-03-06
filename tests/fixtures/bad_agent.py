# violation.py
import requests


def hack_the_planet():
    # Direct network access bypassing the MCP
    return requests.get("https://google.com")
