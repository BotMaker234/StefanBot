import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import json
import os
import random
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

client = commands.Bot(command_prefix="%", intents=intents)

BANK = "bank.json"
if not os.path.exists(BANK):
    with open(BANK, "w") as f:
        json.dump({}, f)

places = [
    'McDonalds', 'KFC', 'Burger King', 'Home Depot', 'Microsoft', 'Apple', 'Nintendo'
]

sounds = [
    'data/sound1.mp3', 'data/sound2.mp3', 'data/sound3.mp3', 'data/sound4.mp3', 'data/sound5.mp3', 'data/sound6.mp3', 'data/sound7.mp3', 'data/sound8.mp3'
]

def healthbar(hp, max_hp = 100):
    full = int(hp / max_hp * 10)
    empty = 10 - full
    return "🟩" * full + "⬛" * empty

class AcceptButtonView(View):
    def __init__(self, challenger, opponent):
        super().__init__(timeout=30)
        self.challenger = challenger
        self.opponent = opponent
        self.result = None

        # Buttons
        accept = Button(label="Accept ✅", style=discord.ButtonStyle.success)
        reject = Button(label="Reject ❌", style=discord.ButtonStyle.danger)
        accept.callback = self.accept
        reject.callback = self.reject
        self.add_item(accept)
        self.add_item(reject)

    async def accept(self, interaction: discord.Interaction):
        if interaction.user != self.opponent:
            return await interaction.response.send_message("Idiot! Stay out of this **mating session**!", ephemeral=True)
        self.result = True
        await interaction.response.edit_message(content="Both players shall fight to the death", view=None)
        self.stop()

    async def reject(self, interaction: discord.Interaction):
        if interaction.user != self.opponent:
            return await interaction.response.send_message("Idiot! Stay out of this **mating session**!", ephemeral=True)
        self.result = False
        await interaction.response.edit_message(content="The one challenged rejected. Pussy!", view=None)
        self.stop()

def load_bank():
    with open(BANK, "r") as f:
        return json.load(f)

def save_bank(data):
    with open(BANK, "w") as f:
        json.dump(data, f, indent=4)

def check_user(user_id):
    data = load_bank()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"wallet": 0}
        save_bank(data)

def get_balance(user_id):
    check_user(user_id)
    data = load_bank()
    return data[str(user_id)]["wallet"]

def add_money(user_id, amount):
    check_user(user_id)
    data = load_bank()
    data[str(user_id)]["wallet"] += amount
    save_bank(data)

def remove_money(user_id, amount):
    check_user(user_id)
    data = load_bank()
    data[str(user_id)]["wallet"] = max(0, data[str(user_id)]["wallet"] - amount)
    save_bank(data)

class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        state = view.board[self.y][self.x]

        if state is not None or interaction.user != view.current_player:
            await interaction.response.send_message("It's not your turn dumbass!", ephemeral=True)
            return

        view.board[self.y][self.x] = view.symbol
        self.label = view.symbol
        self.style = discord.ButtonStyle.success if view.symbol == "❌" else discord.ButtonStyle.danger
        self.disabled = True

        winner = view.check_winner()
        draw = view.is_full()

        embed = view.build_embed()
        if winner:
            view.disable_all_buttons()
            embed.title = f"{view.symbol} wins!"
            embed.color = discord.Color.green()
        elif draw:
            view.disable_all_buttons()
            embed.title = "It's a draw!"
            embed.color = discord.Color.gold()
        else:
            view.switch_turn()
            embed.description = f"Turn: {view.symbol} {view.current_player.mention}"

        await interaction.response.edit_message(embed=embed, view=view)

class TicTacToeView(View):
    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=None)
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.players = [player1, player2]
        self.symbols = ["❌", "⭕"]
        self.current = 0

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    @property
    def current_player(self):
        return self.players[self.current]

    @property
    def symbol(self):
        return self.symbols[self.current]

    def switch_turn(self):
        self.current = 1 - self.current

    def check_winner(self):
        b = self.board
        lines = (
            b[0], b[1], b[2],
            [b[0][0], b[1][0], b[2][0]],
            [b[0][1], b[1][1], b[2][1]],
            [b[0][2], b[1][2], b[2][2]],
            [b[0][0], b[1][1], b[2][2]],
            [b[0][2], b[1][1], b[2][0]],
        )
        return any(all(cell == self.symbol for cell in line) for line in lines)

    def is_full(self):
        return all(cell is not None for row in self.board for cell in row)

    def disable_all_buttons(self):
        for child in self.children:
            child.disabled = True

    def build_embed(self):
        embed = discord.Embed(
            title="Tic-Tac-Toe",
            description=f"Turn: {self.symbol} {self.current_player.mention}",
            color=discord.Color.blurple()
        )
        embed.set_footer(text="You shall battle to the death")
        return embed

