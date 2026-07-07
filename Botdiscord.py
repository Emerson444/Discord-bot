import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os

CANAL_PERMITIDO = 

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

YDL_OPTIONS = {
    'format': 'bestaudio',
    'noplaylist': False,
    'quiet': True
}

class myclient(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix='!', intents=intents)
        self.Mostrar = []

bot = myclient()

async def check_canal(interaction: discord.Interaction) -> bool:
    if interaction.channel_id != CANAL_PERMITIDO:
        await interaction.response.send_message('❌ Usa o canal certo mano!', ephemeral=True)
        return False
    return True

async def get_audio_url(url):
    loop = asyncio.get_event_loop()
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
        if 'entries' in info:
            return [(e['url'], e['title']) for e in info['entries']]
        return [(info['url'], info['title'])]

async def play_next(interaction, voice_client):
    if bot.Mostrar:
        url, title = bot.Mostrar.pop(0)
        source = discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
            play_next(interaction, voice_client), bot.loop
        ))
        await interaction.channel.send(f'pra ja meu vei: **{title}**')
    else:
        await interaction.channel.send('✅ Fila vazia!')

@bot.event
async def on_ready():
    print(f'Bot online: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'on_ready: {len(synced)} comandos sincronizados')
    except Exception as e:
        print(f'Erro no on_ready: {e}')

@bot.tree.command(name='play', description='Toca uma música ou playlist do YouTube')
async def play(interaction: discord.Interaction, url: str):
    if not await check_canal(interaction):
        return
    await interaction.response.defer()
    if not interaction.user.voice:
        await interaction.followup.send('Entra no canal de voz! 🎧')
        return
    channel = interaction.user.voice.channel
    voice_client = interaction.guild.voice_client
    if voice_client is None:
        voice_client = await channel.connect()
    tracks = await get_audio_url(url)
    bot.Mostrar.extend(tracks)
    await interaction.followup.send(f'✅ {len(tracks)} música(s) adicionada(s) à fila!')
    if not voice_client.is_playing():
        await play_next(interaction, voice_client)

@bot.tree.command(name='skip', description='Pula a música atual')
async def skip(interaction: discord.Interaction):
    if not await check_canal(interaction):
        return
    vc = interaction.guild.voice_client
    if vc and vc.is_playing():
        vc.stop()
        await interaction.response.send_message('⏭️ Pulado!')
    else:
        await interaction.response.send_message('❌ Nenhuma música tocando.')

@bot.tree.command(name='mostrar', description='Mostra a fila de músicas')
async def mostrar(interaction: discord.Interaction):
    if not await check_canal(interaction):
        return
    if not bot.Mostrar:
        await interaction.response.send_message('📭 Fila vazia!')
        return
    lista = '\n'.join([f'{i+1}. {t}' for i, (_, t) in enumerate(bot.Mostrar)])
    await interaction.response.send_message(f'🎶 **Fila:**\n{lista}')

@bot.tree.command(name='stop', description='Para a música e sai do canal')
async def stop(interaction: discord.Interaction):
    if not await check_canal(interaction):
        return
    vc = interaction.guild.voice_client
    if vc:
        bot.Mostrar.clear()
        await vc.disconnect()
        await interaction.response.send_message('👋 Saindo!')
    else:
        await interaction.response.send_message('❌ Não estou em nenhum canal.')

@bot.tree.command(name='ping', description='Testa se o bot tá online')
async def ping(interaction: discord.Interaction):
    if not await check_canal(interaction):
        return
    await interaction.response.send_message('🏓 Pong!')

@bot.tree.command(name='help', description='Mostra todos os comandos')
async def help(interaction: discord.Interaction):
    if not await check_canal(interaction):
        return
    embed = discord.Embed(title='📖 Comandos do Bot', color=discord.Color.blue())
    embed.add_field(name='/play [url]', value='Toca musica do youtube ou spotify (eu acho)', inline=False)
    embed.add_field(name='/skip', value='Pula a música atual', inline=False)
    embed.add_field(name='/mostrar', value='Mostra a fila de músicas', inline=False)
    embed.add_field(name='/stop', value='Para a música e sai do canal', inline=False)
    embed.add_field(name='/ping', value='pra ver se ele ta online (o server é podre e talvez)', inline=False)
    embed.add_field(name='/help', value='Mostra essa mensagem', inline=False)
    await interaction.response.send_message(embed=embed)


bot.run('')
