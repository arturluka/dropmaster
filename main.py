import discord
from discord import app_commands
from discord.ext import commands
import random
import json
import os
import datetime

# ==========================
# CONFIGURAÇÃO DO BOT
# ==========================
TOKEN = os.getenv("MTQzOTQwMTU4NDExNDEzOTE2OQ.GJynQw.6JDP8E6Qhf6cDN_8MglAKaqC61bktIgGWPhVtk")

INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)

# ==========================
# BANCO DE DADOS
# ==========================
DB_FILE = "dropdata.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

db = load_db()

# ==========================
# FUNÇÕES DO SISTEMA
# ==========================

def get_user(user_id):
    user_id = str(user_id)
    if user_id not in db:
        db[user_id] = {
            "items": [],
            "coins": 0,
            "last_daily": "none"
        }
        save_db(db)
    return db[user_id]

def add_item(user_id, item):
    user = get_user(user_id)
    user["items"].append(item)
    save_db(db)

def add_coins(user_id, amount):
    user = get_user(user_id)
    user["coins"] += amount
    save_db(db)

def remove_coins(user_id, amount):
    user = get_user(user_id)
    if user["coins"] >= amount:
        user["coins"] -= amount
        save_db(db)
        return True
    return False

DROP_ITENS = [
    "💎 Gema Rara",
    "🔮 Orbe Místico",
    "💰 Saco de Ouro",
    "⚔️ Lâmina Antiga",
    "📜 Pergaminho Misterioso"
]

SHOP_ITEMS = {
    "poção": {"nome": "🏺 Poção de Vida", "preco": 50},
    "faca": {"nome": "🗡️ Faca de Caça", "preco": 100},
    "coroa": {"nome": "👑 Coroa Antiga", "preco": 500}
}

# ==========================
# DROP AUTOMÁTICO
# ==========================

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if random.randint(1, 30) == 1:
        item = random.choice(DROP_ITENS)
        add_item(message.author.id, item)
        await message.channel.send(f"🎁 **DROP!** {message.author.mention} encontrou **{item}**!")

    await bot.process_commands(message)

# ==========================
# COMANDOS DO BOT
# ==========================

