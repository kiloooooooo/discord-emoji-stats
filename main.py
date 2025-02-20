import collections
import json
import logging
import logging.config
import os
import re
from typing import Dict, Union, cast

import discord  # pylint: disable=E0401
from discord.ext import commands  # pylint: disable=E0401
from dotenv import load_dotenv  # pylint: disable=E0401

from lib import (  # pylint: disable=E0401
    export_emoji_counts_to_csv,
    get_top_n_range,
    load_emoji_counts_from_csv,
)

load_dotenv()

with open("./logging.json", "r", encoding="utf-8") as f:
    log_config = json.load(f)
logging.config.dictConfig(log_config)
logger = logging.getLogger(__name__)

EMOJI_COUNTS_FILENAME_BASE = "emoji_counts"

# Botのトークンを設定
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True  # リアクションを監視するためのIntents
intents.members = True  # リアクションの取り消しを監視するためのIntents

bot = commands.Bot(command_prefix="!", intents=intents)

emoji_counts: Dict[int, collections.Counter] = {}


@bot.event
async def on_ready():
    global emoji_counts

    logger.info("%s が起動しました", bot.user.name)
    emoji_counts = load_emoji_counts_from_csv()
    try:
        synced = await bot.tree.sync()
        logger.info("%d個のコマンドを同期しました", len(synced))
    except Exception as e:
        logger.info(e)


@bot.event
async def on_message(message: discord.Message):
    if message.guild is None:
        logger.info("メッセージが投稿されたサーバが不明")
        return

    if message.author == bot.user:
        return

    logger.info("処理中： %s", message.content)
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
    if guild_id not in emoji_counts:
        emoji_counts[guild_id] = collections.Counter()
    emoji_counts[guild_id][str(reaction.emoji)] += 1
    logger.info("%s: +1 @guild_id=%d", reaction.emoji, guild_id)
    export_emoji_counts_to_csv(
        emoji_counts[guild_id], f"{EMOJI_COUNTS_FILENAME_BASE}.{guild_id}.csv"
    )


@bot.event
async def on_reaction_remove(reaction: discord.Reaction, user):
    if user == bot.user:
        return
    guild_id = cast(discord.Guild, reaction.message.guild).id
    if guild_id in emoji_counts:
        emoji_counts[guild_id][str(reaction.emoji)] -= 1
    logger.info("%s: -1 @guild_id=%d", reaction.emoji, guild_id)
    export_emoji_counts_to_csv(
        emoji_counts[guild_id], f"{EMOJI_COUNTS_FILENAME_BASE}.{guild_id}.csv"
    )


@bot.tree.command(name="emojistats", description="サーバ絵文字の使用回数を表示します")
@discord.app_commands.describe(range="順位の範囲．例：1-10．指定しなければ全て表示")
async def emojistats(interaction: discord.Interaction, range: Union[str, None] = None):
    try:
        if range is None:
            min_rank = None
            max_rank = None
        else:
            min_rank = int(range.split("-")[0])
            max_rank = int(range.split("-")[1])
    except ValueError:
        min_rank = None
        max_rank = None

    if interaction.guild_id is None:
        await interaction.response.send_message(
            "エラー: コマンドが使用されたサーバが不明"
        )
        logger.error("エラー: コマンドが使用されたサーバが不明")
        return

    server_exists = interaction.guild_id in emoji_counts
    if not server_exists:
        await interaction.response.send_message("まだ絵文字が使われていません。")
        return

    # top_emojis = emoji_counts[interaction.guild_id].most_common()
    top_emojis = get_top_n_range(emoji_counts[interaction.guild_id], min_rank, max_rank)
    message = "絵文字の使用回数ランキング:\n"
    for rank, (emoji, count) in enumerate(top_emojis):
        message += f"`{rank + 1}位` - {emoji}: {count}回\n"
    await interaction.response.send_message(message)


# @bot.tree.command(
#     name="clear-emojistats", description="サーバ絵文字の使用回数をリセットします"
# )
# async def clear_emoji_stats(interaction: discord.Interaction):
#     if interaction.guild_id is None:
#         await interaction.response.send_message(
#             "エラー: コマンドが使用されたサーバが不明"
#         )
#         logger.error("エラー: コマンドが使用されたサーバが不明")
#         return

#     server_exists = interaction.guild_id in emoji_counts
#     if (not server_exists) or (not emoji_counts[interaction.guild_id]):
#         await interaction.response.send_message("まだ絵文字が使われていません")
#         return

#     emoji_counts.clear()
#     await interaction.response.send_message("絵文字の使用回数をリセットしました．")


if TOKEN:
    bot.run(TOKEN)
else:
    raise ValueError("トークンを読み込めませんでした")
