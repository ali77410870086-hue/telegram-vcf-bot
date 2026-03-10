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

user_data_store = {}

main_menu = [["TXT ➜ VCF", "VCF ➜ TXT"], ["Numbers ➜ VCF"]]
back_menu = [["Back"]]


# START COMMAND
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
    await update.message.reply_text(
        "Welcome to VCF Converter Bot\nChoose an option:",
        reply_markup=keyboard,
    )


# HANDLE TEXT MESSAGES
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "Back":
        user_data_store[user_id] = {}
        keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)
        await update.message.reply_text("Returned to main menu.", reply_markup=keyboard)
        return

    if text == "TXT ➜ VCF":
        user_data_store[user_id] = {"step": "contact_name"}
        await update.message.reply_text(
            "Enter contact name:", reply_markup=ReplyKeyboardMarkup(back_menu, resize_keyboard=True)
        )
        return

    if text == "Numbers ➜ VCF":
        user_data_store[user_id] = {"step": "numbers_vcf_name"}
        await update.message.reply_text(
            "Enter VCF file name:", reply_markup=ReplyKeyboardMarkup(back_menu, resize_keyboard=True)
        )
        return

    if user_id not in user_data_store:
        return

    step = user_data_store[user_id].get("step")

    try:

        if step == "contact_name":
            user_data_store[user_id]["contact_name"] = text
            user_data_store[user_id]["step"] = "vcf_name"
            await update.message.reply_text("Enter VCF file name:")
            return

        if step == "vcf_name":
            user_data_store[user_id]["vcf_name"] = text
            user_data_store[user_id]["step"] = "contacts_per_file"
            await update.message.reply_text("How many contacts per VCF?")
            return

        if step == "contacts_per_file":
            user_data_store[user_id]["contacts_per_file"] = int(text)
            user_data_store[user_id]["step"] = "file_count"
            await update.message.reply_text("How many VCF files do you want?")
            return

        if step == "file_count":
            user_data_store[user_id]["file_count"] = int(text)
            user_data_store[user_id]["step"] = "upload_txt"
            await update.message.reply_text("Now send TXT file with numbers.")
            return

        if step == "numbers_vcf_name":
            user_data_store[user_id]["vcf_name"] = text
            user_data_store[user_id]["step"] = "send_numbers"
            await update.message.reply_text(
                "Send numbers separated by line.\nExample:\n919999999999"
            )
            return

        if step == "send_numbers":
            numbers = text.split("\n")
            filename = user_data_store[user_id]["vcf_name"] + ".vcf"

            with open(filename, "w") as vcf:
                for i, number in enumerate(numbers):
                    vcf.write(
                        f"BEGIN:VCARD\nVERSION:3.0\nFN:Contact{i+1}\nTEL;TYPE=CELL:{number}\nEND:VCARD\n"
                    )

            await update.message.reply_document(open(filename, "rb"))
            os.remove(filename)

            await update.message.reply_text("VCF created successfully.")
            user_data_store[user_id] = {}
            return

    except:
        await update.message.reply_text("Invalid input. Please try again.")


# HANDLE TXT FILE
async def handle_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_data_store.get(user_id, {}).get("step") != "upload_txt":
        return

    file = await update.message.document.get_file()
    await file.download_to_drive("numbers.txt")
    with open("numbers.txt") as f:
        numbers = f.read().splitlines()

    data = user_data_store[user_id]

    name = data["contact_name"]
    per_file = data["contacts_per_file"]
    count = data["file_count"]
    vcf_name = data["vcf_name"]

    index = 0

    for i in range(count):

        filename = f"{vcf_name}_{i+1}.vcf"

        with open(filename, "w") as vcf:

            for j in range(per_file):

                if index >= len(numbers):
                    break

                number = numbers[index]

                vcf.write(
                    f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}{index+1}\nTEL;TYPE=CELL:{number}\nEND:VCARD\n"
                )

                index += 1

        await update.message.reply_document(open(filename, "rb"))
        os.remove(filename)

    user_data_store[user_id] = {}
    await update.message.reply_text("VCF files generated successfully.")


# HANDLE VCF FILE
async def handle_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = await update.message.document.get_file()
    await file.download_to_drive("contacts.vcf")

    numbers = []

    with open("contacts.vcf") as f:

        for line in f:

            if "TEL" in line:
                number = line.split(":")[1].strip()
                numbers.append(number)

    with open("numbers.txt", "w") as out:

        for n in numbers:
            out.write(n + "\n")

    await update.message.reply_document(open("numbers.txt", "rb"))

    os.remove("numbers.txt")
    os.remove("contacts.vcf")


# MAIN FUNCTION
def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_handler(MessageHandler(filters.Document.FileExtension("txt"), handle_txt))

    app.add_handler(MessageHandler(filters.Document.FileExtension("vcf"), handle_vcf))

    print("Bot Running...")

    app.run_polling()


if __name__ == "__main__":
    main()