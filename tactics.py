import os
import random
from datetime import datetime

import cairosvg
import chess
import chess.engine
import chess.pgn
import chess.svg
import discord
import requests
from discord import SelectOption
from discord import app_commands as slash
from discord.ext import commands
from dotenv import load_dotenv
from sqlalchemy import or_

from dbs import Games, Solved, Solving
from utility import Session

load_dotenv()
apikey = os.environ.get("apikey")
path = os.environ.get("path")

url = "https://chess-puzzles.p.rapidapi.com/"

headers = {
    "X-RapidAPI-Key": apikey,  # for authenticashun
    "X-RapidAPI-Host": "chess-puzzles.p.rapidapi.com",  # for that server to identify location of the api endpoint
}

scores = {"easy": 10, "medium": 30, "hard": 80}

# Cog = Component of a Guild
class Tactics(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = Session()  # Initialize the session in the constructor

    def cog_unload(self):
        self.session.close()  # Close the session when the cog is unloaded

    @slash.command(name="details", description="details")
    async def details(self, ctx):
        await ctx.response.send_message(
            """Title: Discord Chess Bot\nCreator: Yashas Donthi\nMade with love in Bangalore, India :heart:"""
        )

    @slash.command(name="solve", description="Make your move to solve the puzzle")
    async def solve(self, ctx, move: str):
        await ctx.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )
        global scores

        results = (
            self.session.query(Solving)
            .filter(
                Solving.channel_id == ctx.channel.id, Solving.user_id == ctx.user.id
            )
            .order_by(Solving.index.desc())
            .first()
        )
        message_id = results.message_id
        board = results.board
        movelist = results.movelist
        level = results.level
        move = move.strip()

        print("2:", movelist)

        if move != movelist[0]:
            mess = await ctx.channel.send("Wrong move")
            await mess.delete()
            return

        else:
            move = board.parse_san(move)
            board.push(move)
            movelist.pop(0)

            self.session.query(Solving).filter(
                Solving.channel_id == ctx.channel.id, Solving.user_id == ctx.user.id
            ).update({Solving.board: board, Solving.movelist: movelist})
            await self.render(message_id, ctx.channel.id)

            if len(movelist) == 0:
                await ctx.channel.send(
                    f"{ctx.user.mention} CONGRATULASHUNS ON SOLVING THE TACTIC!!!"
                )

                row = (
                    self.session.query(Solved)
                    .filter(
                        Solved.server_id == ctx.guild.id, Solved.user_id == ctx.user.id
                    )
                    .order_by(Solved.index.desc())
                    .first()
                )
                print("Row:", row)

                channel = self.bot.get_channel(ctx.channel.id)
                guild_id = channel.guild.id

                test = Solved(user_id=ctx.user.id, server_id=guild_id, easy=1, score=10)
                print("Before:", test.easy, test.medium, test.hard, test.score)

                if level == "easy":
                    if row is None:
                        inst1 = Solved(
                            user_id=ctx.user.id,
                            server_id=guild_id,
                            easy=1,
                            medium=0,
                            hard=0,
                            score=10,
                        )
                        self.session.add(inst1)
                    else:
                        self.session.query(Solved).filter(
                            Solved.server_id == ctx.guild.id,
                            Solved.user_id == ctx.user.id,
                        ).update(
                            {
                                Solved.easy: Solved.easy + 1,
                                Solved.score: Solved.score + 10,
                            }
                        )

                elif level == "medium":
                    if row is None:
                        inst1 = Solved(
                            user_id=ctx.user.id,
                            server_id=guild_id,
                            easy=0,
                            medium=1,
                            hard=0,
                            score=30,
                        )
                        self.session.add(inst1)
                    else:
                        self.session.query(Solved).filter(
                            Solved.server_id == ctx.guild.id,
                            Solved.user_id == ctx.user.id,
                        ).update(
                            {
                                Solved.medium: Solved.medium + 1,
                                Solved.score: Solved.score + 30,
                            }
                        )

                elif level == "hard":
                    if row is None:
                        inst1 = Solved(
                            user_id=ctx.user.id,
                            server_id=guild_id,
                            easy=0,
                            medium=0,
                            hard=1,
                            score=80,
                        )
                        self.session.add(inst1)
                    else:
                        self.session.query(Solved).filter(
                            Solved.server_id == ctx.guild.id,
                            Solved.user_id == ctx.user.id,
                        ).update(
                            {
                                Solved.hard: Solved.hard + 1,
                                Solved.score: Solved.score + 80,
                            }
                        )

                print("Level:", level)
                test2 = Solved(
                    user_id=ctx.user.id, server_id=guild_id, easy=1, score=10
                )
                print("After:", test2.easy, test2.medium, test2.hard, test2.score)

                self.session.query(Solving).filter(
                    Solving.channel_id == ctx.channel.id, Solving.user_id == ctx.user.id
                ).delete()
                self.session.commit()
                print("Commit done")
                return

            move = board.parse_san(movelist[0])
            board.push(move)
            movelist.pop(0)

            self.session.query(Solving).filter(
                Solving.channel_id == ctx.channel.id, Solving.user_id == ctx.user.id
            ).update({Solving.board: board, Solving.movelist: movelist})
            await self.render(message_id, ctx.channel.id)

    async def render(self, message_id, channel_id):
        result = (
            self.session.query(Solving.board)
            .filter(Solving.message_id == message_id, Solving.channel_id == channel_id)
            .all()[-1]
        )

        board = result.board
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        svg_obj = chess.svg.board(board=board)
        png_obj = cairosvg.svg2png(bytestring=svg_obj)

        with open(f"{path}/tactics/{message_id}.png", "wb") as file:
            file.write(png_obj)
        file = discord.File(f"{path}/tactics/{message_id}.png")

        embed = message.embeds[0]
        if board.turn == chess.WHITE:
            embed.title = "White to play"
        elif board.turn == chess.BLACK:
            embed.title = "Black to play"
        embed.set_image(url=f"attachment:/{path}/tactics/{message_id}.png")

        await message.edit(embed=embed, attachments=[file])

    @slash.command(name="tactics", description="Solve tactics")
    async def tactics(self, slash_i):
        await slash_i.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )

        async def select_callback(selected_i):
            await selected_i.response.send_message(
                content="okey", delete_after=0.0001, ephemeral=True
            )
            level = selected_i.data["values"][
                0
            ]  # Get the selected value from the select component

            themes2 = '["middlegame","advantage"]'
            e_moves = random.choice(["1", "2"])
            m_moves = random.choice(["2", "3"])
            h_moves = random.choice(["3", "4"])

            if level == "easy":
                params = {
                    "themes": themes2,
                    "rating": "1100",
                    "ratingdeviation": "80",
                    "themesType": "ALL",
                    "playerMoves": e_moves,
                    "count": "1",
                }
            elif level == "medium":
                params = {
                    "themes": themes2,
                    "rating": "1600",
                    "ratingdeviation": "120",
                    "themesType": "ALL",
                    "playerMoves": m_moves,
                    "count": "1",
                }
            elif level == "hard":
                params = {
                    "themes": themes2,
                    "rating": "2000",
                    "ratingdeviation": "300",
                    "themesType": "ALL",
                    "playerMoves": h_moves,
                    "count": "1",
                }

            try:
                response = requests.get(url=url, headers=headers, params=params)
                response_data = response.json()
            except:
                await selected_i.channel.send("API limit exceeded, possibly.")
                return

            print("1:", response_data)
            fen = response_data["puzzles"][0]["fen"]
            movelist = response_data["puzzles"][0]["moves"]

            board = chess.Board(fen)
            move = board.parse_san(movelist[0])

            svg_obj = chess.svg.board(board=board)
            png_obj = cairosvg.svg2png(bytestring=svg_obj)

            embed = discord.Embed()
            if board.turn == chess.WHITE:
                embed.title = f"{int(len(movelist)/2)} Moves, White to play"
            elif board.turn == chess.BLACK:
                embed.title = f"{int(len(movelist)/2)} Moves, Black to play"

            time = datetime.now()
            with open(f"{path}/tactics/initial{time}.png", "wb") as file:
                file.write(png_obj)  # type:ignore
            file = discord.File(f"{path}/tactics/initial{time}.png")

            message = await selected_i.channel.send(embed=embed, file=file)

            board.push(move)  # 1st move by the other side, & then the tactic starts
            movelist.pop(0)

            inst1 = Solving(
                user_id=selected_i.user.id,
                message_id=message.id,
                channel_id=message.channel.id,
                board=board,
                movelist=movelist,
                level=level,
            )
            self.session.add(inst1)
            self.session.commit()
            await self.render(message.id, message.channel.id)

        options = [
            SelectOption(label="Easy", value="easy"),
            SelectOption(label="Medium", value="medium"),
            SelectOption(label="Hard", value="hard"),
        ]

        select = discord.ui.Select(placeholder="Select a level", options=options)
        select.callback = select_callback

        view = discord.ui.View()
        view.add_item(select)

        await slash_i.channel.send(view=view)

    @slash.command(name="stats", description="Personal stats")
    async def stats(self, ctx, member: discord.Member):
        await ctx.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )

        tactic = (
            self.session.query(Solved)
            .filter(Solved.user_id == member.id, Solved.server_id == ctx.guild.id)
            .first()
        )
        games = (
            self.session.query(Games)
            .filter(
                or_(Games.white_id == member.id, Games.black_id == member.id),
                Games.server_id == ctx.guild.id,
            )
            .all()
        )

        wins, draws, losses = 0, 0, 0

        for game in games:
            if game.result == "1/2-1/2":
                print("a")
                draws += 1
            elif member.id == game.white_id:
                if game.result == "1-0":
                    print("b")
                    wins += 1
                elif game.result == "0-1":
                    print("c")
                    losses += 1
            elif member.id == game.black_id:
                if game.result == "0-1":
                    print("d")
                    wins += 1
                elif game.result == "1-0":
                    print("e")
                    losses += 1

        embed = discord.Embed(
            title=f"Stats for {member.name}", color=discord.Color.blue()
        )

        # name & value will be in same line, name will be bold.
        embed.add_field(name="Tactics", value="", inline=False)
        embed.add_field(name="", value=f"Easy: {tactic.easy}", inline=False)
        embed.add_field(name="", value=f"Medium: {tactic.medium}", inline=False)
        embed.add_field(name="", value=f"Hard: {tactic.hard}", inline=False)
        embed.add_field(name="", value=f"Score: {tactic.score}", inline=False)
        embed.add_field(name=" ", value=" ", inline=False)
        embed.add_field(name="Games", value="", inline=False)
        embed.add_field(name="", value=f"Wins: {wins}", inline=False)
        embed.add_field(name="", value=f"Draws: {draws}", inline=False)
        embed.add_field(name="", value=f"Losses: {losses}", inline=False)

        await ctx.channel.send(embed=embed)


# When you integrate the bot with Discord using bot.run(), Discord.py automatically scans the
# registered cogs and initializes them by calling their respective __init__ methods and other
# necessary setup functions. This includes calling the setup function of each cog that has been
# added using bot.add_cog().
async def setup(bot: commands.Bot):
    await bot.add_cog(Tactics(bot))