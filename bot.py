import discord
from discord.ext import commands
import yt_dlp

# ======================
# 設定 intents
# ======================
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# Queue
# ======================
queue = []
now_playing = None


# ======================
# yt-dlp 設定
# ======================
ydl_opts = {
    'format': 'bestaudio',
    'noplaylist': True,
    'quiet': True
}


# ======================
# 播下一首
# ======================
async def play_next(ctx):
    global queue, now_playing

    if len(queue) == 0:
        now_playing = None
        return

    song = queue.pop(0)
    now_playing = song

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{song}", download=False)
        video = info['entries'][0]

        url = video['url']
        title = video['title']
        thumbnail = video.get('thumbnail')

    source = discord.FFmpegPCMAudio(
        url,
        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        options="-vn"
    )

    def after_playing(error):
        bot.loop.create_task(play_next(ctx))

    ctx.voice_client.play(source, after=after_playing)

    await ctx.send(f"🎵 現在播放：{title}")
    if thumbnail:
        await ctx.send(thumbnail)


# ======================
# 加入語音
# ======================
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
    else:
        await ctx.send("❌ 你要先進語音頻道")


# ======================
# play（加入 queue）
# ======================
@bot.command()
async def play(ctx, *, query):
    global queue

    queue.append(query)
    await ctx.send(f"➕ 已加入：{query}")

    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await ctx.send("❌ 請先進語音頻道")

    if not ctx.voice_client.is_playing():
        await play_next(ctx)


# ======================
# skip
# ======================
@bot.command()
async def skip(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭ 已跳過")


# ======================
# pause
# ======================
@bot.command()
async def pause(ctx):
    if ctx.voice_client:
        ctx.voice_client.pause()
        await ctx.send("⏸ 暫停")


# ======================
# resume
# ======================
@bot.command()
async def resume(ctx):
    if ctx.voice_client:
        ctx.voice_client.resume()
        await ctx.send("▶️ 繼續播放")


# ======================
# queue 顯示
# ======================
@bot.command()
async def list(ctx):
    if queue:
        await ctx.send("📜 排隊清單：\n" + "\n".join(queue))
    else:
        await ctx.send("📭 目前沒有歌曲")


# ======================
# 停止
# ======================
@bot.command()
async def stop(ctx):
    queue.clear()
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    await ctx.send("🛑 已停止播放")


# ======================
# 啟動
# ======================
import os
bot.run(os.getenv("DISCORD_TOKEN"))