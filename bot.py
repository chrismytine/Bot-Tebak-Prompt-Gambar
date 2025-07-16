import discord
from discord.ext import commands
import random
import os
import asyncio
from fusion import FusionBrainAPI
from game import GameSession
from config import TOKEN, API_KEY, SECRET_KEY

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

session = GameSession(max_rounds=5)

PROMPTS = [
    "naga minum kopi di rooftop",
    "kucing astronaut di bulan",
    "robot main gitar di hutan",
    "ikan terbang di atas kota futuristik",
    "singa membaca buku di perpustakaan",
    "alien naik sepeda di jalanan kota",
    "burung api di tengah badai salju",
    "gorila menjelajahi padang pasir",
    "lumba-lumba berenang di laut dalam",
    "anjing menjelajahi luar angkasa",
    "harimau yang sedang menjaga pasar malam",
    "kelinci dan kura-kura berpatroli",
    "rusa mendaki gunung bersalju",
    "elang terbang di dunia maya",
    "dinosaurus duduk di taman kota",
    "ayam bermain di opera",
    "kucing memainkan piano",
    "gajah menyebrang sungai nil",
    "harimau berenang di taman air",
    "anjing bermain di sirkus",
    "alien menjelajahi tambang besi"
]

async def generate_image(prompt):
    api = FusionBrainAPI(
        'https://api-key.fusionbrain.ai/',
        API_KEY,
        SECRET_KEY
    )
    pipeline_id = api.get_pipeline()
    uuid = api.generate(prompt, pipeline_id, images=1)
    files = api.check_generation(uuid)
    filepath = "generated.jpg"
    api.save_image(files, filepath)
    return filepath

#intro
@bot.command(name="intro", aliases=["introduction", "perkenalan"])
async def introduction_command(ctx):
    intro_text = (
        f"Halo {ctx.author.mention}! 👋\n"
        "Aku adalah bot game interaktif yang bisa membuat gambar dari teks dan menguji kecepatan serta ketepatanmu dalam menebak prompt!\n\n"
        "🎮 Game utamaku adalah **Tebak Prompt Gambar** — kamu akan melihat gambar buatan AI dan harus menebak prompt aslinya secepat mungkin.\n\n"
        "🧠 Siapa cepat dia dapat, dan yang menjawab benar duluan akan mendapatkan poin!\n"
        "Gunakan `!helpp` untuk melihat semua perintah yang bisa kamu gunakan.\n"
        "Selamat bermain dan semoga kamu jadi juaranya! 🏆"
    )
    await ctx.send(intro_text)

#help
@bot.command(name="helpp", aliases=["help_me"])
async def help_command(ctx):
    help_text = (
        "📜 **Daftar Perintah Bot:**\n"
        "\n"
        "🎮 `!startgame` - Memulai game tebak prompt\n"
        "📊 `!leaderboard` - Melihat skor semua pemain\n"
        "👋 `!intro` / `!introduction` - Perkenalan singkat dari bot ini\n"
        "ℹ️ `!helpp` / `!help_me` - Menampilkan daftar perintah ini\n"
        "\n"
        "💡 Saat game berlangsung, bot akan otomatis mengirim gambar dan opsi untuk menebak. Siapa cepat dia dapat!"
    )
    await ctx.send(help_text)

# start game
@bot.command()
async def startgame(ctx):
    if session.active:
        await ctx.send("Game sedang berlangsung!")
        return

    await ctx.send("🎮 Mau main berapa ronde? Kirim angka di bawah ini! (contoh: 5)")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit() #ngecek yang jawab adalah yang memulai dan dichannel yang sama dan konten is digit

    try:
        msg = await bot.wait_for("message", check=check, timeout=30) #nunggu 30
        jumlah_ronde = int(msg.content)
        if jumlah_ronde <= 0 or jumlah_ronde > 20:
            await ctx.send("Jumlah ronde harus antara 1 dan 20! Silahkan ulang dengan mengetik !startgame")
            return
    except asyncio.TimeoutError:
        await ctx.send("⌛ Waktu habis! Game akan dimulai dengan 5 ronde secara default.")
        session.start()
        await next_round(ctx)
        return

    session.max_rounds = jumlah_ronde
    session.start()
    await ctx.send(f"🟢 Game dimulai dengan {jumlah_ronde} ronde!")
    await next_round(ctx)

async def next_round(ctx):
    if session.is_game_over():
        session.end()
        await ctx.send(session.get_winner())
        return

    # pilih prompt unik
    available = [p for p in PROMPTS if p not in session.used_prompts] #melihat promp yang available jika tidak masuk ke prompt yang sudah digunakan
    prompt = random.choice(available)
    session.used_prompts.add(prompt) #prompt yang didapatkan dari random di masukkan ke yang sudah di gunakan 

    # generate gambar
    await ctx.send("🧠 Menghasilkan gambar...")
    async with ctx.typing():
        filepath = await generate_image(prompt)

    # buat opsi mirip
    distractors = random.sample([p for p in PROMPTS if p != prompt], 3)
    options = session.next_round(prompt, distractors)

    # kirim gambar dan pilihan
    view = discord.ui.View(timeout=None)
    for opt in options:
        button = discord.ui.Button(label=opt, style=discord.ButtonStyle.secondary, custom_id=opt)
        view.add_item(button)

    with open(filepath, "rb") as f:
        await ctx.send(file=discord.File(f, filename="image.jpg"))
        await ctx.send("Tebak prompt yang digunakan untuk membuat gambar ini:\nJika bot melanjutkan gamenya maka sudah ada yang menjawab dengan benar promptnya!", view=view)

    os.remove(filepath)

@bot.event
async def on_interaction(interaction):
    if not session.active:
        return

    user_id = interaction.user.id
    answer = interaction.data.get("custom_id")

    result = session.answer(user_id, answer)
    await interaction.response.send_message(result, ephemeral=True)

    # jika sudah dijawab dengan benar → delay lalu lanjut ronde berikutnya
    if session.answered:
        if session.is_game_over():
            await next_round(interaction.channel)
            return 
        await interaction.channel.send("⏭️ Lanjut ke ronde berikutnya dalam 3 detik...")
        await asyncio.sleep(3)
        await next_round(interaction.channel)

@bot.command()
async def leaderboard(ctx):
    if session.active:
        await ctx.send("Game masih berlangsung, leaderboard final akan muncul setelah game selesai.")
    else:
        await ctx.send(session.get_leaderboard())

bot.run(TOKEN)
