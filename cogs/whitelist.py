import disnake
from disnake.ext import commands
from disnake.ui import Button, View, Select
import sqlite3

conn = sqlite3.connect('database/main.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS whitelist (
        user_id INTEGER PRIMARY KEY,
        ping TEXT,
        web_upd TEXT,
        web_del TEXT,
        guild_upd TEXT,
        chan_cr TEXT,
        chan_del TEXT,
        chan_upd TEXT,
        memb_ub TEXT,
        memb_kk TEXT,
        add_bot TEXT,
        add_adm_role TEXT,
        role_cr TEXT,
        role_del TEXT,
        role_upd TEXT
    )
''')
conn.commit()

class WhitelistSelect(Select):
    def __init__(self, permissions, member):
        self.permissions = permissions
        self.member = member
        
        options = [
            disnake.SelectOption(label=f"{desc}", value=key) 
            for key, (desc, value) in permissions.items() if value == 'False'
        ]
        super().__init__(placeholder="Выберите права для изменения", options=options, max_values=len(options))

    async def callback(self, interaction: disnake.Interaction):
        selected_permissions = self.values
        selected_permission_names = [option.label.split(' = ')[0] for option in self.options if option.value in selected_permissions]
        embed2 = disnake.Embed(color=0x2B2D31)
        embed2.add_field(name="", value=f"**<@{interaction.author.id}>, Вы выбрали следующие изменения `{', '.join(selected_permission_names)}` для участника <@{self.member.id}>.**", inline=True)
        embed2.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed2.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.guild.default_icon.url)
        await interaction.response.edit_message(embed=embed2, view = None)

        for permission in selected_permissions:
            cursor.execute(f"UPDATE whitelist SET {permission} = 'True' WHERE user_id = ?", (self.member.id,))
        conn.commit()

class WhitelistDelSelect(Select):
    def __init__(self, permissions, member):
        self.permissions = permissions
        self.member = member
        
        options = [
            disnake.SelectOption(label=f"{desc}", value=key) 
            for key, (desc, value) in permissions.items() if value == 'True'
        ]
        super().__init__(placeholder="Выберите права для изменения", options=options, max_values=len(options))

    async def callback(self, interaction: disnake.Interaction):
        selected_permissions = self.values
        selected_permission_names = [option.label.split(' = ')[0] for option in self.options if option.value in selected_permissions]
        embed2 = disnake.Embed(color=0x2B2D31)
        embed2.add_field(name="", value=f"**<@{interaction.author.id}>, Вы выбрали следующие изменения `{', '.join(selected_permission_names)}` для участника <@{self.member.id}>.**", inline=True)
        embed2.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed2.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.guild.default_icon.url)
        await interaction.response.edit_message(embed=embed2, view = None)

        for permission in selected_permissions:
            cursor.execute(f"UPDATE whitelist SET {permission} = 'False' WHERE user_id = ?", (self.member.id,))
        conn.commit()

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("")
        print('•  {} | Загружено.'.format(self.__class__.__name__))

    async def check_all_true(self, member_id):
        cursor.execute("SELECT * FROM whitelist WHERE user_id = ?", (member_id,))
        row = cursor.fetchone()
        if row:
            return all(value == 'True' for value in row[1:])
        return False
    async def check_all_false(self, member_id):
        cursor.execute("SELECT * FROM whitelist WHERE user_id = ?", (member_id,))
        row = cursor.fetchone()
        if row:
            return all(value == 'False' for value in row[1:])
        return True

    @commands.slash_command(name="whitelist", description="Меню Вайт листа")
    async def whitelist(self, interaction, пользователь: disnake.Member):
        member = пользователь
        author = interaction.author

        cursor.execute("SELECT * FROM whitelist WHERE user_id = ?", (member.id,))
        row = cursor.fetchone()

        if row is None:
            cursor.execute('''
                INSERT INTO whitelist (user_id, ping, web_upd, web_del, guild_upd, chan_cr, chan_del, chan_upd, memb_ub, memb_kk, add_bot, add_adm_role, role_cr, role_del, role_upd)
                VALUES (?, 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False')
            ''', (member.id,))
            conn.commit()
            cursor.execute("SELECT * FROM whitelist WHERE user_id = ?", (member.id,))
            row = cursor.fetchone()

        permissions = {
            'ping': ('Упоминание everyone и here, ссылки на сервера', row[1]),
            'web_upd': ('Обновление/Создание вебхуков', row[2]),
            'web_del': ('Удаление вебхуков', row[3]),
            'guild_upd': ('Обновление сервера', row[4]),
            'chan_cr': ('Создание канала', row[5]),
            'chan_del': ('Удаление канала', row[6]),
            'chan_upd': ('Обновление канала', row[7]),
            'memb_ub': ('Разбан участника из пкм бана', row[8]),
            'memb_kk': ('Кик участника с сервера', row[9]),
            'add_bot': ('Добавление ботов на сервер', row[10]),
            'add_adm_role': ('Выдача роли с админ правами', row[11]),
            'role_cr': ('Создание роли', row[12]),
            'role_del': ('Удаление роли', row[13]),
            'role_upd': ('Обновление роли', row[14]),
        }

        all_true = await self.check_all_true(member.id)
        all_false = await self.check_all_false(member.id)

        embed1 = disnake.Embed(color=0x2B2D31)
        embed1.add_field(name="", value=f"**<@{interaction.author.id}>, Выберите взаимодействие с вайт листом пользователя <@{member.id}>**", inline=True)
        embed1.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed1.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.guild.default_icon.url)

        add = Button(style=disnake.ButtonStyle.gray, label='Выдать', disabled=all_true)
        dell = Button(style=disnake.ButtonStyle.gray, label='Снять', disabled=all_false)
        cancel = Button(style=disnake.ButtonStyle.danger, label='Отмена', row=2)

        view_one = View(timeout=None)
        view_one.add_item(add)
        view_one.add_item(dell)
        view_one.add_item(cancel)
        await interaction.response.send_message(embed=embed1, view=view_one)

        async def add_callback(button_interaction):
            if button_interaction.user.id == author.id:
                embed2 = disnake.Embed(color=0x2B2D31)
                embed2.add_field(name="", value=f"**<@{interaction.author.id}>, Выберите что хотите ему добавить в вайт лист пользователю <@{member.id}>**", inline=True)
                embed2.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
                embed2.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.guild.default_icon.url)
                view_two = View(timeout=None)
                view_two.add_item(WhitelistSelect(permissions, member))
                await button_interaction.response.edit_message(embed=embed2, view=view_two)

        add.callback = add_callback

        async def dell_callback(button_interaction):
            if button_interaction.user.id == author.id:
                embed2 = disnake.Embed(color=0x2B2D31)
                embed2.add_field(name="", value=f"**<@{interaction.author.id}>, Выберите что хотите ему убрать из вайт листа у пользователя <@{member.id}>**", inline=True)
                embed2.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
                embed2.set_author(name=f"{interaction.guild.name}", icon_url=interaction.guild.icon.url if interaction.guild.icon else interaction.guild.default_icon.url)
                view_three = View(timeout=None)
                view_three.add_item(WhitelistDelSelect(permissions, member))
                await button_interaction.response.edit_message(embed=embed2, view=view_three)

        dell.callback = dell_callback

        async def cancel_callback(button_interaction):
            if button_interaction.user.id == author.id:
                await button_interaction.message.delete()

        cancel.callback = cancel_callback

    

def setup(bot):
    bot.add_cog(Whitelist(bot))