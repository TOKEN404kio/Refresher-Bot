import os
import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# Setup Bot and Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variables to store your formula choices
formula_options = ["Formula A", "Formula B", "Formula C", "Formula D"]

# --- THE TEXT BOX POP-UP ---
class FormulaInputModal(discord.ui.Modal):
    def __init__(self, selected_formula: str):
        super().__init__(title=f"Applying: {selected_formula}")
        self.selected_formula = selected_formula

        # The text input box the user fills out
        self.user_input = discord.ui.TextInput(
            label="Paste your input here:",
            style=discord.TextStyle.paragraph,
            placeholder="Type or paste your information...",
            required=True,
            max_length=2000
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Instantly respond to the user
        await interaction.response.send_message(
            "Verifying that this is real. This could take up to 2 hours.", 
            ephemeral=True  # Hidden from everyone else
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
            print(f"Could not DM owner. Open your privacy settings! Error: {e}")

# --- THE DROPDOWN SELECT MENU ---
class FormulaSelect(discord.ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=opt, description=f"Select {opt}") for opt in formula_options]
        super().__init__(placeholder="Choose a formula...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(FormulaInputModal(self.values[0]))

class FormulaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FormulaSelect())

# --- BOT COMMANDS ---
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    if bot.owner_id is None:
        app = await bot.application_info()
        bot.owner_id = app.owner.id
    
    try:
        await bot.tree.sync()
    except Exception as e:
        print(e)

# Command 1: Post the Dropdown Menu (For Users)
@bot.hybrid_command(name="start", description="Open up the formula picker.")
async def start(ctx: commands.Context):
    await ctx.send("What formula do you want to do?", view=FormulaView())

# Command 2: Change Options (Owner Only)
@bot.hybrid_command(name="setformulas", description="Owner only: Update the 4 choices.")
@app_commands.describe(opt1="Option 1", opt2="Option 2", opt3="Option 3", opt4="Option 4")
async def setformulas(ctx: commands.Context, opt1: str, opt2: str, opt3: str, opt4: str):
    if ctx.author.id != bot.owner_id:
        await ctx.send("❌ You are not authorized to use this command.", ephemeral=True)
        return
        
    global formula_options
    formula_options = [opt1, opt2, opt3, opt4]
    await ctx.send(f"✅ Formulas updated to:\n1. {opt1}\n2. {opt2}\n3. {opt3}\n4. {opt4}", ephemeral=True)

keep_alive()
bot.run(os.environ.get('DISCORD_TOKEN'))
