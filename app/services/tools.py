import webbrowser
from datetime import datetime

# -------- GOOGLE --------
def open_google():
    webbrowser.open("https://www.google.com")
    return "Opened Google"

def search_google(query: str):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return f"Searched Google for: {query}"


# -------- CALENDAR (TEMP SIMPLE VERSION) --------
calendar_events = []

def add_event(title: str, time: str):
    event = {
        "title": title,
        "time": time
    }
    calendar_events.append(event)
    return f"Event '{title}' added at {time}"

def get_events():
    if not calendar_events:
        return "No events found"

    return "\n".join([f"{e['title']} at {e['time']}" for e in calendar_events])