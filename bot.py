import vobject
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8418161789:AAGrHMkdjeKBDCawA21eftU-RS0syFcBq40"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📂 Contact Converter Bot\n\n"
        "Send TXT file → get VCF\n"
        "Send VCF file → get TXT"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):

    file = await update.message.document.get_file()
    filename = update.message.document.file_name

    await file.download_to_drive(filename)

    # TXT ➜ VCF
    if filename.endswith(".txt"):

        with open(filename, "r") as f:
            numbers = f.readlines()

        vcf_data = ""

        for i, number in enumerate(numbers):
            number = number.strip()

            vcf_data += f"""BEGIN:VCARD
VERSION:3.0
FN:Contact{i+1}
TEL;TYPE=CELL:{number}
END:VCARD
"""

        with open("contacts.vcf", "w") as f:
            f.write(vcf_data)

        await update.message.reply_document(open("contacts.vcf","rb"))

    # VCF ➜ TXT
    elif filename.endswith(".vcf"):

        numbers = []

        with open(filename) as f:
            for vcard in vobject.readComponents(f):
                numbers.append(vcard.tel.value)

        with open("numbers.txt","w") as f:
            for num in numbers:
                f.write(num + "\n")

        await update.message.reply_document(open("numbers.txt","rb"))

def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    print("Bot is running...")

    app.run_polling()

main()