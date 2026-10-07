import asyncio
import discord
import pytz
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
from state import state

class ChargerBot(commands.Bot):
    def __init__(self, token, user_id, hour=None, minute=None):
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

    async def _clear_history(self, channel, limit=None, before=None):
        """Helper to delete all bot messages in a channel."""
        try:
            async for message in channel.history(limit=limit, before=before):
                if message.author == self.user:
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Failed to delete message {message.id}: {e}")
        except Exception as e:
            print(f"Error reading history: {e}")

    async def reminder_loop(self):
        await self.wait_until_ready()
        
        while True:
            now_utc = datetime.now(timezone.utc)
            now_pacific = now_utc.astimezone(self.tz_pacific)

            # Check if we should send a reminder
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

                # Helper to handle sending and tracking messages
                async def send_reminder(user, text):
                    # Delete previous reminder if it exists
                    if state.last_reminder_id:
                        try:
                            dm = user.dm_channel or await user.create_dm()
                            msg = await dm.fetch_message(state.last_reminder_id)
                            await msg.delete()
                        except Exception:
                            pass  # Message already deleted or not found
                    
                    try:
                        new_msg = await user.send(text)
                        state.last_reminder_id = new_msg.id
                        state.save()
                    except Exception as e:
                        print(f"Failed to send/save reminder: {e}")

                # If target time is missing for some reason, re-evaluate it
                if not state.next_target_time:
                    shift, target_utc = state.calculate_shift_and_target(now_utc)
                    state.current_shift = shift
                    state.next_target_time = target_utc
                    state.save()

                # 1. Initial reminder for the active shift
                if not state.initial_reminder_sent:
                    if state.next_target_time and now_utc >= state.next_target_time:
                        try:
                            user = await self.fetch_user(int(self.user_id))
                            if state.current_shift == "day":
                                reminder_msg = "🚨 Reminder: Pick up your car! (Day parking window ends at 6:00 PM)"
                            else:
                                reminder_msg = "🚨 Reminder: Time to pick up / unplug your car!"

                            await send_reminder(user, reminder_msg)
                            state.initial_reminder_sent = True
                            state.last_reminder_date = now_pacific.date()
                            state.next_interval_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                            state.save()
                            print(f"Sent initial {state.current_shift} reminder at {now_pacific}")
                        except Exception as e:
                            print(f"Failed to send reminder: {e}")

                # 2. Nag reminder every 15 minutes after initial reminder
                else:
                    if not state.next_interval_time:
                        state.next_interval_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                        state.save()
                    elif now_utc >= state.next_interval_time:
                        try:
                            user = await self.fetch_user(int(self.user_id))
                            await send_reminder(user, "⚠️ Still plugged in! Don't forget to pick up your car.")
                            state.next_interval_time = datetime.now(timezone.utc) + timedelta(minutes=15)
                            state.save()
                            print(f"Sent nag reminder at {now_pacific}")
                        except Exception as e:
                            print(f"Failed to send nag: {e}")
            else:
                # If not charging, clear nag timers
                state.next_interval_time = None

            await asyncio.sleep(30)  # Check every 30 seconds

def setup_bot(bot, token):
    @bot.tree.command(name="plugged", description="Enable car charging reminders")
    async def plugged(interaction: discord.Interaction):
        # Auto-cleanup before starting
        await interaction.response.send_message("🚿 Cleaning history and enabling reminders...")
        status_msg = await interaction.original_response()
        await bot._clear_history(interaction.channel, before=status_msg)
        shift, target_utc = state.set_plugged()
        target_pacific = target_utc.astimezone(bot.tz_pacific)
        now_utc = datetime.now(timezone.utc)

        shift_label = "Day Shift (6 AM - 6 PM)" if shift == "day" else "Night Shift (6 PM - 6 AM)"
        if target_utc <= now_utc:
            sched_str = "Immediate reminder (then every 15 min)"
        else:
            sched_str = f"Reminder set for {target_pacific.strftime('%I:%M %p')} (then every 15 min)"

        await interaction.edit_original_response(
            content=f"🔌 History cleaned. Reminders enabled for **{shift_label}**.\n⏰ {sched_str}."
        )

    @bot.tree.command(name="unplugged", description="Disable car charging reminders")
    async def unplugged(interaction: discord.Interaction):
        state.set_unplugged()
        await interaction.response.send_message("📴 Done. Reminders off.")

    @bot.tree.command(name="mute", description="Mute reminders until shift ends")
    async def mute(interaction: discord.Interaction):
        mute_until = state.set_mute(bot.tz_pacific)
        await interaction.response.send_message(f"🔇 Muted until {mute_until.strftime('%I:%M %p %Z')}")

    @bot.tree.command(name="unmute", description="Unmute reminders")
    async def unmute(interaction: discord.Interaction):
        state.set_unmute()
        await interaction.response.send_message("🔊 Unmuted. Reminders active.")

    @bot.tree.command(name="clearchathistory", description="Delete ALL previous bot messages in this chat")
    async def clearchathistory(interaction: discord.Interaction):
        await interaction.response.send_message("🧹 Scrubbing all my previous messages... this may take a moment.")
        status_msg = await interaction.original_response()
        await bot._clear_history(interaction.channel, before=status_msg)
        await interaction.edit_original_response(content="✅ Chat history cleaned!")

    return bot
