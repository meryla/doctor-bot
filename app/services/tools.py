import webbrowser
from app.services.google_calendar import add_event as google_add_event
from app.services.google_calendar import get_events as google_get_events

# -------- GOOGLE --------
def open_google():
    webbrowser.open("https://www.google.com")
    return {"status": "success", "message": "Opened Google"}

def search_google(query: str):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    return {"status": "success", "message": f"Searched Google for: {query}"}

# -------- CALENDAR --------
def add_event(title: str, time: str):
    # Temporary mapping from your old tool schema
    return google_add_event(
        title=title,
        start_time=time,
    )

def get_events():
    return google_get_events()