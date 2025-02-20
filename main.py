import collections
import os
import re

import discord  # pylint: disable=E0401
from discord.ext import commands  # pylint: disable=E0401
from dotenv import load_dotenv  # pylint: disable=E0401

from lib import (  # pylint: disable=E0401
    export_emoji_counts_to_csv,
    load_emoji_counts_from_csv,
)

load_dotenv()

# 絵文字カウントの保存先ファイル
EMOJI_COUNTS_CSV = "emoji_counts.csv"

# Botのトークンを設定
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクションを監視するためのIntents

bot = commands.Bot(command_prefix="!", intents=intents)

emoji_counts = collections.Counter()


@bot.event
async def on_ready():
    global emoji_counts

    print(f"{bot.user.name} が起動しました")
    emoji_counts = load_emoji_counts_from_csv(EMOJI_COUNTS_CSV)
    try:
        synced = await bot.tree.sync()
        print(f"{len(synced)}個のコマンドを同期しました")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    print("処理中：", message.content)
    emojis = re.findall(r"<a?:[a-zA-Z0-9_]+:[0-9]+>", message.content)
    emoji_counts.update(emojis)

    export_emoji_counts_to_csv(emoji_counts, EMOJI_COUNTS_CSV)

    await bot.process_commands(message)


@bot.event
async def on_reaction_add(reaction, user):
    if user == bot.user:
        return
    emoji_counts[str(reaction.emoji)] += 1


@bot.event
async def on_reaction_remove(reaction, user):
    if user == bot.user:
        return
    emoji_counts[str(reaction.emoji)] -= 1


@bot.tree.command(name="emojistats", description="絵文字の使用回数を表示します")
async def emojistats(interaction: discord.Interaction):
    if not emoji_counts:
        await interaction.response.send_message("まだ絵文字が使われていません。")
        return

    top_emojis = emoji_counts.most_common(10)
    message = "絵文字の使用回数ランキング:\n"
    for emoji, count in top_emojis:
        message += f"{emoji}: {count}回\n"
    await interaction.response.send_message(message)


@bot.tree.command(
    name="clear-emoji-stats", description="絵文字の使用回数をリセットします"
)
async def clear_emoji_stats(interaction: discord.Interaction):
    if not emoji_counts:
        await interaction.response.send_message("まだ絵文字が使われていません")
        return

    emoji_counts.clear()
    await interaction.response.send_message("絵文字の使用回数をリセットしました．")


bot.run(TOKEN)
