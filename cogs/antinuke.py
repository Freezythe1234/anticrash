import datetime
import re
import disnake
from disnake.ext import commands
import json
import pytz
from disnake.ui import View, Button
import sqlite3

with open('json/settings.json', 'r', encoding='utf-8') as file:
    data_s = json.load(file)

class AntiNuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("")
        print('•  {} | Loaded.'.format(self.__class__.__name__))
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
    
    def has_admin_permissions(self, role):
        return role.permissions.administrator

    async def get_inviter(self, member):
        invites = await member.guild.invites()
        async for entry in member.guild.audit_logs(limit=1, action=disnake.AuditLogAction.invite_create):
            if entry.target.code in [invite.code for invite in invites]:
                return entry.user
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        user = message.author
        content = message.content.lower()
        
        if "everyone" in content or "here" in content:
            result_ping = self.get_perm_whitelist(user, 'ping')
            if result_ping == 'False':
                await message.delete()
                await self.assign_quarantine(user, "Упоминание роли с большим количеством участников")
            
        discord_link_pattern = r'discord\.gg\/\w+'
        if re.search(discord_link_pattern, content):
            result_link = self.get_perm_whitelist(user, 'ping')
            if result_link == 'False':
                await message.delete()
                await self.assign_quarantine(user, "Ссылка на другой Discord сервер")

    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        if isinstance(channel, disnake.TextChannel):
            webhooks_after_update = await channel.webhooks()

            for webhook_after_update in webhooks_after_update:
                if webhook_after_update.user.id == data_s.get('bot_id'):
                    continue
                member = channel.guild.get_member(webhook_after_update.user.id)
                if member:
                    result = self.get_perm_whitelist(member, 'web_upd')
                    if result == 'False':
                        await webhook_after_update.delete()
                        await self.assign_quarantine(member, "Изменение/Создание вебхуков")
                    elif result == 'True':
                        pass

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append("Имя сервера")
        if before.description != after.description:
            changes.append("Описание сервера")
        if before.icon != after.icon:
            changes.append("Иконку сервера")
        if before.banner != after.banner:
            changes.append("Баннер сервера")
        if before.splash != after.splash:
            changes.append("Изображение приглашения сервера")
        if before.discovery_splash != after.discovery_splash:
            changes.append("Изображение для поиска сервера")
        if before.afk_channel != after.afk_channel:
            changes.append("Канал AFK")
        if before.afk_timeout != after.afk_timeout:
            changes.append("Таймаут AFK")
        if before.default_notifications != after.default_notifications:
            changes.append("Стандартные уведомления")
        if before.verification_level != after.verification_level:
            changes.append("Уровень верификации")
        if before.explicit_content_filter != after.explicit_content_filter:
            changes.append("Фильтр эксплицитного контента")
        if before.system_channel != after.system_channel:
            changes.append("Системный канал")
        if before.system_channel_flags != after.system_channel_flags:
            changes.append("Флаги системного канала")
        if before.preferred_locale != after.preferred_locale:
            changes.append("Локал по умолчанию")
        if before.rules_channel != after.rules_channel:
            changes.append("Правила сервера")
        if before.public_updates_channel != after.public_updates_channel:
            changes.append("Канал обновлений сервера")
        if before.premium_progress_bar_enabled != after.premium_progress_bar_enabled:
            changes.append("Наличие прогресс-бара подписки")

        if changes:
            async for entry in after.audit_logs(limit=1, action=disnake.AuditLogAction.guild_update):
                member = entry.user
                if member.id == data_s.get('bot_id'):
                    continue
                result = self.get_perm_whitelist(member, 'guild_upd')
                if result == 'False':
                    await self.assign_quarantine(member, f"Изменение параметров сервера: {', '.join(changes)}")
                    try:
                        if "Имя сервера" in changes:
                            await after.edit(name=before.name)
                        if "Описание сервера" in changes:
                            await after.edit(description=before.description)
                        if "Иконку сервера" in changes:
                            await after.edit(icon=before.icon)
                        if "Баннер сервера" in changes:
                            await after.edit(banner=before.banner)
                        if "Изображение приглашения сервера" in changes:
                            await after.edit(splash=before.splash)
                        if "Канал AFK" in changes:
                            await after.edit(afk_channel=before.afk_channel)
                        if "Таймаут AFK" in changes:
                            await after.edit(afk_timeout=before.afk_timeout)
                        if "Стандартные уведомления" in changes:
                            await after.edit(default_notifications=before.default_notifications)
                        if "Уровень верификации" in changes:
                            await after.edit(verification_level=before.verification_level)
                        if "Фильтр эксплицитного контента" in changes:
                            await after.edit(explicit_content_filter=before.explicit_content_filter)
                        if "Системный канал" in changes:
                            await after.edit(system_channel=before.system_channel)
                        if "Флаги системного канала" in changes:
                            await after.edit(system_channel_flags=before.system_channel_flags)
                        if "Локал по умолчанию" in changes:
                            await after.edit(preferred_locale=before.preferred_locale)
                        if "Правила сервера" in changes:
                            await after.edit(public_updates_channel=before.public_updates_channel)
                        if "Канал обновлений сервера" in changes:
                            await after.edit(public_updates_channel=before.public_updates_channel)
                        if "Наличие прогресс-бара подписки" in changes:
                            await after.edit(premium_progress_bar_enabled=before.premium_progress_bar_enabled)
                    except Exception as e:
                        print(f"Ошибка при восстановлении значений: {e}")
                elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        async for entry in channel.guild.audit_logs(limit=1, action=disnake.AuditLogAction.channel_create):
            creator = entry.user
            if creator.id != data_s.get('bot_id'):
                result = self.get_perm_whitelist(creator, 'chan_cr')
                if result == 'False':
                    await self.assign_quarantine(creator, "Создание нового канала")
                    await channel.delete()
                elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        async for entry in channel.guild.audit_logs(limit=1, action=disnake.AuditLogAction.channel_delete):
            user = entry.user
            if user.id != data_s.get('bot_id'):
                result = self.get_perm_whitelist(user, 'chan_del')
                if result == 'False':
                    await channel.clone()
                    await self.assign_quarantine(user, "Удаление канала")
                elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        async for entry in before.guild.audit_logs(limit=1, action=disnake.AuditLogAction.overwrite_update):
            creator = entry.user
            if creator.id != data_s.get('bot_id'):
                result = self.get_perm_whitelist(creator, 'chan_upd')
                if result == 'False':
                    await self.assign_quarantine(entry.user, "Изменение прав канала")
                    await after.edit(overwrites=before.overwrites)
                elif result == 'True':
                    pass
        async for entry in before.guild.audit_logs(limit=1, action=disnake.AuditLogAction.overwrite_create):
            creator = entry.user
            if creator.id != data_s.get('bot_id'):
                result = self.get_perm_whitelist(creator, 'chan_upd')
                if result == 'False':
                    await self.assign_quarantine(entry.user, "Добавление прав канала")
                    await after.edit(overwrites=before.overwrites)
                elif result == 'True':
                    pass
        async for entry in before.guild.audit_logs(limit=1, action=disnake.AuditLogAction.overwrite_delete):
            creator = entry.user
            if creator.id != data_s.get('bot_id'):
                result = self.get_perm_whitelist(creator, 'chan_upd')
                if result == 'False':
                    await self.assign_quarantine(entry.user, "Удаление прав канала")
                    await after.edit(overwrites=before.overwrites)
                elif result == 'True':
                    pass
        async for entry in before.guild.audit_logs(limit=1, action=disnake.AuditLogAction.channel_update):
            creator = entry.user
            if creator.id != data_s.get('bot_id'):
                result = self.get_perm_whitelist(creator, 'chan_upd')
                if result == 'False':
                    if before.type == disnake.ChannelType.text:
                        if before.name != after.name:
                            await after.edit(name=before.name)
                        if before.position != after.position:
                            await after.edit(position=before.position)
                        if before.nsfw != after.nsfw:
                            await after.edit(nsfw=before.nsfw)
                        if before.slowmode_delay != after.slowmode_delay:
                            await after.edit(slowmode_delay=before.slowmode_delay)
                        if before.category != after.category:
                            await after.edit(category=before.category)
                    elif before.type == disnake.ChannelType.news:
                        if before.name != after.name:
                            await after.edit(name=before.name)
                        if before.position != after.position:
                            await after.edit(position=before.position)
                        if before.nsfw != after.nsfw:
                            await after.edit(nsfw=before.nsfw)
                        if before.slowmode_delay != after.slowmode_delay:
                            await after.edit(slowmode_delay=before.slowmode_delay)
                        if before.category != after.category:
                            await after.edit(category=before.category)
                    elif before.type == disnake.ChannelType.voice:
                        if before.name != after.name:
                            await after.edit(name=before.name)
                        if before.position != after.position:
                            await after.edit(position=before.position)
                        if before.nsfw != after.nsfw:
                            await after.edit(nsfw=before.nsfw)
                        if before.slowmode_delay != after.slowmode_delay:
                            await after.edit(slowmode_delay=before.slowmode_delay)
                        if before.category != after.category:
                            await after.edit(category=before.category)
                        if before.user_limit != after.user_limit:
                            await after.edit(user_limit=before.user_limit)
                        if before.bitrate != after.bitrate:
                            await after.edit(bitrate=before.bitrate)
                        if before.rtc_region != after.rtc_region:
                            await after.edit(rtc_region=before.rtc_region)
                        if before.video_quality_mode != after.video_quality_mode:
                            await after.edit(video_quality_mode=before.video_quality_mode)
                    await self.assign_quarantine(entry.user, "Изменение канала")
                elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        async for entry in guild.audit_logs(limit=1, action=disnake.AuditLogAction.unban):
            if entry.target.id == user.id:
                result = self.get_perm_whitelist(entry.user, 'memb_ub')
                if result == 'False':
                    await self.assign_quarantine(entry.user, f"Снятие пкм бана")
                    await guild.ban(user, reason="AntiNuke Sistem")
                    break
                elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        async for entry in member.guild.audit_logs(limit=1, action=disnake.AuditLogAction.kick):
            if entry.target.id == member.id:
                result = self.get_perm_whitelist(entry.user, 'memb_kk')
                if result == 'False':
                    await self.assign_quarantine(entry.user, f"Пкм кик")
                elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            inviter = await self.get_inviter(member)
            result = self.get_perm_whitelist(inviter, 'add_bot')
            if result == 'False':
                await self.assign_quarantine(inviter, "Приглашение бота")
                await member.guild.ban(member, reason="AntiNuke Sistem")
            elif result == 'True':
                    pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if len(after.roles) > len(before.roles):
            new_role = next(role for role in after.roles if role not in before.roles)
            if self.has_admin_permissions(new_role):
                async for entry in before.guild.audit_logs(limit=1, action=disnake.AuditLogAction.member_role_update):
                    if new_role in entry.changes.after.roles:
                        result = self.get_perm_whitelist(entry.user, 'add_adm_role')
                        if result == 'False':
                            await after.remove_roles(new_role)
                            await self.assign_quarantine(entry.user, "Выдача роли с админ правами")
                        elif result == 'True':
                            pass

    @commands.slash_command(description="Показать настройки вайт-листа и описание действий")
    async def setting(self, inter: disnake.ApplicationCommandInteraction):
        embed = disnake.Embed(
        title="Настройки Вайт-Листа",
        description="Здесь показаны текущие настройки вайт-листа и описание действий.",
        color=0x2B2D31
    )
    
        embed.add_field(name="Карантин", value="На каждое запрещённое действие пользователя бот выдаёт карантин!", inline=False)
    
        await inter.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(AntiNuke(bot))