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
ADMIN_ID = 7447021326 # <-- put your Telegram ID

# States
(
    MENU,
    TXT_UPLOAD,
    TXT_OPTIONS,
    VCF_TO_TXT,
    NUMBERS_TO_VCF,
    ADMIN_PANEL,
) = range(6)

# Default settings
settings = {
    "contact_name": "Contact",
    "vcf_name": "contacts",
    "navy_mode": False,
}

# Keyboards
main_menu = ReplyKeyboardMarkup(
    [["TXT ➜ VCF", "VCF ➜ TXT"], ["Numbers ➜ VCF"], ["Admin"]],
    resize_keyboard=True,
)

back_btn = ReplyKeyboardMarkup([["🔙 Back"]], resize_keyboard=True)


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Main Menu:", reply_markup=main_menu)
    return MENU


# MENU
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "TXT ➜ VCF":
        await update.message.reply_text(
            "Send TXT file (numbers line by line).", reply_markup=back_btn
        )
        return TXT_UPLOAD

    elif text == "VCF ➜ TXT":
        await update.message.reply_text("Send VCF file.", reply_markup=back_btn)
        return VCF_TO_TXT

    elif text == "Numbers ➜ VCF":
        await update.message.reply_text(
            "Send numbers (comma or line separated).", reply_markup=back_btn
        )
        return NUMBERS_TO_VCF

    elif text == "Admin":
        if update.message.from_user.id != ADMIN_ID:
            await update.message.reply_text("Not authorized ❌")
            return MENU

        await update.message.reply_text(
            "Admin Commands:\n/setname NAME\n/setvcf NAME\n/navy on|off",
            reply_markup=back_btn,
        )
        return ADMIN_PANEL

    return MENU


# BACK
async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Back to menu", reply_markup=main_menu)
    return MENU


# ---------------- TXT ➜ VCF ----------------

async def txt_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    file = await update.message.document.get_file()
    await file.download_to_drive("numbers.txt")

    await update.message.reply_text(
        "Now send:\nformat → files,contacts_per_file,name,vcf_name\n\nExample:\n2,50,John,MyVCF",
        reply_markup=back_btn,
    )
    return TXT_OPTIONS


async def txt_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    try:
        files, per_file, name, vcf_name = update.message.text.split(",")
        files = int(files)
        per_file = int(per_file)
    except:
        await update.message.reply_text("Invalid format ❌")
        return TXT_OPTIONS

    with open("numbers.txt") as f:
        numbers = f.read().splitlines()

    index = 0
    for fno in range(files):
        vcf_data = ""

        for i in range(per_file):
            if index >= len(numbers):
                break

            num = numbers[index]
            contact_name = (
                f"{name} {index+1}" if not settings["navy_mode"] else f"{name}_{index+1}"
            )

            vcf_data += f"""BEGIN:VCARD
VERSION:3.0
FN:{contact_name}
TEL;TYPE=CELL:{num}
END:VCARD
"""
            index += 1

        filename = f"{vcf_name}_{fno+1}.vcf"
        with open(filename, "w") as f:
            f.write(vcf_data)

        await update.message.reply_document(open(filename, "rb"))

    return await back(update, context)


# ---------------- VCF ➜ TXT ----------------

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


# ---------------- NUMBERS ➜ VCF ----------------

async def numbers_to_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    numbers = update.message.text.replace(",", "\n").splitlines()

    vcf_data = ""
    for i, num in enumerate(numbers):
        name = f"{settings['contact_name']} {i+1}"
        vcf_data += f"""BEGIN:VCARD
VERSION:3.0
FN:{name}
TEL;TYPE=CELL:{num}
END:VCARD
"""

    filename = f"{settings['vcf_name']}.vcf"
    with open(filename, "w") as f:
        f.write(vcf_data)

    await update.message.reply_document(open(filename, "rb"))
    return await back(update, context)


# ---------------- ADMIN ----------------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "🔙 Back":
        return await back(update, context)

    text = update.message.text

    if text.startswith("/setname"):
        settings["contact_name"] = text.split(" ", 1)[1]
        await update.message.reply_text("Default contact name updated ✅")

    elif text.startswith("/setvcf"):
        settings["vcf_name"] = text.split(" ", 1)[1]
        await update.message.reply_text("Default VCF name updated ✅")

    elif text.startswith("/navy"):
        mode = text.split(" ")[1]
        settings["navy_mode"] = True if mode == "on" else False
        await update.message.reply_text(f"Navy mode {mode} ✅")

    else:
        await update.message.reply_text("Invalid admin command ❌")

    return ADMIN_PANEL


# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, menu)],
            TXT_UPLOAD: [MessageHandler(filters.ALL, txt_upload)],
            TXT_OPTIONS: [MessageHandler(filters.TEXT, txt_options)],
            VCF_TO_TXT: [MessageHandler(filters.ALL, vcf_to_txt)],
            NUMBERS_TO_VCF: [MessageHandler(filters.TEXT, numbers_to_vcf)],
            ADMIN_PANEL: [MessageHandler(filters.TEXT, admin_panel)],
        },
        fallbacks=[MessageHandler(filters.TEXT, back)],
    )

    app.add_handler(conv)
    app.run_polling()


if __name__ == "__main__":
    main()