# Viewing of games should happen only in dms.

import math
import os

import cairosvg
import chess
import chess.engine
import chess.pgn
import chess.svg
import discord
from discord import SelectOption
from discord import app_commands as slash
from discord.ext import commands
from discord.ui import Button, View, Select
from dotenv import load_dotenv
from sqlalchemy import or_

from challenge import Games
from dbs import Viewing
from utility import Session

load_dotenv()
path = os.environ.get("path")

"""it is not possible to fetch a message using just the message ID without specifying the 
channel ID. In Discord's API, the combination of the message ID and the channel ID uniquely 
identifies a message within a server."""


class Viewfn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session = Session()

    def cog_unload(self):
        self.session.close()  # Close the session when the cog is unloaded

    async def button_i(self, i, games):
        embed = discord.Embed(title="Game")

        b1 = Button(emoji="⏪", custom_id="b1")
        b2 = Button(emoji="◀", custom_id="b2")
        b3 = Button(emoji="▶", custom_id="b3")
        b4 = Button(emoji="⏩", custom_id="b4")

        b1.callback = b2.callback = b3.callback = b4.callback = lambda i: self.game_i(
            i, message.id, message.channel.id
        )
        view = View().add_item(b1).add_item(b2).add_item(b3).add_item(b4)

        svg_obj = chess.svg.board(board=chess.Board())
        png_obj = cairosvg.svg2png(bytestring=svg_obj)

        with open(f"{path}/views/initial.png", "wb") as file:
            file.write(png_obj)  # type:ignore
        file = discord.File(f"{path}/views/initial.png")

        message = await i.user.send(embed=embed, view=view, file=file)
        # Till this line we just send a board to the user in the starting position

        # Now we find the game they want and add the board object of that game to the db so that game_i() can access it
        index = int(i.data["values"][0][1])
        game = games[index]

        board = chess.Board()

        inst1 = Viewing(
            board=board,
            moves=game.moves,
            movenum=0,
            embed_id=message.id,
            channel_id=message.channel.id,
        )
        self.session.add(inst1)
        print("Added to viewing")
        self.session.commit()

    async def game_i(self, i, embed_id, channel_id):
        await i.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )
        # Just need to extract moves of the game from the board object stored for that row
        # in the database

        result = (
            self.session.query(Viewing)
            .filter(Viewing.embed_id == embed_id, Viewing.channel_id == channel_id)
            .first()
        )

        board = result.board
        moves = result.moves
        movenum = result.movenum

        if i.data["custom_id"] == "b1":
            if movenum == 0:
                return

            self.session.query(Viewing).filter(
                Viewing.embed_id == embed_id, Viewing.channel_id == channel_id
            ).update({Viewing.board: chess.Board(), Viewing.movenum: 0})

        elif i.data["custom_id"] == "b2":
            if movenum == 0:
                return
            elif movenum == len(moves):
                board = chess.Board()
                for move in moves[:-1]:
                    board.push(move)
                movenum -= 1
            else:
                board.pop()
                movenum -= 1

            self.session.query(Viewing).filter(
                Viewing.embed_id == embed_id, Viewing.channel_id == channel_id
            ).update({Viewing.board: board, Viewing.movenum: movenum})

        elif i.data["custom_id"] == "b3":
            if movenum == len(moves):
                return

            board.push(moves[movenum])
            movenum += 1
            print("1", movenum)
            self.session.query(Viewing).filter(
                Viewing.embed_id == embed_id, Viewing.channel_id == channel_id
            ).update({Viewing.board: board, Viewing.movenum: movenum})
            print("2", movenum)

        elif i.data["custom_id"] == "b4":
            if movenum == len(moves):
                return
            print("3", movenum)
            for move in moves[movenum:]:
                board.push(move)
                movenum += 1
            print("4", movenum)
            self.session.query(Viewing).filter(
                Viewing.embed_id == embed_id, Viewing.channel_id == channel_id
            ).update({Viewing.board: board, Viewing.movenum: movenum})

        self.session.commit()

        await self.render(embed_id, channel_id)

    async def render(self, embed_id, channel_id):
        channel = self.bot.get_channel(channel_id)
        message = await channel.fetch_message(embed_id)

        result = (
            self.session.query(Viewing.board, Viewing.movenum)
            .filter(Viewing.embed_id == embed_id, Viewing.channel_id == channel_id)
            .first()
        )

        board = result.board
        movenum = result.movenum
        svg_obj = chess.svg.board(board=board, orientation=board.turn)
        png_obj = cairosvg.svg2png(bytestring=svg_obj)

        with open(f"{path}/views/{embed_id}{channel_id}.png", "wb") as file:
            file.write(png_obj)  # type:ignore
        file = discord.File(f"{path}/views/{embed_id}{channel_id}.png")

        embed = message.embeds[0]
        embed.title = "Move " + str(math.ceil(movenum / 2))
        embed.set_image(url=f"attachment:/{path}/views/{embed_id}{channel_id}.png")

        await message.edit(embed=embed, attachments=[file])

    @slash.command(name="view", description="View past games")
    async def view(self, ctx, member: discord.Member):
        await ctx.response.send_message(
            content="okey", delete_after=0.0001, ephemeral=True
        )
        # User should input a member, in DMs it should show them an embed with 5 columns: white, black,
        # result, start date & time, green arrow buttons. Only after they click a button,
        # a board of that game will load in their DMs, and they can view it

        # Retrieve past games for the specified member from the database
        games = (
            self.session.query(Games)
            .filter(
                or_(Games.white_id == member.id, Games.black_id == member.id),
                Games.server_id == ctx.guild.id,
            )
            .all()
        )

        print("Games:", games)

        for index, game in enumerate(games):
            w = await self.bot.fetch_user(game.white_id)
            b = await self.bot.fetch_user(game.black_id)
            options = [
                SelectOption(
                    label=f"{w.name} | {b.name} | {game.result} | {game.start_time.strftime('%d/%m/%y %H:%M')}",
                    value=f"B{index}",
                )
            ]

        select = Select(placeholder="Select a game", options=options)
        select.callback = lambda i: self.button_i(i, games)

        view = View()
        view.add_item(select)

        await ctx.user.send(view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Viewfn(bot))
