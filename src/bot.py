import logging

from agromodels import agromodels_conv
from auth import auth_conv
from config import TELEGRAM_BOT_KEY, METRICS_PORT, CONVERSATION_DUMP_FILE
from posts import posts_conv
from reports import reports_conv
from regions import regions_conv
from wiki import wiki_conv
from zonds import zonds_conv

from commands import *

from prometheus_client import start_wsgi_server
from telegram.ext import Updater, CommandHandler, PicklePersistence


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token
    persistence = PicklePersistence(filename=CONVERSATION_DUMP_FILE,
                                    store_callback_data=False,
                                    store_bot_data=False,
                                    store_chat_data=False,
                                    store_user_data=True)

    updater = Updater(
        TELEGRAM_BOT_KEY,
        persistence=persistence)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # REGISTER COMMANDS WITHOUT CONVERSATIONS
    dispatcher.add_handler(CommandHandler(Labels.START.value, start_command))
    dispatcher.add_handler(CommandHandler(Labels.HELP.value, help_command))
    dispatcher.add_handler(CommandHandler(Labels.RAINFALL.value, rainfall_command))
    dispatcher.add_handler(CommandHandler(Labels.LEGEND.value, legend_command))

    # REGISTER CONVERSATIONS
    dispatcher.add_handler(auth_conv)
    dispatcher.add_handler(reports_conv)
    dispatcher.add_handler(regions_conv)
    dispatcher.add_handler(zonds_conv)
    dispatcher.add_handler(posts_conv)
    dispatcher.add_handler(agromodels_conv)
    dispatcher.add_handler(wiki_conv)

    start_wsgi_server(METRICS_PORT)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
