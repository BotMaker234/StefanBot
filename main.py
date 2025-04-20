import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


client = commands.Bot(command_prefix="%", intents=intents)

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

client.run(TOKEN)