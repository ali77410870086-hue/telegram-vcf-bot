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
(
    MENU,
    TXT_FILE,
    ASK_NAME,
    ASK_PER_FILE,
    ASK_TOTAL_FILE,
    ASK_VCF_NAME,
    VCF_TO_TXT,
    NUMBERS_TO_VCF,
    ADMIN_NUMBERS,
    ADMIN_NAME,
    ADMIN_VCF_NAME,
) = range(11)

# Keyboards
main_menu = ReplyKeyboardMarkup(
    [
        ["TXT ➜ VCF", "VCF ➜ TXT"],
        ["Numbers ➜ VCF", "Admin / Navy VCF"],
    ],
    resize_keyboard=True,
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
        await update.message.reply_text(
            "Send numbers (comma or line)", reply_markup=back_btn
        )
        return NUMBERS_TO_VCF

    elif text == "Admin / Navy VCF":
        await update.message.reply_text(
            "Send numbers for admin VCF", reply_markup=back_btn
        )
        return ADMIN_NUMBERS

    return MENU


# ================= TXT ➜ VCF FLOW =================

async def txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    file = await update.message.document.get_file()
    await file.download_to_drive("numbers.txt")

    with open("numbers.txt") as f:
        context.user_data["numbers"] = f.read().splitlines()

    await update.message.reply_text("Enter contact name prefix:", reply_markup=back_btn)
    return ASK_NAME


async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    context.user_data["name"] = update.message.text
    await update.message.reply_text("Contacts per VCF file:", reply_markup=back_btn)
    return ASK_PER_FILE


async def ask_per_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    context.user_data["per_file"] = int(update.message.text)
    await update.message.reply_text("How many VCF files:", reply_markup=back_btn)
    return ASK_TOTAL_FILE


async def ask_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    context.user_data["total"] = int(update.message.text)
    await update.message.reply_text("Enter VCF file base name:", reply_markup=back_btn)
    return ASK_VCF_NAME


async def generate_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    base_name = update.message.text
    numbers = context.user_data["numbers"]
    per_file = context.user_data["per_file"]
    total = context.user_data["total"]
    name = context.user_data["name"]

    index = 0

    for f_num in range(total):
        vcf = ""
        for i in range(per_file):
            if index >= len(numbers):
                break
            num = numbers[index]
            vcf += f"""BEGIN:VCARD
VERSION:3.0
FN:{name} {index+1}
TEL;TYPE=CELL:{num}
END:VCARD
"""
            index += 1
            file_name = f"{base_name}_{f_num+1}.vcf"
        with open(file_name, "w") as f:
            f.write(vcf)

        await update.message.reply_document(open(file_name, "rb"))

    return await back(update, context)


# ================= VCF ➜ TXT =================

async def vcf_to_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

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


# ================= NUMBERS ➜ VCF =================

async def numbers_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    nums = update.message.text.replace(",", "\n").splitlines()

    vcf = ""
    for i, num in enumerate(nums):
        vcf += f"""BEGIN:VCARD
VERSION:3.0
FN:Contact {i+1}
TEL;TYPE=CELL:{num}
END:VCARD
"""

    with open("contacts.vcf", "w") as f:
        f.write(vcf)

    await update.message.reply_document(open("contacts.vcf", "rb"))
    return await back(update, context)


# ================= ADMIN / NAVY VCF =================

async def admin_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    context.user_data["admin_nums"] = update.message.text.replace(",", "\n").splitlines()

    await update.message.reply_text("Enter admin name:", reply_markup=back_btn)
    return ADMIN_NAME


async def admin_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    context.user_data["admin_name"] = update.message.text
    await update.message.reply_text("Enter VCF file name:", reply_markup=back_btn)
    return ADMIN_VCF_NAME


async def admin_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    file_name = update.message.text + ".vcf"
    nums = context.user_data["admin_nums"]
    admin_name = context.user_data["admin_name"]

    vcf = ""
    for i, num in enumerate(nums):
        vcf += f"""BEGIN:VCARD
VERSION:3.0
FN:{admin_name} {i+1}
TEL;TYPE=CELL:{num}
END:VCARD
"""

    with open(file_name, "w") as f:
        f.write(vcf)

    await update.message.reply_document(open(file_name, "rb"))
    return await back(update, context)


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT, menu)],

            TXT_FILE: [MessageHandler(filters.ALL, txt_file)],
            ASK_NAME: [MessageHandler(filters.TEXT, ask_name)],
            ASK_PER_FILE: [MessageHandler(filters.TEXT, ask_per_file)],
            ASK_TOTAL_FILE: [MessageHandler(filters.TEXT, ask_total)],
            ASK_VCF_NAME: [MessageHandler(filters.TEXT, generate_vcf)],

            VCF_TO_TXT: [MessageHandler(filters.ALL, vcf_to_txt)],
            NUMBERS_TO_VCF: [MessageHandler(filters.TEXT, numbers_to_vcf)],

            ADMIN_NUMBERS: [MessageHandler(filters.TEXT, admin_numbers)],
            ADMIN_NAME: [MessageHandler(filters.TEXT, admin_name)],
            ADMIN_VCF_NAME: [MessageHandler(filters.TEXT, admin_vcf)],
        },
        fallbacks=[MessageHandler(filters.TEXT, back)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()