@client.event
async def on_ready():
    print(f"We're logged in as {client.user}")

@client.command(help="Check your balance")
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal = get_balance(target.id)
    embed = discord.Embed(
        title = f"{target.name}'s balance",
        description=f"Wallet Cash: ${bal}",
        color=discord.Color.green()
    )
    embed.set_footer(text="Don't be a stinky brokie!")
    await ctx.send(embed=embed)

@client.command(help='rise grind and shine')
@commands.cooldown(1, 5, commands.BucketType.user)
async def work(ctx):
    bal = get_balance(ctx.author.id)
    amount = random.randint(0, 120)
    place = random.choice(places)
    add_money(ctx.author.id, amount)
    embed = discord.Embed(color=discord.Color.blurple())

    if amount == 0:
        embed.title = "Work Results"
        embed.description = f"You absolute BOZO, you just got fired out of {place}!"
        embed.color = discord.Color.red()

    else:
        embed.title = "Work Results"
        embed.description = f"You worked your shit at {place} and earned ${amount}."
    await ctx.send(embed=embed)

@work.error
async def work_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        time = round(error.retry_after, 2)
        await ctx.send(f"Bitch, you're on cooldown! {time}s left.")

@client.command()
async def slots(ctx, bet: int):
    user_id = ctx.author.id
    bal = get_balance(ctx.author.id)

    if bet <= 0 or bet == None:
        return await ctx.send("We don't accept Gierek era hobos, come back when you're a little richer!")

    if bet > bal:
        return await ctx.send("Foolish baboon! You can't bet more than you have in your wallet!")
    emojis = [
        '🆓',
        '🗣️',
        '<:zbok:1309026800567058462>',
        '<:ofoz:815578044118335519>',
        '<:dupa:594173407298453544>',
        '<:weirdchamp:795062316235358238>',
        '<:jjgrin:643237317724864512>',
        '<:3_:1253017918313201747>'
    ]
    slot1 = random.choice(emojis)
    slot2 = random.choice(emojis)
    slot3 = random.choice(emojis)

    result = f"{slot1} {slot2} {slot3}"

    if slot1 == emojis[3] and slot2 == emojis[3] and slot3 == emojis[3]:
        amount = bet * 30
        add_money(user_id, amount)
        message = "DUPA JACKPOT!! You won real big!"
        color = discord.Color.cyan()
    elif slot1 == slot2 == slot3:
        amount = bet * 5
        add_money(user_id, amount)
        message = "You actually won you lucky cunt!"
        color = discord.Color.green()
    else:
        remove_money(user_id, bet)
        message = f"You bloody baffoon, you lost!"
        color = discord.Color.red()

    embed = discord.Embed(title = "Your rigged slots!", description=result, color=color)
    embed.add_field(name="Winnings: ", value=message, inline=False)
    embed.set_footer(text="The lion rapes his wife when she roars (and gambles away)")
    await ctx.send(embed=embed)



@client.command(help="I Tic Tac Toe'd all over the place.")
async def tictactoe(ctx, opponent: discord.User):
    if opponent.bot:
        await ctx.send("Bro you'd lose to us bots in a mere picosecond")
        return
    if opponent == ctx.author:
        await ctx.send("YYou goddamn nutsack, playing against yourself is a paradox!")
        return

    view = TicTacToeView(ctx.author, opponent)
    embed = view.build_embed()
    await ctx.send(embed=embed, view=view)

