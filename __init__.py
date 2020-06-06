from redbot.core.bot import Red

from .indexer import Indexer

def setup(bot: Red) -> None:
    bot.add_cog(Indexer())
