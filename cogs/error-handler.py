import datetime
import disnake
from disnake.ext import commands
import json
import pytz

class Error(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("")
        print('•  {} | Loaded.'.format(self.__class__.__name__))

    @commands.Cog.listener()
    async def on_slash_command_error(self, interaction, error):
        if isinstance(error, commands.MissingAnyRole):
            embed = disnake.Embed(title="Ошибка", color=0x2b2d31)
            embed.add_field(name="", value=f"**{interaction.author.mention}, У вас нет прав для использования этой команды.**", inline=False)
            embed.set_thumbnail(interaction.author.avatar.url if interaction.author.avatar else interaction.author.default_avatar.url)
            await interaction.send(embed=embed, ephemeral=True)
        else:
            print(f"Произошла ошибка: {error}")
            embed = disnake.Embed(title="Ошибка", color=0x2b2d31)
            embed.add_field(name="", value=f"**{interaction.author.mention}, Произошла ошибка при выполнении команды.**", inline=False)
            embed.set_thumbnail(interaction.author.avatar.url if interaction.author.avatar else interaction.author.default_avatar.url)
            await interaction.send(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Error(bot))