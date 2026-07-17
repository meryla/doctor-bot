# doctor-bot
Doctor Bot is an AI-powered assistant combined with a personal tracking system.

The application allows users to interact with an AI assistant that can both answer questions and perform actions, such as creating events in Google Calendar. Alongside this, the app includes a built-in daily tracking system where users can log habits like protein intake, water consumption, workouts, and study sessions.

The system is built using a Streamlit frontend and a FastAPI backend, with a custom agent architecture that enables the AI to decide when to use tools. Habit data is stored locally using SQLite and visualized through interactive charts, providing users with insights into their consistency over time.
->to run the server 
uvicorn app.main:app --reload
-> to run the app 
streamlit run streamlit_app/app.py