@bot.tree.command(name="inventario", description="Mostra seu inventário.")
async def inventario(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    items = user["items"]

    if not items:
        await interaction.response.send_message("📦 Seu inventário está vazio.")
        return

    inv = "\n".join(f"- {i}" for i in items)
    await interaction.response.send_message(f"🎒 **Inventário:**\n{inv}")

# ---- LOJA ----
@bot.tree.command(name="loja", description="Itens disponíveis para compra.")
async def loja(interaction: discord.Interaction):
    texto = "\n".join([f"- **{i}** → {d['nome']} ({d['preco']} moedas)" for i, d in SHOP_ITEMS.items()])
    await interaction.response.send_message(f"🛒 **Loja do DropMaster:**\n{texto}")

# ---- ECONOMIA ----
@bot.tree.command(name="moedas", description="Mostra quantas moedas você tem.")
async def moedas(interaction: discord.Interaction):
    coins = get_user(interaction.user.id)["coins"]
    await interaction.response.send_message(f"💰 Você tem **{coins} moedas**.")

@bot.tree.command(name="daily", description="Coleta moedas diárias.")
async def daily(interaction: discord.Interaction):
    user = get_user(interaction.user.id)
    hoje = str(datetime.date.today())

    if user["last_daily"] == hoje:
        await interaction.response.send_message("⏳ Você já coletou sua daily hoje!")
        return

    user["last_daily"] = hoje
    add_coins(interaction.user.id, 150)
    await interaction.response.send_message("🎉 Você recebeu **150 moedas**!")

@bot.tree.command(name="transferir", description="Transfere moedas para outro usuário.")
async def transferir(interaction: discord.Interaction, usuario: discord.User, quantia: int):
    if quantia <= 0:
        await interaction.response.send_message("Valor inválido.")
        return

    if not remove_coins(interaction.user.id, quantia):
        await interaction.response.send_message("❌ Você não tem moedas suficientes.")
        return

    add_coins(usuario.id, quantia)
    await interaction.response.send_message(f"💸 Você transferiu **{quantia} moedas** para {usuario.mention}.")

# ---- COMPRA / VENDA ----
@bot.tree.command(name="comprar", description="Compra um item da loja.")
async def comprar(interaction: discord.Interaction, item: str):
    item = item.lower()
    if item not in SHOP_ITEMS:
        await interaction.response.send_message("❌ Item inexistente.")
        return

    preco = SHOP_ITEMS[item]["preco"]

    if not remove_coins(interaction.user.id, preco):
        await interaction.response.send_message("❌ Moedas insuficientes.")
        return

    add_item(interaction.user.id, SHOP_ITEMS[item]["nome"])
    await interaction.response.send_message(f"✅ Você comprou **{SHOP_ITEMS[item]['nome']}**!")

@bot.tree.command(name="vender", description="Vende um item do seu inventário.")
async def vender(interaction: discord.Interaction, nome: str):
    user = get_user(interaction.user.id)

    if nome not in user["items"]:
        await interaction.response.send_message("❌ Você não tem esse item.")
        return

    user["items"].remove(nome)
    add_coins(interaction.user.id, 20)
    save_db(db)

    await interaction.response.send_message(f"💰 Você vendeu **{nome}** por 20 moedas.")

# ---- DROPS ----
@bot.tree.command(name="drop", description="Força um drop manual.")
async def drop(interaction: discord.Interaction):
    item = random.choice(DROP_ITENS)
    add_item(interaction.user.id, item)
    await interaction.response.send_message(f"🎁 **DROP!** Você encontrou **{item}**!")

@bot.tree.command(name="evento_drop", description="Evento de drop global (ADMIN).")
@commands.has_permissions(administrator=True)
async def evento_drop(interaction: discord.Interaction):
    for member in interaction.guild.members:
        if not member.bot:
            add_item(member.id, random.choice(DROP_ITENS))
    await interaction.response.send_message("🎉 **EVENTO DE DROP GLOBAL ATIVADO!**")

# ---- RANKINGS ----
@bot.tree.command(name="ranking_itens", description="Ranking de quem tem mais itens.")
async def ranking_itens(interaction: discord.Interaction):
    ranking = sorted(db.items(), key=lambda x: len(x[1]["items"]), reverse=True)
    txt = "\n".join([f"**{bot.get_user(int(uid))}** — {len(data['items'])} itens" for uid, data in ranking[:10]])
    await interaction.response.send_message(f"🏆 **TOP 10 em itens:**\n{txt}")

@bot.tree.command(name="ranking_moedas", description="Ranking de quem tem mais moedas.")
async def ranking_moedas(interaction: discord.Interaction):
    ranking = sorted(db.items(), key=lambda x: x[1]["coins"], reverse=True)
    txt = "\n".join([f"**{bot.get_user(int(uid))}** — {data['coins']} moedas" for uid, data in ranking[:10]])
    await interaction.response.send_message(f"💰 **TOP 10 mais ricos:**\n{txt}")

# ---- ADMINISTRAÇÃO ----
@bot.tree.command(name="limparinventario", description="Zera inventário de alguém (ADMIN).")
@commands.has_permissions(administrator=True)
async def limparinventario(interaction: discord.Interaction, usuario: discord.User):
    user = get_user(usuario.id)
    user["items"] = []
    save_db(db)

    await interaction.response.send_message(f"🗑️ Inventário de {usuario.mention} apagado.")

@bot.tree.command(name="setmoedas", description="Define a quantidade de moedas de um usuário (ADMIN).")
@commands.has_permissions(administrator=True)
async def setmoedas(interaction: discord.Interaction, usuario: discord.User, quantia: int):
    user = get_user(usuario.id)
    user["coins"] = quantia
    save_db(db)
    await interaction.response.send_message(f"💰 Moedas de {usuario.mention} definidas para {quantia}.")

@bot.tree.command(name="additem", description="Adiciona item manualmente (ADMIN).")
@commands.has_permissions(administrator=True)
async def additem(interaction: discord.Interaction, usuario: discord.User, item: str):
    add_item(usuario.id, item)
    await interaction.response.send_message(f"🎁 Item **{item}** adicionado para {usuario.mention}.")

# ==========================
# INICIALIZAÇÃO
# ==========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 DropMaster Online como {bot.user}!")

bot.run(TOKEN)
