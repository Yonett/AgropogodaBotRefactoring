import logging

from auth import auth_conv
from reports import reports_conv
from regions import regions_conv
from zonds import zonds_conv
from posts import posts_conv
from agromodels import agromodels_conv
from wiki import wiki_conv

from commands import *

from telegram.ext import Updater, CommandHandler, PicklePersistence

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token

    persistence = PicklePersistence(filename="conversationbot")
    updater = Updater(
        "5342496177:AAFuLj90FFdry_768IyvVpleEpzTcrp-q1I",
        persistence=persistence)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # REGISTER COMMANDS WITHOUT CONVERSATIONS
    dispatcher.add_handler(CommandHandler("start", start_command))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("rainfall", rainfall_command))
    dispatcher.add_handler(CommandHandler("legend", legend_command))

    # REGISTER CONVERSATIONS
    dispatcher.add_handler(auth_conv)
    dispatcher.add_handler(reports_conv)
    dispatcher.add_handler(regions_conv)
    dispatcher.add_handler(zonds_conv)
    dispatcher.add_handler(posts_conv)
    dispatcher.add_handler(agromodels_conv)
    dispatcher.add_handler(wiki_conv)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
