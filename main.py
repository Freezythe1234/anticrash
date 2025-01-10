import json
import time
import disnake
from disnake.ext import commands
import os

# Подключаем все разрешения
intents = disnake.Intents.all()  
# Создаем экземпляр бота с установленным префиксом и разрешениями
bot = commands.Bot(command_prefix="!", intents=intents, test_guilds=[1297477436560379924]) 

# Загружаем токен из файла
with open('./!cfg/token.json', 'r') as file:
    data = json.load(file)
    TOKEN = data.get('token')

@bot.event
async def on_ready():
    print("")
    print("")
    print(f"• {time.strftime('%X')} | AntiNuke | Started")
    await bot.change_presence(status=disnake.Status.online, activity=disnake.Activity(type=disnake.ActivityType.watching, name=f"Защищает Aurait"))

# Загружаем расширения (cogs)
bot.load_extension('cogs.antinuke')
bot.load_extension('cogs.roles')
bot.load_extension('cogs.whitelist')
bot.load_extension('cogs.error-handler')
bot.load_extension('cogs.info')

# Запускаем бота
bot.run(TOKEN)
