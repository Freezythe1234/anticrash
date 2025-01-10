import disnake
from disnake.ext import commands
import aiosqlite

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Показывает людей в вайт-листе")
    async def infowhitelist(self, inter: disnake.ApplicationCommandInteraction):
        async with aiosqlite.connect('database/main.db') as db:
            async with db.execute("SELECT user_id FROM whitelist") as cursor:
                rows = await cursor.fetchall()
                if rows:
                    user_list = [f"<@{row[0]}>" for row in rows]
                    embed = disnake.Embed(
                        title="Пользователи в вайт-листе",
                        description="\n".join(user_list),
                        color=disnake.Color.green()
                    )
                    await inter.response.send_message(embed=embed)
                else:
                    embed = disnake.Embed(
                        title="Пользователи в вайт-листе",
                        description="В вайт-листе нет пользователей.",
                        color=disnake.Color.red()
                    )
                    await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(Info(bot))
