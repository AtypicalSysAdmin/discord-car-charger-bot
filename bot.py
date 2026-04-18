import asyncio
import discord
import pytz
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
from state import state

class ChargerBot(commands.Bot):
    def __init__(self, token, user_id, hour, minute):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)
        self.token = token
        self.user_id = user_id
        self.hour = hour
        self.minute = minute
        self.tz_pacific = pytz.timezone('US/Pacific')
        self.tz_utc = pytz.utc

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced.")

    async def on_ready(self):
        print(f'Logged in as {self.user.name}')
        self.loop.create_task(self.reminder_loop())

    async def reminder_loop(self):
        await self.wait_until_ready()
        
        while True:
            now_utc = datetime.now(timezone.utc)
            now_pacific = now_utc.astimezone(self.tz_pacific)
            
            # 1. Calculate next target time for display
            target_today = now_pacific.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            if now_pacific >= target_today:
                next_target_pacific = target_today + timedelta(days=1)
            else:
                next_target_pacific = target_today
            
            state.next_target_time = next_target_pacific.astimezone(timezone.utc)
            state.save()

            # 2. Check if we should send a reminder
            if state.charging_active:
                # Check for mute expiration
                if state.is_muted and state.muted_until:
                    if now_utc >= state.muted_until:
                        state.is_muted = False
                        state.muted_until = None
                        state.save()
                        print("Mute expired. Resuming notifications.")
                
                if state.is_muted:
                    await asyncio.sleep(30)
                    continue

                # Original reminder logic follows...
                # If we are past today's target time AND we haven't sent a reminder yet today
                if now_pacific >= target_today and state.last_reminder_date != now_pacific.date():
                    try:
                        user = await self.fetch_user(int(self.user_id))
                        await user.send("🚨 Reminder: Unplug your car!")
                        state.last_reminder_date = now_pacific.date()
                        state.next_interval_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                        state.save()
                        print(f"Sent daily reminder at {now_pacific}")
                    except Exception as e:
                        print(f"Failed to send reminder: {e}")
                
                # If we already sent the daily reminder, handle nag logic
                elif state.last_reminder_date == now_pacific.date():
                    # If we don't have a next nag time set (e.g. just plugged back in), set one
                    if not state.next_interval_time:
                        state.next_interval_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                        state.save()
                        print(f"Car replugged after daily reminder. Next nag scheduled for {state.next_interval_time}")
                    
                    # Check if it's time to nag
                    elif now_utc >= state.next_interval_time:
                        try:
                            user = await self.fetch_user(int(self.user_id))
                            await user.send("⚠️ Still plugged in! Don't forget to unplug.")
                            state.next_interval_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                            state.save()
                            print(f"Sent nag reminder at {now_pacific}")
                        except Exception as e:
                            print(f"Failed to send nag: {e}")
            else:
                # If not charging, clear the nag timer so it resets upon next plug-in
                state.next_interval_time = None

            await asyncio.sleep(30) # Check every 30 seconds

def setup_bot(bot, token):
    @bot.tree.command(name="plugged", description="Enable car charging reminders")
    async def plugged(interaction: discord.Interaction):
        state.set_plugged()
        await interaction.response.send_message("🔌 Noted. Reminders enabled.")

    @bot.tree.command(name="unplugged", description="Disable car charging reminders")
    async def unplugged(interaction: discord.Interaction):
        state.set_unplugged()
        await interaction.response.send_message("📴 Done. Reminders off.")

    @bot.tree.command(name="mute", description="Mute reminders until 6 AM PST")
    async def mute(interaction: discord.Interaction):
        mute_until = state.set_mute(bot.tz_pacific)
        await interaction.response.send_message(f"🔇 Muted until {mute_until.strftime('%I:%M %p %Z')}")

    @bot.tree.command(name="unmute", description="Unmute reminders")
    async def unmute(interaction: discord.Interaction):
        state.set_unmute()
        await interaction.response.send_message("🔊 Unmuted. Reminders active.")

    return bot