@client.command(help="Plays the funny one at a nearest voice channel")
async def chicken(ctx):
    if not ctx.author.voice:
        await ctx.send("Not connected to a voice channel.")
        return

    channel = ctx.author.voice.channel
    voice_client = ctx.guild.voice_client

    if not voice_client:
        voice_client = await channel.connect()
    elif voice_client.channel != channel:
        await voice_client.move_to(channel)

    if not voice_client.is_playing():
        source = discord.FFmpegPCMAudio("chicken.mp3")

        def after_playing(error):
            coro = voice_client.disconnect()
            fut = asyncio.run_coroutine_threadsafe(coro, client.loop)
            try:
                fut.result()
            except:
                pass

        voice_client.play(source, after=after_playing)
        await ctx.send(f"Playing LAVA CHICKEN in {channel}")
    else:
        await ctx.send("wait in line lil bro")

@client.command()
async def troll(ctx):
    if not ctx.author.voice:
        await ctx.send("Not connected to a voice channel.")
        return

    vc = ctx.voice_client
    if not vc:
        vc = await ctx.author.voice.channel.connect()

    if vc.is_playing():
        vc.stop()

    source = random.choice(sounds)
    audio = discord.FFmpegPCMAudio(source)
    vc.play(audio)

    while vc.is_playing():
        await asyncio.sleep(1)

    await asyncio.sleep(60)

    if vc and not vc.is_playing():
        await vc.disconnect()
        await ctx.send("No Minecraft? I'm fucking leaving bozos")

@client.command(help="Fight to the death for mere dollars")
async def fight(ctx, opponent: discord.Member, bet: int):
    if opponent.bot or opponent == ctx.author:
        return await ctx.send("The lion rapes users who attack themselves.")

    if bet <= 0:
        return await ctx.send("There's no negative money you dimwit")

    user_id = ctx.author.id
    opponent_id = opponent.id

    if get_balance(user_id) < bet:
        return await ctx.send(f"The challenger is downright broke, LAUGH AT HIM CHAT")
    if get_balance(opponent_id) < bet:
        return await ctx.send("Would you look at that, the victim couldn't care less as they are India slums themselves")

    view = AcceptButtonView(ctx.author, opponent)
    await ctx.send(f"{ctx.author.mention} challenged {opponent.mention} to a fight to the death for mere ${bet}!", view=view)
    await view.wait()

    if view.accept is None:
        return await ctx.send("One of yall scaready cats didn't accept in time!")
    if not view.accept:
        return

    remove_money(user_id, bet)
    remove_money(opponent_id, bet)
    await ctx.send(f"Bets placed, no more bets no more bets, ${bet} in the pool!")

    user_hp = 100
    opp_hp = 100
    turn = 0



    while user_hp > 0 and opp_hp > 0:
        attacker = ctx.author if turn % 2 == 0 else opponent
        defender = opponent if turn % 2 == 0 else ctx.author

        damage = random.randint(10, 25)
        hits = [
            f"**{attacker.display_name}** steals **{defender.display_name}**'s code! EMOTIONAL DAMAGE! -{damage} HP",
            f"**{attacker.display_name}** strikes **{defender.display_name}**'s testicles with a vase for {damage} HP",
            f"**{attacker.display_name}** SLAPS **{defender.display_name}** so hard they fly into a wall! -{damage} HP",
            f"**{attacker.display_name}** shoots **{defender.display_name}** with a 9mm! -{damage} HP",
            f"**{defender.display_name}** gets struck by a thunder! How lucky for **{attacker.display_name}**! -{damage} HP",
        ]
        if turn % 2 == 0:
            opp_hp = max(0, opp_hp - damage)
        else:
            user_hp = max(0, user_hp - damage)

        embed = discord.Embed(
            title = "Bitches be fighting to death!",
            description = random.choice(hits),
            color = discord.Color.orange()
        )
        embed.add_field(name = f"{ctx.author.display_name}'s HP", value=healthbar(user_hp), inline = True)
        embed.add_field(name = f"{opponent.display_name}'s HP", value=healthbar(opp_hp), inline = True)
        await ctx.send(embed=embed)
        await asyncio.sleep(2)
        turn += 1

    winner = ctx.author if user_hp > 0 else opponent
    loser = opponent if user_hp > 0 else ctx.author
    amount = bet * 2
    add_money(winner.id, amount)

    final_embed = discord.Embed(
        title = "Done and Done!!",
        description = f"The winner is **{winner.mention}**! The motherfucker gets the sum of ${bet}!",
        color = discord.Color.gold()
    )
    await ctx.send(embed=final_embed)



client.run(TOKEN)