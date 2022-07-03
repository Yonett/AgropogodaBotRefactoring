from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from methods import get_regions_keyboard, get_companies_keyboard
from commands import cancel_command

REGION_STEP, COMPANY_STEP = range(2)


def reports_command(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(get_regions_keyboard())
    update.message.reply_markdown_v2(
        text="Выберите район: ", reply_markup=reply_markup)

    return REGION_STEP


def enter_region(update: Update, context: CallbackContext) -> None:
    context.user_data['region'] = update.message.text
    reply_markup = ReplyKeyboardMarkup(get_companies_keyboard(context))
    update.message.reply_markdown_v2(
        text="Выберите компанию: ", reply_markup=reply_markup)

    return COMPANY_STEP


def enter_company(update: Update, context: CallbackContext) -> None:
    update.message.reply_markdown_v2(
        text=f"Отчёт для {update.message.text} из района {context.user_data.get('region')}",
        reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


reports_conv = ConversationHandler(
    entry_points=[
        CommandHandler(
            'reports',
            reports_command)],
    states={
        REGION_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_region)],
        COMPANY_STEP: [
            MessageHandler(
                Filters.text & (
                    ~ Filters.text("/cancel")),
                enter_company)]},
    fallbacks=[
        CommandHandler(
            'cancel',
            cancel_command)],
    allow_reentry=True,
    persistent=False)
