import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"

keyboard = [
    ["TXT ➝ VCF", "VCF ➝ TXT"],
    ["Numbers ➝ VCF"]
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Select option:", reply_markup=reply_markup)

# BUTTON HANDLER
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "TXT ➝ VCF":
        context.user_data.clear()
        context.user_data["mode"] = "txt_to_vcf"
        context.user_data["step"] = "filename"
        await update.message.reply_text("Enter file name:")

    elif text == "VCF ➝ TXT":
        context.user_data["mode"] = "vcf_to_txt"
        await update.message.reply_text("Send VCF file")

    elif text == "Numbers ➝ VCF":
        context.user_data["mode"] = "num_to_vcf"
        await update.message.reply_text("Send numbers (one per line)")

# TEXT HANDLER (STEPS)
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    step = context.user_data.get("step")

    # ===== TXT TO VCF STEPS =====
    if mode == "txt_to_vcf":

        if step == "filename":
            context.user_data["filename"] = update.message.text
            context.user_data["step"] = "contactname"
            await update.message.reply_text("Enter contact name prefix:")
            return

        elif step == "contactname":
            context.user_data["contactname"] = update.message.text
            context.user_data["step"] = "perfile"
            await update.message.reply_text("Contacts per file:")
            return

        elif step == "perfile":
            context.user_data["perfile"] = int(update.message.text)
            context.user_data["step"] = "totalfiles"
            await update.message.reply_text("Total number of files:")
            return

        elif step == "totalfiles":
            context.user_data["totalfiles"] = int(update.message.text)
            context.user_data["step"] = "upload"
            await update.message.reply_text("Now send TXT file")
            return

    # ===== NUMBERS TO VCF =====
    elif mode == "num_to_vcf":
        numbers = update.message.text.splitlines()

        with open("numbers.vcf", "w") as vcf:
            for i, num in enumerate(numbers):
                vcf.write(f"BEGIN:VCARD\nVERSION:3.0\nFN:Contact{i}\nTEL:{num}\nEND:VCARD\n")

        await update.message.reply_document(open("numbers.vcf", "rb"))

# FILE HANDLER
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    file = await update.message.document.get_file()
    file_path = update.message.document.file_name
    await file.download_to_drive(file_path)

    # ===== TXT ➝ VCF ADVANCED =====
    if mode == "txt_to_vcf":
        with open(file_path, "r") as f:
            numbers = f.read().splitlines()

        filename = context.user_data["filename"]
        cname = context.user_data["contactname"]
        per_file = context.user_data["perfile"]
        total_files = context.user_data["totalfiles"]

        index = 0

        for file_no in range(total_files):
            vcf_name = f"{filename}_{file_no+1}.vcf"

            with open(vcf_name, "w") as vcf:
                for i in range(per_file):
                    if index >= len(numbers):
                        break

                    num = numbers[index]
                    vcf.write(
                        f"BEGIN:VCARD\nVERSION:3.0\nFN:{cname}{index+1}\nTEL:{num}\nEND:VCARD\n"
                    )
                    index += 1

            await update.message.reply_document(open(vcf_name, "rb"))
            os.remove(vcf_name)
            # ===== VCF ➝ TXT =====
    elif mode == "vcf_to_txt":
        numbers = []
        with open(file_path, "r") as f:
            for line in f:
                if line.startswith("TEL"):
                    numbers.append(line.split(":")[1].strip())

        with open("output.txt", "w") as txt:
            txt.write("\n".join(numbers))

        await update.message.reply_document(open("output.txt", "rb"))
        os.remove("output.txt")

    os.remove(file_path)

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot running...")
    app.run_polling()

if name == "main":
    main()