import datetime
import json
import disnake
from disnake.ui import View
from disnake.ext import commands
import sqlite3
import asyncio

conn = sqlite3.connect('database/main.db')
cursor = conn.cursor()

import pytz
with open('json/settings.json', 'r', encoding='utf-8') as file:
    data_s = json.load(file)
class Role(commands.Cog):
    def __init__(self, bot):
        print("")
        print('•  {} | Loaded.'.format(self.__class__.__name__))
        self.bot = bot
        self.conn = sqlite3.connect('database/rolelist.db')
        self.cursor = self.conn.cursor()

        self.bot.loop.create_task(self.update_all_roles_members())

    async def update_all_roles_members(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            guild = self.bot.get_guild(data_s.get('guild_id'))

            if guild:
                roles = [role for role in guild.roles if not role.is_default()]

                self.delete_previous_tables()

                for role in roles:
                    members = role.members

                    table_name = f"role_{hash(role.id)}"
                    self.create_table_if_not_exists(table_name)

                    self.save_role_members(table_name, role.id, [member.id for member in members])

            await asyncio.sleep(10)

    def delete_previous_tables(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = self.cursor.fetchall()

        for table in tables:
            if table[0].startswith("role_") and not table[0].endswith("role_@everyone"):
                self.cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
                self.conn.commit()

    def create_table_if_not_exists(self, table_name):
        self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                role_id INTEGER,
                member_id INTEGER
            )
        ''')
        self.conn.commit()

    def save_role_members(self, table_name, role_id, member_ids):
        self.cursor.executemany(f"INSERT INTO {table_name} VALUES (?, ?)", [(role_id, member_id) for member_id in member_ids])
        self.conn.commit()

    async def restore_and_update_role(self, role):
        table_name = f"role_{hash(role.id)}"
        self.create_table_if_not_exists(table_name)

        self.cursor.execute(f"SELECT member_id FROM {table_name}")
        member_ids = [row[0] for row in self.cursor.fetchall()]

        new_role = await role.guild.create_role(name=role.name, color=role.color, permissions=role.permissions, mentionable=role.mentionable, hoist=role.hoist)

        await new_role.edit(position=role.position)

        for member_id in member_ids:
            member = role.guild.get_member(member_id)
            if member:
                await member.add_roles(new_role)

        await self.update_all_roles_members()

    async def assign_quarantine(self, member, reason):
        role = member.guild.get_role(data_s.get('role_ban_id'))
        logs = member.guild.get_channel(data_s.get('channel_id_logs'))
        await member.edit(roles=[])
        await member.add_roles(role)

        embed = disnake.Embed(title="AntiNuke", color=0x2B2D31)
        embed.add_field(name="> Нарушитель", value=f"* {member.mention} \n * Тег: {member.name} \n * ID:{member.id}", inline=True)
        embed.add_field(name="> Причина", value=f"```{reason}```", inline=False)
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"{member.name}", icon_url=member.avatar.url if member.avatar else member.default_avatar.url)
        await logs.send(embed=embed)

    def get_perm_whitelist(self, member, type):
        conn = sqlite3.connect('database/main.db')
        cursor = conn.cursor()
        cursor.execute("SELECT {} FROM whitelist WHERE user_id = ?".format(type), (member.id,))
        row = cursor.fetchone()
        if row:
            result = row[0]
            return result
        else:
            cursor.execute('''
                INSERT INTO whitelist (user_id, ping, web_upd, web_del, guild_upd, chan_cr, chan_del, chan_upd, memb_ub, memb_kk, add_bot, add_adm_role, role_cr, role_del, role_upd)
                VALUES (?, 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False', 'False')
            ''', (member.id,))
            conn.commit()
            cursor.execute("SELECT {} FROM whitelist WHERE user_id = ?".format(type), (member.id,))
            row = cursor.fetchone()
            if row:
                result = row[0]
                return result

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        guild = self.bot.get_guild(data_s.get('guild_id'))
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_delete):
                down = entry.user
                if down.id == data_s.get('bot_id'):
                    continue
                result = self.get_perm_whitelist(down, 'role_del')
                if result == 'False':
                    table_name = f"role_{hash(role.id)}"
                    self.create_table_if_not_exists(table_name)

                    self.cursor.execute(f"SELECT member_id FROM {table_name}")
                    member_ids = [row[0] for row in self.cursor.fetchall()]

                    new_role = await role.guild.create_role(name=role.name, color=role.color, permissions=role.permissions, mentionable=role.mentionable, hoist=role.hoist)

                    await new_role.edit(position=role.position)

                    for member_id in member_ids:
                        member = role.guild.get_member(member_id)
                        if member:
                            await member.add_roles(new_role)
                    await self.assign_quarantine(down, "Удаление роли")
                    await self.update_all_roles_members()
                elif result == 'True':
                    pass
    
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        changes = []

        if before.name != after.name:
            changes.append("Имя роли")
        if before.color != after.color:
            changes.append("Цвет роли")
        if before.permissions != after.permissions:
            changes.append("Разрешения роли")
        if before.mentionable != after.mentionable:
            changes.append("Возможность упоминания роли")
        if before.hoist != after.hoist:
            changes.append("Отображение роли отдельно")
        if before.icon != after.icon:
            changes.append("Иконка роли")

        if changes:
            async for entry in after.guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_update):
                member = entry.user
                if member.id == data_s.get('bot_id'):
                    continue
                result = self.get_perm_whitelist(member, 'role_upd')
                if result == 'False':
                    role_data = {}
                    for change in changes:
                        if change == "Имя роли":
                            role_data["name"] = before.name
                        elif change == "Цвет роли":
                            role_data["color"] = before.color
                        elif change == "Разрешения роли":
                            role_data["permissions"] = before.permissions
                        elif change == "Возможность упоминания роли":
                            role_data["mentionable"] = before.mentionable
                        elif change == "Отображение роли отдельно":
                            role_data["hoist"] = before.hoist
                        elif change == "Иконка роли":
                            role_data["icon"] = before.icon
                    await after.edit(**role_data)
                    await self.assign_quarantine(member, "Изменение роли")
                elif result == 'True':
                    pass
    
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        guild = self.bot.get_guild(data_s.get('guild_id'))
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.role_create):
                member = entry.user
                if member.id == data_s.get('bot_id'):
                    pass
                else:
                    result = self.get_perm_whitelist(member, 'role_cr')
                    if result == 'False':
                        await self.assign_quarantine(member, "Создание роли")
                        await role.delete()
                    elif result == 'True':
                        pass

def setup(bot):
    bot.add_cog(Role(bot))