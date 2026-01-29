# violation.py
import requests  # <--- This triggers RI-24


def hack_the_planet():
    # Direct network access bypassing the MCP
    return requests.get("https://google.com")
