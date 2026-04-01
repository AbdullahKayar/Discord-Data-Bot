import discord
import os
import aiosqlite
import asyncio
import io
import csv
import re
from datetime import timedelta, datetime, time 
from discord import app_commands
from discord.ext import commands, tasks 
from dotenv import load_dotenv

# --- CONFIGURATION ---
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# --- CHANNEL IDs ---
# Replace 0 with your actual server channel IDs.
USER_COMMAND_CHANNEL_ID = 0  # Where regular users can use commands
ADMIN_COMMAND_CHANNEL_ID = 0 # Where admins can use restricted commands
AUDIT_LOG_CHANNEL_ID = 0     # Where audit logs & weekly reports will be sent

class DataWarehouseBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await setup_database()
        await self.tree.sync()
        self.weekly_report_loop.start()
        print("✨ [System]: Data Warehouse & Autonomous Reporting Active.")

    # --- WEEKLY AUTONOMOUS REPORT ---
    @tasks.loop(time=time(hour=23, minute=59)) 
    async def weekly_report_loop(self):
        if datetime.now().weekday() != 6: # 6 = Sunday
            return

        log_channel = self.get_channel(AUDIT_LOG_CHANNEL_ID)
        if not log_channel: return

        print("📊 [Analysis]: Weekly report is being generated...")
        
        async with aiosqlite.connect("server_archive.db") as db:
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            async with db.execute("SELECT COUNT(*) FROM messages WHERE date >= ?", (seven_days_ago,)) as c:
                total_msgs = (await c.fetchone())[0]
            
            async with db.execute("SELECT user_name, COUNT(*) as m FROM messages WHERE date >= ? GROUP BY user_id ORDER BY m DESC LIMIT 1", (seven_days_ago,)) as c:
                row = await c.fetchone()
                top_user = f"{row[0]} ({row[1]} messages)" if row else "No Data"

            async with db.execute("SELECT channel_name, COUNT(*) as m FROM messages WHERE date >= ? GROUP BY channel_id ORDER BY m DESC LIMIT 1", (seven_days_ago,)) as c:
                row = await c.fetchone()
                top_channel = f"#{row[0]}" if row else "No Data"

            async with db.execute("SELECT COUNT(*) FROM deleted_messages WHERE date >= ?", (seven_days_ago,)) as c:
                deleted_count = (await c.fetchone())[0]

        embed = discord.Embed(title="📈 Weekly Server Analytics Report", color=discord.Color.gold())
        embed.add_field(name="💬 Total Messages", value=f"**{total_msgs}**", inline=True)
        embed.add_field(name="👻 Deleted Messages", value=f"**{deleted_count}**", inline=True)
        embed.add_field(name="🏆 Top User", value=top_user, inline=False)
        embed.add_field(name="📍 Top Channel", value=top_channel, inline=False)
        embed.set_footer(text="Date Range: Last 7 Days")
        
        await log_channel.send(embed=embed)

bot = DataWarehouseBot()

