import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"

(
    MENU,
    TXT_FILE,
    ASK_VCF_COUNT,
    ASK_CONTACTS_PER_FILE,
    ASK_CONTACT_NAME,
    ASK_VCF_NAME,
    PROCESS_TXT,
    VCF_TO_TXT,
    NUMBERS_TO_VCF,
    ADMIN_NAME,
    ADMIN_VCF_NAME,
    NAVY_NAME,
    NAVY_VCF_NAME
) = range(13)

main_menu = ReplyKeyboardMarkup(
    [
        ["TXT ➜ VCF", "VCF ➜ TXT"],
        ["Numbers ➜ VCF"],
        ["Admin VCF", "Navy VCF"]
    ],
    resize_keyboard=True
)

back_btn = ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Select option:", reply_markup=main_menu)
    return MENU


# BACK
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("Back to menu", reply_markup=main_menu)
    return MENU


# MENU
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "TXT ➜ VCF":
        await update.message.reply_text("Send TXT file", reply_markup=back_btn)
        return TXT_FILE

    elif text == "VCF ➜ TXT":
        await update.message.reply_text("Send VCF file", reply_markup=back_btn)
        return VCF_TO_TXT

    elif text == "Numbers ➜ VCF":
        await update.message.reply_text("Send numbers", reply_markup=back_btn)
        return NUMBERS_TO_VCF

    elif text == "Admin VCF":
        await update.message.reply_text("Enter Admin Name:", reply_markup=back_btn)
        return ADMIN_NAME

    elif text == "Navy VCF":
        await update.message.reply_text("Enter Navy Name:", reply_markup=back_btn)
        return NAVY_NAME

    return MENU


# TXT FLOW
async def txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    file = await update.message.document.get_file()
    await file.download_to_drive("numbers.txt")

    with open("numbers.txt") as f:
        context.user_data["numbers"] = f.read().splitlines()

    await update.message.reply_text("How many VCF files?", reply_markup=back_btn)
    return ASK_VCF_COUNT


async def ask_vcf_count(update: Update, context):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    context.user_data["vcf_count"] = int(update.message.text)
    await update.message.reply_text("Contacts per file?")
    return ASK_CONTACTS_PER_FILE


async def ask_contacts(update: Update, context):
    context.user_data["per_file"] = int(update.message.text)
    await update.message.reply_text("Contact name prefix?")
    return ASK_CONTACT_NAME


async def ask_name(update: Update, context):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("VCF file name?")
    return ASK_VCF_NAME


async def generate_vcf(update: Update, context):
    base_name = update.message.text
    numbers = context.user_data["numbers"]
    per_file = context.user_data["per_file"]
    name = context.user_data["name"]

    files = []
    for i in range(0, len(numbers), per_file):
        chunk = numbers[i:i+per_file]
        filename = f"{base_name}_{i//per_file+1}.vcf"

        with open(filename, "w") as f:
            for j, num in enumerate(chunk):
                f.write(f"""BEGIN:VCARD
VERSION:3.0
FN:{name} {i+j+1}
TEL;TYPE=CELL:{num}
END:VCARD
""")

        files.append(filename)

    for file in files:
        await update.message.reply_document(open(file, "rb"))

    return await back(update, context)


# ADMIN VCF
async def admin_name(update: Update, context):
    context.user_data["admin"] = update.message.text
    await update.message.reply_text("Enter VCF name:")
    return ADMIN_VCF_NAME


async def admin_vcf(update: Update, context):
    vcf_name = update.message.text
    admin = context.user_data["admin"]
    content = f"""BEGIN:VCARD
VERSION:3.0
FN:{admin} (ADMIN)
TEL;TYPE=CELL:+0000000000
END:VCARD
"""

    file = f"{vcf_name}.vcf"
    with open(file, "w") as f:
        f.write(content)

    await update.message.reply_document(open(file, "rb"))
    return await back(update, context)


# NAVY VCF
async def navy_name(update: Update, context):
    context.user_data["navy"] = update.message.text
    await update.message.reply_text("Enter VCF name:")
    return NAVY_VCF_NAME


async def navy_vcf(update: Update, context):
    vcf_name = update.message.text
    navy = context.user_data["navy"]

    content = f"""BEGIN:VCARD
VERSION:3.0
FN:{navy} (NAVY)
TEL;TYPE=CELL:+0000000000
END:VCARD
"""

    file = f"{vcf_name}.vcf"
    with open(file, "w") as f:
        f.write(content)

    await update.message.reply_document(open(file, "rb"))
    return await back(update, context)


# VCF ➜ TXT
async def vcf_to_txt(update: Update, context):
    file = await update.message.document.get_file()
    await file.download_to_drive("contacts.vcf")

    numbers = []
    with open("contacts.vcf") as f:
        for line in f:
            if "TEL" in line:
                numbers.append(line.split(":")[1].strip())

    with open("numbers.txt", "w") as f:
        f.write("\n".join(numbers))

    await update.message.reply_document(open("numbers.txt", "rb"))
    return await back(update, context)


# NUMBERS ➜ VCF
async def numbers_to_vcf(update: Update, context):
    text = update.message.text
    numbers = text.replace(",", "\n").splitlines()

    with open("numbers.vcf", "w") as f:
        for i, num in enumerate(numbers):
            f.write(f"""BEGIN:VCARD
VERSION:3.0
FN:User {i+1}
TEL;TYPE=CELL:{num}
END:VCARD
""")

    await update.message.reply_document(open("numbers.vcf", "rb"))
    return await back(update, context)


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT, menu)],

            TXT_FILE: [MessageHandler(filters.ALL, txt_file)],
            ASK_VCF_COUNT: [MessageHandler(filters.TEXT, ask_vcf_count)],
            ASK_CONTACTS_PER_FILE: [MessageHandler(filters.TEXT, ask_contacts)],
            ASK_CONTACT_NAME: [MessageHandler(filters.TEXT, ask_name)],
            ASK_VCF_NAME: [MessageHandler(filters.TEXT, generate_vcf)],

            ADMIN_NAME: [MessageHandler(filters.TEXT, admin_name)],
            ADMIN_VCF_NAME: [MessageHandler(filters.TEXT, admin_vcf)],

            NAVY_NAME: [MessageHandler(filters.TEXT, navy_name)],
            NAVY_VCF_NAME: [MessageHandler(filters.TEXT, navy_vcf)],

            VCF_TO_TXT: [MessageHandler(filters.ALL, vcf_to_txt)],
            NUMBERS_TO_VCF: [MessageHandler(filters.TEXT, numbers_to_vcf)],
        },
        fallbacks=[MessageHandler(filters.TEXT, back)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()