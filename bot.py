from telegram import Update,ReplyKeyboardMarkup
from telegram.ext import *
import config
import os
from converter import *

CONTACT_NAME,VCF_NAME,PER_FILE,FILE_COUNT,TXT_FILE=range(5)

menu=ReplyKeyboardMarkup(
[
["TXT ➜ VCF","VCF ➜ TXT"],
["Numbers ➜ VCF"],
["Back to Menu"]
],
resize_keyboard=True
)

def is_admin(user_id):
    return user_id in config.ADMINS


def is_allowed(user_id):

    if is_admin(user_id):
        return True

    try:
        with open(config.USERS_FILE) as f:
            users=f.read().splitlines()

        return str(user_id) in users

    except:
        return False


async def check_access(update):

    user_id=update.effective_user.id

    if not is_allowed(user_id):

        await update.message.reply_text(
        "❌ Access denied.\nAsk admin for permission."
        )

        return False

    return True


async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if not config.BOT_STATUS:
        await update.message.reply_text("Bot is OFF")
        return

    if not await check_access(update):
        return

    await update.message.reply_text(
    "VCF Converter Bot",
    reply_markup=menu
    )


async def txt_start(update,context):

    if not await check_access(update):
        return

    await update.message.reply_text("Enter contact name")
    return CONTACT_NAME


async def contact_name(update,context):

    context.user_data["contact"]=update.message.text
    await update.message.reply_text("Enter VCF file name")

    return VCF_NAME


async def vcf_name(update,context):

    context.user_data["vcfname"]=update.message.text
    await update.message.reply_text("Contacts per VCF file")

    return PER_FILE


async def per_file(update,context):

    context.user_data["perfile"]=int(update.message.text)
    await update.message.reply_text("How many VCF files")

    return FILE_COUNT


async def file_count(update,context):

    context.user_data["count"]=int(update.message.text)
    await update.message.reply_text("Send TXT file")

    return TXT_FILE


async def generate(update,context):

    file=await update.message.document.get_file()
    await file.download_to_drive("numbers.txt")

    with open("numbers.txt") as f:
        numbers=f.read().splitlines()

    files=txt_to_vcf(
    numbers,
    context.user_data["contact"],
    context.user_data["vcfname"],
    context.user_data["perfile"],
    context.user_data["count"]
    )

    for f in files:
        await update.message.reply_document(open(f,"rb"))
        os.remove(f)

    os.remove("numbers.txt")

    return ConversationHandler.END


async def vcf_txt(update,context):

    if not await check_access(update):
        return

    await update.message.reply_text("Send VCF file")


async def vcf_file(update,context):

    file=await update.message.document.get_file()
    await file.download_to_drive("contacts.vcf")

    txt=vcf_to_txt("contacts.vcf")

    await update.message.reply_document(open(txt,"rb"))

    os.remove("contacts.vcf")
    os.remove(txt)


async def numbers(update,context):

    if not await check_access(update):
        return

    nums=update.message.text.split()

    vcf=numbers_to_vcf(nums)

    await update.message.reply_document(open(vcf,"rb"))

    os.remove(vcf)


async def allow(update,context):

    if not is_admin(update.effective_user.id):
        return

    try:

        user=context.args[0]

        with open(config.USERS_FILE,"a") as f:
            f.write(user+"\n")

        await update.message.reply_text("User allowed")

    except:
        await update.message.reply_text("Usage: /allow userid")


async def deny(update,context):

    if not is_admin(update.effective_user.id):
        return

    try:

        user=context.args[0]

        with open(config.USERS_FILE) as f:
            users=f.read().splitlines()

        users=[u for u in users if u!=user]

        with open(config.USERS_FILE,"w") as f:
            for u in users:
                f.write(u+"\n")

        await update.message.reply_text("User removed")

    except:
        await update.message.reply_text("Usage: /deny userid")


app=ApplicationBuilder().token(config.TOKEN).build()

async def back_menu(update, context):
    await update.message.reply_text(
        "Main Menu",
        reply_markup=menu
    )
    return ConversationHandler.END


conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("TXT ➜ VCF"), txt_start)],
    states={
        CONTACT_NAME: [
            MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu),
            MessageHandler(filters.TEXT, contact_name)
        ],
        VCF_NAME: [
            MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu),
            MessageHandler(filters.TEXT, vcf_name)
        ],
        PER_FILE: [
            MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu),
            MessageHandler(filters.TEXT, per_file)
        ],
        FILE_COUNT: [
            MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu),
            MessageHandler(filters.TEXT, file_count)
        ],
        TXT_FILE: [
            MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu),
            MessageHandler(filters.Document.ALL, generate)
        ]
    },
    fallbacks=[
        MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu)
    ]
)

app.add_handler(CommandHandler("start",start))
app.add_handler(conv)

app.add_handler(MessageHandler(filters.Regex("VCF ➜ TXT"),vcf_txt))
app.add_handler(MessageHandler(filters.Document.ALL,vcf_file))
app.add_handler(MessageHandler(filters.Regex("Numbers ➜ VCF"),numbers))

app.add_handler(MessageHandler(filters.Regex("🔙 Back to Menu"), back_menu))

app.add_handler(CommandHandler("allow",allow))
app.add_handler(CommandHandler("deny",deny))

print("Bot Running...")

app.run_polling()