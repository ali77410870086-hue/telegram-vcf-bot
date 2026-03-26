import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"

# States
MENU, TXT_TO_VCF, VCF_TO_TXT, NUMBERS_TO_VCF = range(4)

# Keyboards
main_menu = ReplyKeyboardMarkup(
    [["TXT ➜ VCF", "VCF ➜ TXT"], ["Numbers ➜ VCF"]],
    resize_keyboard=True,
)

back_btn = ReplyKeyboardMarkup(
    [["🔙 Back"]],
    resize_keyboard=True,
)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Choose an option:", reply_markup=main_menu)
    return MENU


# MENU HANDLER
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "TXT ➜ VCF":
        await update.message.reply_text(
            "Send TXT file with numbers (one per line).", reply_markup=back_btn
        )
        return TXT_TO_VCF

    elif text == "VCF ➜ TXT":
        await update.message.reply_text(
            "Send VCF file.", reply_markup=back_btn
        )
        return VCF_TO_TXT

    elif text == "Numbers ➜ VCF":
        await update.message.reply_text(
            "Send numbers separated by comma or line.", reply_markup=back_btn
        )
        return NUMBERS_TO_VCF

    else:
        return MENU


# BACK BUTTON
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Back to menu", reply_markup=main_menu)
    return MENU


# TXT ➜ VCF
async def txt_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    file = await update.message.document.get_file()
    file_path = "numbers.txt"
    await file.download_to_drive(file_path)

    with open(file_path, "r") as f:
        numbers = f.read().splitlines()

    vcf_content = ""
    for i, num in enumerate(numbers):
        vcf_content += f"""BEGIN:VCARD
VERSION:3.0
FN:Contact {i+1}
TEL;TYPE=CELL:{num}
END:VCARD
"""

    with open("contacts.vcf", "w") as f:
        f.write(vcf_content)

    await update.message.reply_document(document=open("contacts.vcf", "rb"))
    return await back(update, context)


# VCF ➜ TXT
async def vcf_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    file = await update.message.document.get_file()
    file_path = "contacts.vcf"
    await file.download_to_drive(file_path)

    numbers = []
    with open(file_path, "r") as f:
        for line in f:
            if "TEL" in line:
                numbers.append(line.split(":")[1].strip())

    with open("numbers.txt", "w") as f:
        f.write("\n".join(numbers))

    await update.message.reply_document(document=open("numbers.txt", "rb"))
    return await back(update, context)


# NUMBERS ➜ VCF
async def numbers_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    text = update.message.text
    numbers = text.replace(",", "\n").splitlines()

    vcf_content = ""
    for i, num in enumerate(numbers):
        vcf_content += f"""BEGIN:VCARD
VERSION:3.0
FN:Contact {i+1}
TEL;TYPE=CELL:{num}
END:VCARD
"""

    with open("contacts.vcf", "w") as f:
        f.write(vcf_content)

    await update.message.reply_document(document=open("contacts.vcf", "rb"))
    return await back(update, context)


# MAIN FUNCTION
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler)],
            TXT_TO_VCF: [MessageHandler(filters.ALL, txt_to_vcf)],
            VCF_TO_TXT: [MessageHandler(filters.ALL, vcf_to_txt)],
            NUMBERS_TO_VCF: [MessageHandler(filters.ALL, numbers_to_vcf)],
        },
        fallbacks=[MessageHandler(filters.TEXT, back)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()