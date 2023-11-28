import math
import os
import random

import cairosvg
import chess
import chess.engine
import chess.pgn
import chess.svg
import discord
from discord import app_commands as slash
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
from sqlalchemy import or_

from dbs import Games, Playing
from utility import Session
#from main import client as bot

load_dotenv()
path = os.environ.get("path")


class Challenge(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = Session()

    def cog_unload(self):
        self.session.close()  # Close the session when the cog is unloaded

    async def on_ready(self):
        print(f"{self.user} is ready!")
        await self.time_check()

    async def on_message_edit(self, before, after):
        print(before.data, "edited to", after.data)

    @slash.command(
        name="ily", description="The most fundamental secret of the universe"
    )
    async def ily(self, ctx):
        await ctx.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )
        # ephemeral means only user who interacted can see that message
        await ctx.user.send(f"I love you too, {str(ctx.user)[:-2]}")

    @slash.command(
        name="move",
        description="Make your move\nExample:e2e4 (Initial square to final square)",
    )
    async def play(self, ctx, move: str):
        # move example: e2e4, not just e4
        await ctx.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )
        results = (
            self.session.query(
                Playing.white_id,
                Playing.black_id,
                Playing.movenum,
                Playing.board,
                Playing.message_id,
                Playing.start_time,
            )
            .filter(or_(Playing.white_id == ctx.user.id, Playing.black_id == ctx.user.id),
                    Playing.channel_id == ctx.channel.id)
            .first()
        )

        if results is None:
            await ctx.channel.send(
                f"{ctx.user.mention} you do not have an active game in this channel"
            )
            return

        if ctx.user.id != results.white_id and ctx.user.id != results.black_id:
            print(ctx.user.id, results.white_id, results.black_id)
            await ctx.channel.send(f"{ctx.user.mention} you are not participating in any active games in this channel")
            return

        w_id = results.white_id
        b_id = results.black_id
        w = await self.bot.fetch_user(w_id)
        b = await self.bot.fetch_user(b_id)
        message_id = results.message_id
        movenum = results.movenum
        start_time = results.start_time
        board = results.board

        if (board.turn == chess.WHITE and ctx.user.id != w_id) or (
            board.turn == chess.BLACK and ctx.user.id != b_id
        ):
            print(board.turn == chess.WHITE)
            print(ctx.user.id != w_id)
            print(chess.WHITE, ctx.user.id, w_id, b_id)
            await ctx.channel.send(f"{ctx.user.mention} not your turn")
            return

        try:
            move = chess.Move.from_uci(move.strip())
            print("\nInput move, type of data:", move, type(move))
            print("Is it white's turn?", chess.WHITE)
            print("list(board.legal_moves):", list(board.legal_moves), "\n")

            if move in list(board.legal_moves):  #board.legal_moves is a generator!
                board.push(move)
                movenum += 1
                print("Move made")
            else:
                await ctx.channel.send(f"{ctx.user.mention} illegal move")
                return

        except:
            await ctx.channel.send(f"{ctx.user.mention} invalid move")
            raise

        self.session.query(Playing).filter(Playing.channel_id == ctx.channel.id).update(
            {Playing.movenum: movenum, Playing.board: board}
        )

        await self.render(message_id, ctx.channel.id)

        if (
            board.is_stalemate()
            or board.is_insufficient_material()
            or board.is_checkmate()
        ):
            if board.result() == "1/2-1/2":
                await ctx.channel.send(
                    f"{w.mention} {board.result()} {b.mention} gg game ended in a draw"
                )
            elif board.result() == "1-0":
                await ctx.channel.send(f"{w.mention} CONGRATULASHUNS ON WINNING")
            else:
                await ctx.channel.send(f"{b.mention} CONGRATULASHUNS ON WINNING")

            inst1 = Games(
                result=board.result(),
                white_id=w_id,
                black_id=b_id,
                moves=board.move_stack,
                server_id=ctx.guild.id,
                start_time=start_time,
            )
            self.session.add(inst1)
            self.session.query(Playing).filter(
                Playing.channel_id == ctx.channel.id
            ).delete()
        self.session.commit()

    async def render(self, message_id, channel_id):
        result = (
            self.session.query(Playing.board, Playing.movenum)
            .filter(Playing.message_id == message_id, Playing.channel_id == channel_id)
            .first()
        )

        board = result.board
        movenum = result.movenum
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)

        svg_obj = chess.svg.board(board=board, orientation=board.turn)
        png_obj = cairosvg.svg2png(bytestring=svg_obj)

        with open(f"{path}/challenges/{message_id}.png", "wb") as file:
            file.write(png_obj)
        file = discord.File(f"{path}/challenges/{message_id}.png")

        embed = message.embeds[0]
        embed.title = "Move " + str(math.ceil(movenum / 2))
        embed.set_image(url=f"attachment:/{path}/challenges/{message_id}.png")

        await message.edit(embed=embed, attachments=[file])

    @slash.command(name="challenge", description="Challenge someone to play chess")
    async def challenge(self, ctx, member: discord.Member):
        await ctx.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )

        check = (
            self.session.query(Playing)
            .filter(
                or_(Playing.white_id == ctx.user.id, Playing.black_id == ctx.user.id),
                Playing.channel_id == ctx.channel.id,
            )
            .first()
        )
        if check:
            await ctx.channel.send(
                f"{ctx.user.mention}, you already have an ongoing game in this channel"
            )
            return

        async def first_callback(tick_i):
            await tick_i.response.send_message(
                content="okey", delete_after=0.0001, ephemeral=True
            )

            if tick_i.user != member:
                print("Wrong person:", tick_i.user, "is not", member)
                return

            if tick_i.data["custom_id"] == "b2":
                await ctx.channel.send(
                    f"{ctx.user.mention}, challenge denied by {member}"
                )

            elif tick_i.data["custom_id"] == "b1":
                await ctx.channel.send(f"{ctx.user.mention}, challenge accepted")

                w = random.choice([ctx.user, member])
                if w == member:
                    b = ctx.user
                    print(f"w == member, id:{w.id}")
                    print(f"b == ctx.user, id:{b.id}")
                else:
                    b = member
                    print(f"w == ctx.user, id:{w.id}")
                    print(f"b == member, id:{b.id}")
                embed = discord.Embed(title=f"{str(w)[:-3]}(White) vs {str(b)[:-3]}(Black)")
                embed.set_image(url=f"attachment:/{path}/challenges/initial.png")

                file = discord.File(f"{path}/challenges/initial.png")

                message = await ctx.channel.send(
                    embed=embed, view=discord.ui.View(), file=file
                )

                inst1 = Playing(
                    white_id=w.id,
                    black_id=b.id,
                    message_id=message.id,
                    channel_id=message.channel.id,
                    board=chess.Board(),
                    movenum=0,
                )
                self.session.add(inst1)
                self.session.commit()

        b1 = Button(emoji="✅", custom_id="b1")
        b2 = Button(emoji="❌", custom_id="b2")
        b1.callback = b2.callback = first_callback
        view = View().add_item(b1).add_item(b2)

        await ctx.channel.send(
            f"{member.mention}, {str(ctx.user)[:-5]} challenges you to a game of chess!",
            view=view,
        )


# This is required for load_extension to work in main.py, discord py will add this fn as a cog to the guild
async def setup(bot: commands.Bot):
    await bot.add_cog(Challenge(bot))