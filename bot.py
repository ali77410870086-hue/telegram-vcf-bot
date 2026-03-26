import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("TXT ➜ VCF", callback_data="txt_to_vcf"),
            InlineKeyboardButton("VCF ➜ TXT", callback_data="vcf_to_txt"),
        ],
        [
            InlineKeyboardButton("Numbers ➜ VCF", callback_data="num_to_vcf")
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📂 Select an option:", reply_markup=reply_markup
    )

# --- BUTTON HANDLER ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["mode"] = query.data

    if query.data == "txt_to_vcf":
        await query.message.reply_text("📄 Send TXT file")
    elif query.data == "vcf_to_txt":
        await query.message.reply_text("📇 Send VCF file")
    elif query.data == "num_to_vcf":
        await query.message.reply_text("📱 Send numbers (one per line)")

# --- TXT → VCF ---
def txt_to_vcf(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(output_file, "w", encoding="utf-8") as vcf:
        for i, line in enumerate(lines):
            number = line.strip()
            if number:
                vcf.write("BEGIN:VCARD\nVERSION:3.0\n")
                vcf.write(f"N:Contact{i}\n")
                vcf.write(f"TEL:{number}\nEND:VCARD\n")

# --- VCF → TXT ---
def vcf_to_txt(input_file, output_file):
    numbers = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("TEL"):
                numbers.append(line.split(":")[1].strip())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(numbers))

# --- NUMBERS → VCF ---
def numbers_to_vcf(numbers, output_file):
    with open(output_file, "w", encoding="utf-8") as vcf:
        for i, num in enumerate(numbers):
            vcf.write("BEGIN:VCARD\nVERSION:3.0\n")
            vcf.write(f"N:Contact{i}\n")
            vcf.write(f"TEL:{num}\nEND:VCARD\n")

# --- FILE HANDLER ---
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if not mode:
        await update.message.reply_text("⚠️ Please select option first (/start)")
        return

    file = await update.message.document.get_file()
    input_path = f"{update.message.chat_id}_input"
    output_path = f"{update.message.chat_id}_output"

    await file.download_to_drive(input_path)

    if mode == "txt_to_vcf":
        output_path += ".vcf"
        txt_to_vcf(input_path, output_path)

    elif mode == "vcf_to_txt":
        output_path += ".txt"
        vcf_to_txt(input_path, output_path)

    else:
        await update.message.reply_text("❌ Invalid file for this mode")
        return

    await update.message.reply_document(InputFile(output_path))

    os.remove(input_path)
    os.remove(output_path)

# --- TEXT HANDLER (Numbers → VCF) ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    if mode != "num_to_vcf":
        return

    numbers = update.message.text.splitlines()
    output_path = f"{update.message.chat_id}.vcf"

    numbers_to_vcf(numbers, output_path)

    await update.message.reply_document(InputFile(output_path))
    os.remove(output_path)

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()