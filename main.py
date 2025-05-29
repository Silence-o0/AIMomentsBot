import json
import os
from telegram import Update, Message, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, CommandHandler, filters
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID"))

MAPPING_FILE = "mapping.json"

def load_mapping():
    if not os.path.exists(MAPPING_FILE):
        return {}
    with open(MAPPING_FILE, "r") as f:
        return json.load(f)

def save_mapping(mapping):
    with open(MAPPING_FILE, "w") as f:
        json.dump(mapping, f)

user_mapping = load_mapping()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""👋 Вітаю! Тут Ви можете надіслати свої мемні ситуації користування ШІ (ChatGPT, DeepSeek або інші), а ми їх розглянемо і, можливо, опублікуємо.

❗️Надсилаючи нам контент, Ви погоджуєтесь на його публікацію від імені нашого каналу.

‼️Приймаємо лише україномовний або англомовний контент.""")

async def forward_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_message = update.message

    if user_message.photo:
        photo = user_message.photo[-1]
        caption = user_message.caption if user_message.caption else ""
        forwarded = await context.bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=photo.file_id,
            caption=f"Від [{user.full_name}](tg://user?id={user.id}):\n{caption}",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✨ Вашу пропозицію надіслано адмінам.")
    elif user_message.video:
        video = user_message.video
        caption = user_message.caption if user_message.caption else ""
        forwarded = await context.bot.send_video(
            chat_id=ADMIN_CHAT_ID,
            video=video.file_id,
            caption=f"Від [{user.full_name}](tg://user?id={user.id}):\n{caption}",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✨ Вашу пропозицію надіслано адмінам.")

    elif user_message.text:
        forwarded = await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"Від [{user.full_name}](tg://user?id={user.id}):\n{user_message.text}",
            parse_mode="Markdown"
        )

    else:
        return

    user_mapping[str(forwarded.message_id)] = {
        "user_id": user.id,
        "original_message_id": user_message.message_id
    }
    save_mapping(user_mapping)

async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    replied_message_id = str(update.message.reply_to_message.message_id)

    if replied_message_id in user_mapping:
        mapping = user_mapping[replied_message_id]
        target_user_id = mapping["user_id"]
        original_user_message_id = mapping["original_message_id"]

        await context.bot.send_message(
            chat_id=target_user_id,
            text=update.message.text,
            reply_to_message_id=original_user_message_id
        )

if __name__ == "__main__":
    WEBHOOK_PATH = "/webhook"
    PORT = int(os.environ.get('PORT', 8443))
    WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & (filters.TEXT | filters.PHOTO | filters.VIDEO), forward_to_admin))
    app.add_handler(MessageHandler(filters.Chat(ADMIN_CHAT_ID) & filters.REPLY & filters.TEXT, handle_reply))

    print("Bot started.")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=WEBHOOK_PATH,
        webhook_url=WEBHOOK_URL + WEBHOOK_PATH
    )
