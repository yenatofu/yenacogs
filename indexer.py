import asyncio
import json
import os
import re
from datetime import datetime

import discord
from discord.ext import commands

from cogs.utils import checks

# Copyright 2018 Kixiron
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

PATH_LIST = ['data', 'kixkogs']
PATH = os.path.join(*PATH_LIST)
SERVER_INDEX_PATH_LIST = ['data', 'kixkogs', 'server_index']
SERVER_INDEX_PATH = os.path.join(*SERVER_INDEX_PATH_LIST)
MEMBER_INDEX_PATH_LIST = ['data', 'kixkogs', 'member_index']
MEMBER_INDEX_PATH = os.path.join(*MEMBER_INDEX_PATH_LIST)
EMOJI_INDEX_PATH_LIST = ['data', 'kixkogs', 'emoji_index']
EMOJI_INDEX_PATH = os.path.join(*EMOJI_INDEX_PATH_LIST)


class Indexer:
    """Indexes servers and members that the bot is in"""

    def __init__(self, bot):
        self.bot = bot


    async def search_server(self, ctx, server_id):
        if server_id == None:
            if ctx.message.server != None:
                return ctx.message.server
            else:
                await self.bot.say("I need a server id to index a server!")
                return None
        else:
            for s in self.bot.servers:
                if server_id == s.id:
                    return s


    async def search_members(self, ctx, member_id):
        if member_id == None:
            await self.bot.say("Indexing you")
            return ctx.message.author
        else:
            for s in self.bot.servers:
                for m in s.members:
                    if member_id == m.id:
                        await self.bot.say("Indexing {}#{}".format(m.name, m.discriminator))
                        return m


    async def check_server(self, server, member):
        for m in server.members:
            if member.id == m.id:
                return True
        return False


    async def get_server_member(self, server, member):
        for m in server.members:
            if member.id == m.id:
                return m


    async def write_file(self, path, file):
        with open(path, '+a') as outfile:
            json.dump(file, outfile, indent=4)


    async def check_for_file(self, path):
        try:
            os.remove(path)
        except OSError:
            pass

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def indexserver(self, ctx, server_id=None):
        """
        Index a server
        If the command is used in a server without specifing a server id,
        then the current server will be indexed
        Bot must be in a server to index it

        Format:
        [indexserver {server_id}]
        """
        server = await self.search_server(ctx, server_id)
        if server == None:
            return

        server_index = {}
        server_index['server'] = []
        server_index['server'].append("{} ({})".format(server.name, server.id))
        server_index['server'].append("Icon: [{}]".format(server.icon_url))
        server_index['server'].append("Owner: {}#{} ({})".format(
            server.owner.name, server.owner.discriminator, server.owner.id))
        server_index['server'].append(
            "Members: {}".format(server.member_count))
        server_index['members'] = []

        member_num = 0
        for m in server.members:
            member_num += 1

            if m.name == m.display_name:
                server_index['members'].append(
                    "{}#{} ({})".format(m.name, m.discriminator, m.id))
            else:
                server_index['members'].append("{}#{} ({}) [{}]".format(
                    m.name, m.discriminator, m.id, m.display_name))

        server_index['members'].insert(
            0, "Format: member name#member discriminator (member id) [member nickname]")
        server_index['members'].insert(
            0, "Total Members: {}".format(member_num))
        server_index['channels'] = []

        channel_num = 0
        for c in server.channels:
            channel_num += 1

            if c.topic != None:
                server_index['channels'].insert(
                    c.position, "[{}] {} ({}) [{}]".format(c.type, c.name, c.id, c.topic))
            else:
                server_index['channels'].insert(
                    c.position, "[{}] {} ({})".format(c.type, c.name, c.id))

        server_index['channels'].insert(
            0, "Format: [channel type] channel name (channel id) [channel topic]")
        server_index['channels'].insert(
            0, "Total Channels: {}".format(channel_num))
        server_index['roles'] = []

        role_num = 0
        for r in server.roles:
            role_num += 1
            server_index['roles'].insert(
                r.position, "{} ({}) [{}]".format(r.name, r.id, r.position))

        server_index['roles'].insert(0, "Format: role name (role id)")
        server_index['roles'].insert(0, "Total Roles: {}".format(role_num))

        server_index['server'].append("Channels: {}".format(channel_num))
        server_index['server'].append("Roles: {}".format(role_num))

        path = os.path.join(SERVER_INDEX_PATH, "{}.json".format(server.id))
        await self.check_for_file(path)
        await self.write_file(path, server_index)

        em = discord.Embed(color=0x1e2dd4,
                           title="Finished Indexing Server")
        em.set_thumbnail(url=server.icon_url)
        em.add_field(name="Server:",
                     value="{} ({})".format(server.name, server.id),
                     inline=False)
        em.add_field(name="Owner:",
                     value="{}#{} ({})".format(server.owner.name,
                                               server.owner.discriminator, server.owner.id),
                     inline=False)
        em.add_field(name="Created At:",
                     value="{}".format(str(server.created_at).split(" ")[0]),
                     inline=True)
        em.add_field(name="Total Members:",
                     value="{}".format(server.member_count),
                     inline=True)
        em.add_field(name="Total Roles:",
                     value="{}".format(role_num),
                     inline=True)
        em.add_field(name="Total Channels:",
                     value="{}".format(channel_num),
                     inline=True)
        em.set_footer(
            text="Data only represents servers that {} is in".format(self.bot.user.name))

        await self.bot.say(embed=em)
        await self.bot.send_file(ctx.message.channel, path)

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def indexmember(self, ctx, member: discord.User):
        """
        Index a member
        If the command is used without specifing a member, 
        then you will be indexed
        Bot can only index data from servers that it is in

        Format:
        [indexmember {member}]
        """

        member_index = {}
        member_index['member_info'] = []
        member_index['member_info'].append("{}#{} ({})".format(
            member.name, member.discriminator, member.id))
        member_index['servers'] = {}

        total_servers = 0
        total_roles = 0
        for s in self.bot.servers:
            if await self.check_server(s, member) == True:
                member_index['servers']['{}'.format(s.name)] = []
                total_servers += 1
                server_member = await self.get_server_member(s, member)

                server_roles = 0
                for r in server_member.roles:
                    server_roles += 1
                    total_roles += 1
                    member_index['servers']['{}'.format(
                        s.name)].append("{}".format(r.name))

                if server_member.display_name != member.name:
                    member_index['servers']['{}'.format(s.name)].insert(
                        0, "Nickname: {}".format(server_member.display_name))

        member_index['member_info'].append("{} is in {} servers that {} is in.".format(
            member.name, total_servers, self.bot.user.name))
        member_index['member_info'].append("{} has {} total roles in the servers that {} is in".format(
            member.name, total_roles, self.bot.user.name))

        path = os.path.join(MEMBER_INDEX_PATH, "{}.json".format(member.id))
        await self.check_for_file(path)
        await self.write_file(path, member_index)

        em = discord.Embed(color=0x1e2dd4,
                           title="Finished Indexing Member")
        em.set_thumbnail(url=member.avatar_url)
        em.add_field(name="Member:",
                     value="{} ({})".format(member.name, member.id),
                     inline=False)
        em.add_field(name="Created At:",
                     value="{}".format(str(member.created_at).split(" ")[0]),
                     inline=True)
        em.add_field(name="Total Servers:",
                     value="{}".format(total_servers),
                     inline=True)
        em.add_field(name="Total Roles:",
                     value="{}".format(total_roles),
                     inline=True)
        em.set_footer(
            text="Data only represents servers that {} is in".format(self.bot.user.name))

        await self.bot.say(embed=em)
        await self.bot.send_file(ctx.message.channel, path)

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def indexallmembers(self, ctx, server_id=None):
        """
        Index the members in a server
        If the command is used without specifing a server id, 
        then the current server will be indexed
        Bot can only index data from servers that it is in

        Format:
        [indexservermembers {member_id}]
        """
        server = await self.search_server(ctx, server_id)

        total_members = 0
        members_indexed = 0

        for member in server.members:
            total_members += 1

        indexed = await self.bot.say("{}/{} Servers Indexed...".format(members_indexed, total_members))

        for member in server.members:
            members_indexed += 1
            member_index = {}
            member_index['member_info'] = []
            member_index['member_info'].append("{}#{} ({})".format(
                member.name, member.discriminator, member.id))
            member_index['servers'] = {}

            total_servers = 0
            total_roles = 0
            for s in self.bot.servers:
                if await self.check_server(s, member) == True:
                    member_index['servers']['{}'.format(s.name)] = []
                    total_servers += 1
                    server_member = await self.get_server_member(s, member)

                    server_roles = 0
                    for r in server_member.roles:
                        server_roles += 1
                        total_roles += 1
                        member_index['servers']['{}'.format(
                            s.name)].append("{}".format(r.name))

                    if server_member.display_name != member.name:
                        member_index['servers']['{}'.format(s.name)].insert(
                            0, "Nickname: {}".format(server_member.display_name))

            member_index['member_info'].append("{} is in {} servers that {} is in.".format(
                member.name, total_servers, self.bot.user.name))
            member_index['member_info'].append("{} has {} total roles in the servers that {} is in".format(
                member.name, total_roles, self.bot.user.name))

            path = os.path.join(MEMBER_INDEX_PATH, "{}.json".format(member.id))
            await self.check_for_file(path)
            await self.write_file(path, member_index)

            await self.bot.edit_message(indexed, new_content="{}/{} Members Indexed...".format(members_indexed, total_members))
            await asyncio.sleep(1)
        await self.bot.edit_message(indexed, new_content="{}/{} Members Indexed... Done!".format(members_indexed, total_members))

    @commands.command(pass_context=True, hidden=True)
    @checks.is_owner()
    async def indexallservers(self, ctx):

        total_servers = 0
        servers_indexed = 0
        for server in self.bot.servers:
            total_servers += 1

        indexed = await self.bot.say("{}/{} Members Indexed...".format(servers_indexed, total_servers))

        for server in self.bot.servers:
            servers_indexed += 1

            server_index = {}
            server_index['server'] = []
            server_index['server'].append(
                "{} ({})".format(server.name, server.id))
            server_index['server'].append("Icon: [{}]".format(server.icon_url))
            server_index['server'].append("Owner: {}#{} ({})".format(
                server.owner.name, server.owner.discriminator, server.owner.id))
            server_index['server'].append(
                "Members: {}".format(server.member_count))
            server_index['members'] = []

            member_num = 0
            for m in server.members:
                member_num += 1

                if m.name == m.display_name:
                    server_index['members'].append(
                        "{}#{} ({})".format(m.name, m.discriminator, m.id))
                else:
                    server_index['members'].append("{}#{} ({}) [{}]".format(
                        m.name, m.discriminator, m.id, m.display_name))

            server_index['members'].insert(
                0, "Format: member name#member discriminator (member id) [member nickname]")
            server_index['members'].insert(
                0, "Total Members: {}".format(member_num))
            server_index['channels'] = []

            channel_num = 0
            for c in server.channels:
                channel_num += 1

                if c.topic != None:
                    server_index['channels'].insert(
                        c.position, "[{}] {} ({}) [{}]".format(c.type, c.name, c.id, c.topic))
                else:
                    server_index['channels'].insert(
                        c.position, "[{}] {} ({})".format(c.type, c.name, c.id))

            server_index['channels'].insert(
                0, "Format: [channel type] channel name (channel id) [channel topic]")
            server_index['channels'].insert(
                0, "Total Channels: {}".format(channel_num))
            server_index['roles'] = []

            role_num = 0
            for r in server.roles:
                role_num += 1
                server_index['roles'].insert(
                    r.position, "{} ({})".format(r.name, r.id))

            server_index['roles'].insert(0, "Format: role name (role id)")
            server_index['roles'].insert(0, "Total Roles: {}".format(role_num))

            path = os.path.join(SERVER_INDEX_PATH, "{}.json".format(server.id))
            await self.check_for_file(path)
            await self.write_file(path, server_index)

            await self.bot.edit_message(indexed, new_content="{}/{} Servers Indexed...".format(servers_indexed, total_servers))
            await asyncio.sleep(1)
        await self.bot.edit_message(indexed, new_content="{}/{} Servers Indexed... Done!".format(servers_indexed, total_servers))

    @commands.command(pass_context=True)
    @checks.is_owner()
    async def indexemoji(self, ctx, server_id=None):
        server = await self.search_server(ctx, server_id)
        if server == None:
            return

        emoji_index = {}
        emoji_index['emoji'] = []

        emoji_num = 0
        for e in server.emojis:
            emoji_num += 1
            emoji_index['emoji'].append(":{}: [{}]".format(e.name, e.url))

        emoji_index['emoji'].insert(0, "Total Emoji: {}".format(emoji_num))
        path = os.path.join(EMOJI_INDEX_PATH, "{}.json".format(server.id))

        await self.check_for_file(path)
        await self.write_file(path, emoji_index)

        em = discord.Embed(color=0x1e2dd4,
                           title="{} Emoji".format(server.name),
                           description="Total Emoji: {}".format(emoji_num))

        await self.bot.say(embed=em)
        await self.bot.send_file(ctx.message.channel, path)


def check_folders():
    if not os.path.exists(PATH):
        os.mkdir(PATH)
    if not os.path.exists(SERVER_INDEX_PATH):
        os.mkdir(SERVER_INDEX_PATH)
    if not os.path.exists(MEMBER_INDEX_PATH):
        os.mkdir(MEMBER_INDEX_PATH)
    if not os.path.exists(EMOJI_INDEX_PATH):
        os.mkdir(EMOJI_INDEX_PATH)


def setup(bot):
    check_folders()
    i = Indexer(bot)
    bot.add_cog(i)
