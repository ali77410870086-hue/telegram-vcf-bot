import os
import zipfile
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


# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

    await update.message.reply_text(
        "📂 VCF Converter Bot\n\nChoose an option:",
        reply_markup=keyboard
    )


# TEXT HANDLER
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id
    text = update.message.text

    if text == "Back":

        user_data_store[user_id] = {}

        keyboard = ReplyKeyboardMarkup(main_menu, resize_keyboard=True)

        await update.message.reply_text("🔙 Back to menu", reply_markup=keyboard)

        return


    if text == "TXT ➜ VCF":

        user_data_store[user_id] = {"step": "contact_name"}

        await update.message.reply_text(
            "Enter Contact Name:",
            reply_markup=ReplyKeyboardMarkup(back_menu, resize_keyboard=True)
        )

        return


    if text == "VCF ➜ TXT":

        user_data_store[user_id] = {"step": "vcf_to_txt"}

        await update.message.reply_text(
            "Send VCF file to extract numbers.",
            reply_markup=ReplyKeyboardMarkup(back_menu, resize_keyboard=True)
        )

        return


    if text == "Numbers ➜ VCF":

        user_data_store[user_id] = {"step": "numbers_vcf_name"}

        await update.message.reply_text(
            "Enter VCF File Name:",
            reply_markup=ReplyKeyboardMarkup(back_menu, resize_keyboard=True)
        )

        return


    if user_id not in user_data_store:
        return


    step = user_data_store[user_id].get("step")


    try:

        if step == "contact_name":

            user_data_store[user_id]["contact_name"] = text
            user_data_store[user_id]["step"] = "vcf_name"

            await update.message.reply_text("Enter VCF File Name:")

            return


        if step == "vcf_name":

            user_data_store[user_id]["vcf_name"] = text
            user_data_store[user_id]["step"] = "contacts_per_file"

            await update.message.reply_text("Contacts per VCF file?")

            return


        if step == "contacts_per_file":

            user_data_store[user_id]["contacts_per_file"] = int(text)
            user_data_store[user_id]["step"] = "file_count"

            await update.message.reply_text("How many VCF files?")

            return


        if step == "file_count":

            user_data_store[user_id]["file_count"] = int(text)
            user_data_store[user_id]["step"] = "upload_txt"

            await update.message.reply_text("Send TXT file with numbers.")

            return


        if step == "numbers_vcf_name":

            user_data_store[user_id]["vcf_name"] = text
            user_data_store[user_id]["step"] = "send_numbers"

            await update.message.reply_text(
                "Send numbers line by line\nExample:\n919999999999"
            )

            return


        if step == "send_numbers":

            numbers = text.split("\n")

            filename = f"{user_id}.vcf"

            with open(filename, "w") as vcf:

                for i, number in enumerate(numbers):

                    number = number.strip()

                    if number == "":
                        continue

                    vcf.write(
                        f"BEGIN:VCARD\nVERSION:3.0\nFN:Contact{i+1}\nTEL;TYPE=CELL:{number}\nEND:VCARD\n"
                    )

            await update.message.reply_document(open(filename, "rb"))

            os.remove(filename)

            await update.message.reply_text("✅ VCF created")

            user_data_store[user_id] = {}

    except:

        await update.message.reply_text("❌ Invalid input")


# TXT FILE HANDLER
async def handle_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_data_store.get(user_id, {}).get("step") != "upload_txt":
        return

    file = await update.message.document.get_file()

    txt_file = f"{user_id}_numbers.txt"

    await file.download_to_drive(txt_file)

    with open(txt_file) as f:
        numbers = f.read().splitlines()

    data = user_data_store[user_id]

    name = data["contact_name"]
    per_file = data["contacts_per_file"]
    count = data["file_count"]
    vcf_name = data["vcf_name"]

    index = 0

    created_files = []


    for i in range(count):

        filename = f"{user_id}_{vcf_name}_{i+1}.vcf"

        with open(filename, "w") as vcf:

            for j in range(per_file):

                if index >= len(numbers):
                    break

                number = numbers[index].strip()

                if number == "":
                    index += 1
                    continue

                vcf.write(
                    f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}{index+1}\nTEL;TYPE=CELL:{number}\nEND:VCARD\n"
                )

                index += 1

        created_files.append(filename)


    zipname = f"{user_id}_vcf_files.zip"

    with zipfile.ZipFile(zipname, "w") as zipf:

        for file in created_files:

            zipf.write(file)

            os.remove(file)


    await update.message.reply_document(open(zipname, "rb"))

    os.remove(zipname)
    os.remove(txt_file)

    user_data_store[user_id] = {}

    await update.message.reply_text("✅ VCF files generated")


# VCF TO TXT FIXED
async def handle_vcf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_data_store.get(user_id, {}).get("step") != "vcf_to_txt":
        return

    file = await update.message.document.get_file()

    vcf_file = f"{user_id}_contacts.vcf"

    await file.download_to_drive(vcf_file)

    numbers = []

    with open(vcf_file, "r", errors="ignore") as f:

        for line in f:

            if line.startswith("TEL"):

                number = line.split(":")[-1].strip()

                numbers.append(number)


    txt_file = f"{user_id}_numbers.txt"

    with open(txt_file, "w") as out:

        for n in numbers:

            out.write(n + "\n")


    await update.message.reply_document(open(txt_file, "rb"))

    os.remove(txt_file)
    os.remove(vcf_file)

    user_data_store[user_id] = {}

    await update.message.reply_text("✅ Numbers extracted successfully")


# MAIN
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