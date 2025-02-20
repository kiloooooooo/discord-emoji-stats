import collections
import os
import re
from typing import Dict, cast

import discord  # pylint: disable=E0401
from discord.ext import commands  # pylint: disable=E0401
from dotenv import load_dotenv  # pylint: disable=E0401

from lib import (  # pylint: disable=E0401
    export_emoji_counts_to_csv,
    load_emoji_counts_from_csv,
)

load_dotenv()

EMOJI_COUNTS_FILENAME_BASE = "emoji_counts"

# Botのトークンを設定
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクションを監視するためのIntents

bot = commands.Bot(command_prefix="!", intents=intents)

emoji_counts: Dict[int, collections.Counter] = {}


@bot.event
async def on_ready():
    global emoji_counts

    print(f"{bot.user.name} が起動しました")
    emoji_counts = load_emoji_counts_from_csv()
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message: discord.Message):
    if message.guild is None:
        print("メッセージが投稿されたサーバが不明")
        return

    if message.author == bot.user:
        return

    print("処理中：", message.content)
    emojis = re.findall(r"<a?:[a-zA-Z0-9_]+:[0-9]+>", message.content)

    if message.guild.id not in emoji_counts:
        emoji_counts[message.guild.id] = collections.Counter()

    emoji_counts[message.guild.id].update(emojis)

    export_emoji_counts_to_csv(
        emoji_counts[message.guild.id],
        f"{EMOJI_COUNTS_FILENAME_BASE}.{message.guild.id}.csv",
    )

    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction: discord.Reaction, user):
    if user == bot.user:
        return
    guild_id = cast(discord.Guild, reaction.message.guild).id
    emoji_counts[guild_id][str(reaction.emoji)] += 1


@bot.event
async def on_reaction_remove(reaction, user):
    if user == bot.user:
        return
    guild_id = cast(discord.Guild, reaction.message.guild).id
    emoji_counts[guild_id][str(reaction.emoji)] -= 1


@bot.tree.command(name="emojistats", description="サーバ絵文字の使用回数を表示します")
async def emojistats(interaction: discord.Interaction):
    if interaction.guild_id is None:
        await interaction.response.send_message(
            "エラー: コマンドが使用されたサーバが不明"
        )
        print("エラー: コマンドが使用されたサーバが不明")
        return

    server_exists = interaction.guild_id in emoji_counts
    if not server_exists:
        await interaction.response.send_message("まだ絵文字が使われていません。")
        return

    top_emojis = emoji_counts[interaction.guild_id].most_common()
    message = "絵文字の使用回数ランキング:\n"
    for emoji, count in top_emojis:
        message += f"{emoji}: {count}回\n"
    await interaction.response.send_message(message)


@bot.tree.command(
    name="clear-emojistats", description="サーバ絵文字の使用回数をリセットします"
)
async def clear_emoji_stats(interaction: discord.Interaction):
    if interaction.guild_id is None:
        await interaction.response.send_message(
            "エラー: コマンドが使用されたサーバが不明"
        )
        print("エラー: コマンドが使用されたサーバが不明")
        return

    server_exists = interaction.guild_id in emoji_counts
    if (not server_exists) or (not emoji_counts[interaction.guild_id]):
        await interaction.response.send_message("まだ絵文字が使われていません")
        return

    emoji_counts.clear()
    await interaction.response.send_message("絵文字の使用回数をリセットしました．")


if TOKEN:
    bot.run(TOKEN)
else:
    raise ValueError("トークンを読み込めませんでした")