# --- DATABASE SETUP ---
async def setup_database():
    async with aiosqlite.connect("server_archive.db") as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS messages 
            (id INTEGER PRIMARY KEY, user_id INTEGER, user_name TEXT, content TEXT, channel_id INTEGER, channel_name TEXT, date TEXT, media TEXT, links TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS users 
            (user_id INTEGER PRIMARY KEY, tag TEXT, join_date TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS edited_messages 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name TEXT, channel_name TEXT, old_message TEXT, new_message TEXT, date TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS deleted_messages 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, user_name TEXT, channel_name TEXT, content TEXT, media TEXT, date TEXT)''')
        await db.commit()

# --- TIMEZONE SETTINGS ---
def get_local_time():
    # Adjust timezone offset here if needed (e.g., hours=3 for UTC+3)
    return discord.utils.utcnow() + timedelta(hours=3)

# --- DATA SCRAPING & LOGGING ---
async def scrape_history():
    print("🔍 [Scraper]: Archiving started...")
    async with aiosqlite.connect("server_archive.db") as db:
        for guild in bot.guilds:
            async for member in guild.fetch_members(limit=None):
                await db.execute('INSERT OR REPLACE INTO users (user_id, tag, join_date) VALUES (?, ?, ?)',
                    (member.id, str(member), str(member.joined_at)))
            
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).read_message_history:
                    async for msg in channel.history(limit=None, oldest_first=True):
                        if msg.author.bot: continue
                        links = ", ".join(re.findall(r'(https?://[^\s]+)', msg.content))
                        media = ", ".join([attachment.url for attachment in msg.attachments])
                        
                        real_time = msg.created_at + timedelta(hours=3) if msg.created_at.tzinfo else msg.created_at
                        
                        await db.execute('INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (msg.id, msg.author.id, msg.author.name, msg.content, msg.channel.id, msg.channel.name, str(real_time), media, links))
        await db.commit()
    print("🚀 [Scraper]: Data archived successfully.")

@bot.event
async def on_message(message):
    if message.author.bot: return
    links = ", ".join(re.findall(r'(https?://[^\s]+)', message.content))
    media = ", ".join([attachment.url for attachment in message.attachments])
    async with aiosqlite.connect("server_archive.db") as db:
        await db.execute('INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (message.id, message.author.id, message.author.name, message.content, message.channel.id, message.channel.name, str(get_local_time()), media, links))
        await db.commit()
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content: return
    async with aiosqlite.connect("server_archive.db") as db:
        await db.execute('INSERT INTO edited_messages (user_name, channel_name, old_message, new_message, date) VALUES (?, ?, ?, ?, ?)',
            (before.author.name, before.channel.name, before.content, after.content, str(get_local_time())))
        await db.execute('UPDATE messages SET content = ? WHERE id = ?', (after.content, after.id))
        await db.commit()

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    media = ", ".join([attachment.url for attachment in message.attachments])
    async with aiosqlite.connect("server_archive.db") as db:
        await db.execute('INSERT INTO deleted_messages (user_name, channel_name, content, media, date) VALUES (?, ?, ?, ?, ?)',
            (message.author.name, message.channel.name, message.content, media, str(get_local_time())))
        await db.commit()

# --- AUDIT LOG CENTER ---
async def send_audit_log(user, category, action, details):
    if AUDIT_LOG_CHANNEL_ID == 0: return # Skip if ID is missing
    log_channel = bot.get_channel(AUDIT_LOG_CHANNEL_ID)
    if log_channel:
        color = discord.Color.green() if "User" in category else discord.Color.red()
        embed = discord.Embed(title=f"🕵️ Audit Log [{category}]", color=color)
        embed.add_field(name="Requested By", value=user, inline=True)
        embed.add_field(name="Action", value=action, inline=True)
        embed.add_field(name="Details", value=details[:1024], inline=False)
        embed.set_footer(text=f"Timestamp: {get_local_time().strftime('%Y-%m-%d %H:%M')}")
        await log_channel.send(embed=embed)


# =====================================================================
# CATEGORY 1: USER COMMANDS (RESTRICTED TO USER CHANNEL)
# =====================================================================

@bot.tree.command(name="my_data", description="[User] Download your own categorized data.")
@app_commands.describe(category="Which data are you looking for?")
@app_commands.choices(category=[
    app_commands.Choice(name="🔗 My Links", value="links"),
    app_commands.Choice(name="📂 My Media/Files", value="media"),
    app_commands.Choice(name="💬 All My Messages", value="messages")
])
async def my_data(interaction: discord.Interaction, category: app_commands.Choice[str]):
    if USER_COMMAND_CHANNEL_ID != 0 and interaction.channel_id != USER_COMMAND_CHANNEL_ID:
        await interaction.response.send_message(f"❌ This command can only be used in <#{USER_COMMAND_CHANNEL_ID}>.", ephemeral=True)
        return
    
    await interaction.response.defer(ephemeral=True)

    async with aiosqlite.connect("server_archive.db") as db:
        if category.value == "links":
            query = "SELECT date, channel_name, links FROM messages WHERE user_id = ? AND links != '' ORDER BY id ASC"
        elif category.value == "media":
            query = "SELECT date, channel_name, media FROM messages WHERE user_id = ? AND media != '' ORDER BY id ASC"
        else:
            query = "SELECT date, channel_name, content FROM messages WHERE user_id = ? ORDER BY id ASC"
            
        async with db.execute(query, (interaction.user.id,)) as cursor:
            records = await cursor.fetchall()

    if not records:
        await interaction.followup.send(f"❌ No '{category.name}' records found for you.", ephemeral=True)
        return

    content = f"--- PERSONAL DATA DUMP ({category.name}) ---\n"
    content += f"Records Found: {len(records)}\n{'='*50}\n\n"

    for date, channel, data in records:
        content += f"[{date[:16]}] #{channel}: {data}\n"

    file_buffer = io.StringIO(content)
    discord_file = discord.File(fp=file_buffer, filename=f"My_Data_{category.value}.txt")

    await interaction.followup.send(f"✅ Your data archive is ready!", file=discord_file, ephemeral=True)
    await send_audit_log(interaction.user.name, "Category 1 (User)", "Downloaded Own Data", f"Selected: {category.name}")


# =====================================================================
# CATEGORY 2: ADMIN DATA MINING COMMANDS
# =====================================================================

@bot.tree.command(name="admin_target_data", description="[Admin] Download a specific user's data (including hidden channels).")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(target_user="Whose data to extract?", category="Which data category?")
@app_commands.choices(category=[
    app_commands.Choice(name="🔗 Only Links", value="links"),
    app_commands.Choice(name="📂 Only Media/Files", value="media"),
    app_commands.Choice(name="💬 All Message History", value="messages")
])
async def admin_target_data(interaction: discord.Interaction, target_user: discord.Member, category: app_commands.Choice[str]):
    if ADMIN_COMMAND_CHANNEL_ID != 0 and interaction.channel_id != ADMIN_COMMAND_CHANNEL_ID:
        await interaction.response.send_message(f"❌ Admin commands are restricted to <#{ADMIN_COMMAND_CHANNEL_ID}>.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    async with aiosqlite.connect("server_archive.db") as db:
        if category.value == "links":
            query = "SELECT date, channel_name, links FROM messages WHERE user_id = ? AND links != '' ORDER BY id ASC"
        elif category.value == "media":
            query = "SELECT date, channel_name, media FROM messages WHERE user_id = ? AND media != '' ORDER BY id ASC"
        else:
            query = "SELECT date, channel_name, content FROM messages WHERE user_id = ? ORDER BY id ASC"
            
        async with db.execute(query, (target_user.id,)) as cursor:
            records = await cursor.fetchall()

    if not records:
        await interaction.followup.send(f"❌ No '{category.name}' records found for {target_user.name}.", ephemeral=True)
        return

    content = f"--- ADMIN DATA DUMP (TARGET: {target_user.name}) ---\n"
    content += f"Category: {category.name}\n"
    content += f"Records Found: {len(records)} (including private channels)\n{'='*50}\n\n"

    for date, channel, data in records:
        content += f"[{date[:16]}] #{channel}: {data}\n"

    file_buffer = io.StringIO(content)
    discord_file = discord.File(fp=file_buffer, filename=f"TARGET_{target_user.name}_{category.value}.txt")

    await interaction.followup.send(f"🔴 **Extraction Successful:** Data for {target_user.name} is ready.", file=discord_file, ephemeral=True)
    await send_audit_log(interaction.user.name, "Category 2 (Admin)", "Target Data Dump", f"Target: {target_user.name} | {category.name}")


@bot.tree.command(name="csv_export", description="[Admin] Export the entire database or a user's data to a CSV file.")
@app_commands.checks.has_permissions(manage_messages=True)
async def csv_export(interaction: discord.Interaction, user: discord.Member = None):
    if ADMIN_COMMAND_CHANNEL_ID != 0 and interaction.channel_id != ADMIN_COMMAND_CHANNEL_ID:
        await interaction.response.send_message(f"❌ Admin commands are restricted to <#{ADMIN_COMMAND_CHANNEL_ID}>.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    async with aiosqlite.connect("server_archive.db") as db:
        if user:
            query = "SELECT id, user_name, content, channel_name, date, links FROM messages WHERE user_id = ?"
            param = (user.id,)
        else:
            query = "SELECT id, user_name, content, channel_name, date, links FROM messages"
            param = ()
            
        async with db.execute(query, param) as cursor:
            records = await cursor.fetchall()

    if not records:
        await interaction.followup.send("❌ No data found.", ephemeral=True)
        return

    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(["Message_ID", "Username", "Content", "Channel", "Date", "Links"])
    for row in records:
        writer.writerow(row)

    output.seek(0)
    csv_file = discord.File(fp=output, filename="Database_Dump.csv")
    await interaction.followup.send(f"📊 CSV Export is ready.", file=csv_file, ephemeral=True)
    await send_audit_log(interaction.user.name, "Category 2 (Admin)", "CSV Export", f"Rows exported: {len(records)}")


@bot.tree.command(name="edited_messages", description="[Admin] View the original content of edited messages.")
@app_commands.checks.has_permissions(manage_messages=True)
async def edited_messages(interaction: discord.Interaction, user: discord.Member):
    if ADMIN_COMMAND_CHANNEL_ID != 0 and interaction.channel_id != ADMIN_COMMAND_CHANNEL_ID:
        await interaction.response.send_message(f"❌ Admin commands are restricted to <#{ADMIN_COMMAND_CHANNEL_ID}>.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    async with aiosqlite.connect("server_archive.db") as db:
        async with db.execute("SELECT channel_name, old_message, new_message, date FROM edited_messages WHERE user_name = ? ORDER BY id DESC LIMIT 5", (user.name,)) as cursor:
            results = await cursor.fetchall()

    if not results:
        await interaction.followup.send(f"❌ No edit records found for `{user.name}`.", ephemeral=True)
        return

    response = f"🕵️ **Edit Log for {user.name}:**\n\n"
    for channel, old, new, date in results:
        response += f"📍 **#{channel}** ({date[:16]})\n❌ **Old:** {old}\n✅ **New:** {new}\n{'-'*30}\n"

    await interaction.followup.send(response, ephemeral=True)
    await send_audit_log(interaction.user.name, "Category 2 (Admin)", "Checked Edit Logs", user.name)


@bot.tree.command(name="deleted_messages", description="[Admin] View recently deleted (shadow) messages.")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(user="Select a user to filter their deleted messages")
async def deleted_messages(interaction: discord.Interaction, user: discord.Member = None):
    if ADMIN_COMMAND_CHANNEL_ID != 0 and interaction.channel_id != ADMIN_COMMAND_CHANNEL_ID:
        await interaction.response.send_message(f"❌ Admin commands are restricted to <#{ADMIN_COMMAND_CHANNEL_ID}>.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    async with aiosqlite.connect("server_archive.db") as db:
        if user:
            query = "SELECT channel_name, content, media, date FROM deleted_messages WHERE user_name = ? ORDER BY id DESC LIMIT 5"
            param = (user.name,)
            async with db.execute(query, param) as cursor:
                results = await cursor.fetchall()
        else:
            query = "SELECT user_name, channel_name, content, media, date FROM deleted_messages ORDER BY id DESC LIMIT 5"
            async with db.execute(query) as cursor:
                results = await cursor.fetchall()

    if not results:
        await interaction.followup.send("❌ No deleted message records found.", ephemeral=True)
        return

    response = f"👻 **Recently Deleted Messages (Shadow Records):**\n\n"
    if user:
        for channel, content, media, date in results:
            media_text = f"\n📎 Attachment: {media}" if media else ""
            response += f"📍 **#{channel}** ({date[:16]})\n🗑️ **Message:** {content}{media_text}\n{'-'*30}\n"
    else:
        for name, channel, content, media, date in results:
            media_text = f"\n📎 Attachment: {media}" if media else ""
            response += f"👤 **{name}** | 📍 **#{channel}** ({date[:16]})\n🗑️ **Message:** {content}{media_text}\n{'-'*30}\n"

    await interaction.followup.send(response, ephemeral=True)
    target_log = user.name if user else "General Top 5 Deleted"
    await send_audit_log(interaction.user.name, "Category 2 (Admin)", "Checked Deleted Messages", target_log)


# --- PERMISSION ERROR HANDLING ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("⛔ **Access Denied:** This command is restricted to administrators.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"🚀 {bot.user} is Online and ready!")
    asyncio.create_task(scrape_history())

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())