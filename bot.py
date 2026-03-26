import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"

# STATES
FILENAME, CNAME, PERFILE, TOTALFILES, WAIT_FILE = range(5)

keyboard = [
    ["TXT ➝ VCF", "VCF ➝ TXT"],
    ["Numbers ➝ VCF"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Select option:", reply_markup=reply_markup)
    return ConversationHandler.END


# ===== TXT ➝ VCF FLOW =====

async def txt_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Enter file name:")
    return FILENAME


async def get_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["filename"] = update.message.text
    await update.message.reply_text("Enter contact name prefix:")
    return CNAME


async def get_cname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["cname"] = update.message.text
    await update.message.reply_text("Contacts per file:")
    return PERFILE


async def get_perfile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["perfile"] = int(update.message.text)
        await update.message.reply_text("Total files:")
        return TOTALFILES
    except:
        await update.message.reply_text("❌ Enter valid number")
        return PERFILE


async def get_totalfiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["totalfiles"] = int(update.message.text)
        await update.message.reply_text("Now send TXT file")
        return WAIT_FILE
    except:
        await update.message.reply_text("❌ Enter valid number")
        return TOTALFILES


async def process_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    path = update.message.document.file_name
    await file.download_to_drive(path)

    try:
        with open(path, "r") as f:
            numbers = [x.strip() for x in f if x.strip()]

        if not numbers:
            await update.message.reply_text("❌ Empty file")
            return ConversationHandler.END

        filename = context.user_data["filename"]
        cname = context.user_data["cname"]
        per_file = context.user_data["perfile"]
        total_files = context.user_data["totalfiles"]

        index = 0

        for file_no in range(total_files):
            if index >= len(numbers):
                break

            vcf_name = f"{filename}_{file_no+1}.vcf"

            with open(vcf_name, "w") as vcf:
                for _ in range(per_file):
                    if index >= len(numbers):
                        break

                    num = numbers[index]
                    vcf.write(
                        f"BEGIN:VCARD\nVERSION:3.0\nFN:{cname}{index+1}\nTEL:{num}\nEND:VCARD\n"
                    )
                    index += 1

            await update.message.reply_document(open(vcf_name, "rb"))
            os.remove(vcf_name)

        await update.message.reply_text("✅ Done")

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

    os.remove(path)
    return ConversationHandler.END


# ===== VCF ➝ TXT =====

async def vcf_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    path = update.message.document.file_name
    await file.download_to_drive(path)

    numbers = []
    with open(path, "r") as f:
        for line in f:
            if line.startswith("TEL"):
                numbers.append(line.split(":")[1].strip())

    with open("output.txt", "w") as txt:
        txt.write("\n".join(numbers))

    await update.message.reply_document(open("output.txt", "rb"))

    os.remove(path)
    os.remove("output.txt")


# ===== NUMBERS ➝ VCF =====
async def numbers_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    numbers = update.message.text.splitlines()

    with open("numbers.vcf", "w") as vcf:
        for i, num in enumerate(numbers):
            vcf.write(
                f"BEGIN:VCARD\nVERSION:3.0\nFN:Contact{i+1}\nTEL:{num.strip()}\nEND:VCARD\n"
            )

    await update.message.reply_document(open("numbers.vcf", "rb"))
    os.remove("numbers.vcf")


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Conversation for TXT ➝ VCF
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^TXT ➝ VCF$"), txt_start)],
        states={
            FILENAME: [MessageHandler(filters.TEXT, get_filename)],
            CNAME: [MessageHandler(filters.TEXT, get_cname)],
            PERFILE: [MessageHandler(filters.TEXT, get_perfile)],
            TOTALFILES: [MessageHandler(filters.TEXT, get_totalfiles)],
            WAIT_FILE: [MessageHandler(filters.Document.ALL, process_txt)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    app.add_handler(MessageHandler(filters.Regex("^VCF ➝ TXT$"), start))
    app.add_handler(MessageHandler(filters.Document.ALL, vcf_to_txt))

    app.add_handler(MessageHandler(filters.Regex("^Numbers ➝ VCF$"), start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, numbers_to_vcf))

    print("Bot Running...")
    app.run_polling()


if __name__ == "__main__":
    main()