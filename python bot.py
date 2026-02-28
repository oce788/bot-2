import os
import discord
from discord.ext import commands
from discord import app_commands

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN          = os.environ.get("BOT_TOKEN", "")
SALON_RAPPORTS = int(os.environ.get("SALON_RAPPORTS", 0))
ROLE_MODO      = os.environ.get("ROLE_MODO", "aide")

if not TOKEN:
    raise ValueError(f"BOT_TOKEN manquant. Variables dispo: {list(os.environ.keys())}")
if not SALON_RAPPORTS:
    raise ValueError(f"SALON_RAPPORTS manquant. Variables dispo: {list(os.environ.keys())}")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

TYPES = {
    "spam":         {"label": "Spam",               "color": discord.Color.orange()},
    "hate":         {"label": "Discours haineux",    "color": discord.Color.red()},
    "nsfw":         {"label": "Contenu NSFW",        "color": discord.Color.purple()},
    "harcelement":  {"label": "Harcelement",          "color": discord.Color.dark_orange()},
    "fausses_info": {"label": "Fausses informations", "color": discord.Color.blue()},
}

def est_modo(interaction: discord.Interaction) -> bool:
    return any(role.name.lower() == ROLE_MODO.lower() for role in interaction.user.roles)

class ActionsMod(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Traite", style=discord.ButtonStyle.success)
    async def traite(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not est_modo(interaction):
            await interaction.response.send_message("Tu n'as pas la permission de faire ca !", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed.add_field(name="Statut", value=f"Traite par {interaction.user.mention}", inline=False)
        embed.color = discord.Color.green()
        self.clear_items()
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("Signalement marque comme traite.", ephemeral=True)

    @discord.ui.button(label="Rejete", style=discord.ButtonStyle.danger)
    async def rejete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not est_modo(interaction):
            await interaction.response.send_message("Tu n'as pas la permission de faire ca !", ephemeral=True)
            return
        embed = interaction.message.embeds[0]
        embed.add_field(name="Statut", value=f"Rejete par {interaction.user.mention}", inline=False)
        embed.color = discord.Color.dark_grey()
        self.clear_items()
        await interaction.message.edit(embed=embed, view=self)
        await interaction.response.send_message("Signalement rejete.", ephemeral=True)

class BoutonsSignalement(discord.ui.View):
    def __init__(self, message_signale=None):
        super().__init__(timeout=60)
        self.message_signale = message_signale

    async def envoyer_rapport(self, interaction: discord.Interaction, type_id: str):
        info = TYPES[type_id]
        salon_rapports = interaction.guild.get_channel(SALON_RAPPORTS)

        if not salon_rapports:
            await interaction.response.send_message("Salon introuvable, contacte un admin.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Nouveau Signalement",
            color=info["color"],
            timestamp=interaction.created_at
        )
        embed.add_field(name="Type",        value=info["label"],                    inline=True)
        embed.add_field(name="Signale par", value=f"{interaction.user.mention}",    inline=True)
        embed.add_field(name="Salon",       value=f"{interaction.channel.mention}", inline=True)

        if self.message_signale:
            msg = self.message_signale
            contenu = msg.content if msg.content else "pas de texte"
            if len(contenu) > 300:
                contenu = contenu[:300] + "..."
            embed.add_field(name="Auteur du message", value=f"{msg.author.mention}",         inline=True)
            embed.add_field(name="Lien du message",   value=f"[Clique ici]({msg.jump_url})", inline=True)
            embed.add_field(name="Contenu",           value=contenu,                         inline=False)
            embed.set_thumbnail(url=msg.author.display_avatar.url)
            embed.set_footer(text=f"ID auteur : {msg.author.id}")
        else:
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text=f"ID : {interaction.user.id}")

        await salon_rapports.send(embed=embed, view=ActionsMod())
        await interaction.response.edit_message(
            content="Signalement envoye aux moderateurs. Merci !",
            view=None
        )

    @discord.ui.button(label="Spam", style=discord.ButtonStyle.secondary)
    async def btn_spam(self, interaction, button):
        await self.envoyer_rapport(interaction, "spam")

    @discord.ui.button(label="Haine", style=discord.ButtonStyle.danger)
    async def btn_hate(self, interaction, button):
        await self.envoyer_rapport(interaction, "hate")

    @discord.ui.button(label="NSFW", style=discord.ButtonStyle.danger)
    async def btn_nsfw(self, interaction, button):
        await self.envoyer_rapport(interaction, "nsfw")

    @discord.ui.button(label="Harcelement", style=discord.ButtonStyle.danger)
    async def btn_harcel(self, interaction, button):
        await self.envoyer_rapport(interaction, "harcelement")

    @discord.ui.button(label="Fausses infos", style=discord.ButtonStyle.primary)
    async def btn_fausses(self, interaction, button):
        await self.envoyer_rapport(interaction, "fausses_info")

@bot.tree.command(name="signalement", description="Signaler un comportement problematique")
async def signalement(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Quel est le probleme ? Choisis une categorie :",
        view=BoutonsSignalement(),
        ephemeral=True
    )

@bot.tree.context_menu(name="Signaler ce message")
async def signaler_message(interaction: discord.Interaction, message: discord.Message):
    if message.author == interaction.user:
        await interaction.response.send_message("Tu ne peux pas signaler ton propre message !", ephemeral=True)
        return
    if message.author.bot:
        await interaction.response.send_message("Tu ne peux pas signaler un bot !", ephemeral=True)
        return
    await interaction.response.send_message(
        "Quel est le probleme avec ce message ? Choisis une categorie :",
        view=BoutonsSignalement(message),
        ephemeral=True
    )

@bot.event
async def on_ready():
    synced = await bot.tree.sync()
    print(f"Bot connecte : {bot.user}")
    print(f"{len(synced)} commande(s) synchronisee(s)")

bot.run(TOKEN)