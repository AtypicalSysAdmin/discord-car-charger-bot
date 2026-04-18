import os
import threading
from dotenv import load_dotenv
from bot import ChargerBot, setup_bot
from dashboard import run_dashboard

# Load configuration
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
YOUR_USER_ID = os.getenv('YOUR_USER_ID')
REMINDER_HOUR = int(os.getenv('REMINDER_HOUR'))
REMINDER_MINUTE = int(os.getenv('REMINDER_MINUTE'))

def main():
    # 1. Initialize the Discord Bot
    bot_instance = ChargerBot(
        token=TOKEN,
        user_id=YOUR_USER_ID,
        hour=REMINDER_HOUR,
        minute=REMINDER_MINUTE
    )
    
    # 2. Setup bot commands
    bot = setup_bot(bot_instance, TOKEN)
    
    # 3. Start the Flask Dashboard in a separate thread
    # This allows Flask to run without blocking the Discord bot
    flask_thread = threading.Thread(target=run_dashboard, args=(bot,), daemon=True)
    flask_thread.start()
    print("Dashboard thread started.")

    # 4. Start the Discord Bot (This is a blocking call)
    print("Starting Discord bot...")
    bot.run(TOKEN)

if __name__ == "__main__":
    main()