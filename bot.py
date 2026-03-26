from telegram.ext import *
from telegram import Update
import config
from menu import main_menu
from converter import txt_to_vcf, vcf_to_txt, numbers_to_vcf  # Ensure converter.py exists in the same directory
from admin import *

CONTACT_NAME,VCF_NAME,PER_FILE,FILE_COUNT,TXT_FILE=range(5)

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if not config.BOT_STATUS:
        await update.message.reply_text("Bot is OFF")
        return

    await update.message.reply_text(
    "VCF Converter Bot",
    reply_markup=main_menu
    )

async def txt_start(update,context):

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

    return ConversationHandler.END


async def vcf_txt(update,context):

    await update.message.reply_text("Send VCF file")


async def vcf_file(update,context):

    file=await update.message.document.get_file()

    await file.download_to_drive("contacts.vcf")

    txt=vcf_to_txt("contacts.vcf")

    await update.message.reply_document(open(txt,"rb"))


async def numbers(update,context):

    nums=update.message.text.split()

    vcf=numbers_to_vcf(nums)

    await update.message.reply_document(open(vcf,"rb"))


app=ApplicationBuilder().token(config.TOKEN).build()

conv=ConversationHandler(

entry_points=[MessageHandler(filters.Regex("TXT ➜ VCF"),txt_start)],

states={

CONTACT_NAME:[MessageHandler(filters.TEXT,contact_name)],

VCF_NAME:[MessageHandler(filters.TEXT,vcf_name)],

PER_FILE:[MessageHandler(filters.TEXT,per_file)],

FILE_COUNT:[MessageHandler(filters.TEXT,file_count)],

TXT_FILE:[MessageHandler(filters.Document.ALL,generate)]

},

fallbacks=[]
)

app.add_handler(CommandHandler("start",start))

app.add_handler(conv)

app.add_handler(MessageHandler(filters.Regex("VCF ➜ TXT"),vcf_txt))

app.add_handler(MessageHandler(filters.Document.ALL,vcf_file))

app.add_handler(MessageHandler(filters.Regex("Numbers ➜ VCF"),numbers))

app.add_handler(CommandHandler("boton",bot_on))
app.add_handler(CommandHandler("botoff",bot_off))
app.add_handler(CommandHandler("addadmin",add_admin))

print("Bot Running...")

app.run_polling()