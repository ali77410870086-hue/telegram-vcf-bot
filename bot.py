import os
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"

# --- START MENU ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["TXT ➜ VCF", "VCF ➜ TXT"],
        ["Numbers ➜ VCF"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "📂 Select an option:", reply_markup=reply_markup
    )

# --- HANDLE MENU ---
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "TXT ➜ VCF":
        context.user_data["mode"] = "txt_to_vcf"
        context.user_data["step"] = "ask_split"
        await update.message.reply_text("How many VCF files do you want?")

    elif text == "VCF ➜ TXT":
        context.user_data["mode"] = "vcf_to_txt"
        await update.message.reply_text("Send VCF file")

    elif text == "Numbers ➜ VCF":
        context.user_data["mode"] = "num_to_vcf"
        await update.message.reply_text("Send numbers (one per line)")

# --- HANDLE NUMBER INPUT ---
async def number_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "ask_split":
        try:
            count = int(update.message.text)
            context.user_data["split_count"] = count
            context.user_data["step"] = "waiting_txt"
            await update.message.reply_text("Now send TXT file with numbers.")
        except:
            await update.message.reply_text("❌ Send valid number")

# --- TXT → MULTIPLE VCF ---
def split_txt_to_vcf(numbers, parts, base_name="Ali"):
    chunk_size = len(numbers) // parts
    files = []

    for i in range(parts):
        start = i * chunk_size
        end = None if i == parts - 1 else (i + 1) * chunk_size
        chunk = numbers[start:end]

        filename = f"{base_name}_{i+1}.vcf"
        with open(filename, "w", encoding="utf-8") as vcf:
            for j, num in enumerate(chunk):
                vcf.write("BEGIN:VCARD\nVERSION:3.0\n")
                vcf.write(f"N:Contact{j}\n")
                vcf.write(f"TEL:{num}\nEND:VCARD\n")

        files.append(filename)

    return files

# --- VCF → TXT ---
def vcf_to_txt(input_file, output_file):
    numbers = []
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("TEL"):
                numbers.append(line.split(":")[1].strip())

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(numbers))

# --- FILE HANDLER ---
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")

    file = await update.message.document.get_file()
    input_path = f"{update.message.chat_id}_input.txt"
    await file.download_to_drive(input_path)

    # --- TXT TO MULTIPLE VCF ---
    if mode == "txt_to_vcf" and context.user_data.get("step") == "waiting_txt":
        with open(input_path, "r") as f:
            numbers = [line.strip() for line in f if line.strip()]

        parts = context.user_data.get("split_count", 1)
        files = split_txt_to_vcf(numbers, parts)

        for fpath in files:
            await update.message.reply_document(InputFile(fpath))
            os.remove(fpath)

    # --- VCF TO TXT ---
    elif mode == "vcf_to_txt":
        output = "output.txt"
        vcf_to_txt(input_path, output)
        await update.message.reply_document(InputFile(output))
        os.remove(output)

    os.remove(input_path)

# --- TEXT HANDLER (Numbers → VCF) ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("mode") == "num_to_vcf":
        numbers = update.message.text.splitlines()
        filename = "numbers.vcf"
        with open(filename, "w", encoding="utf-8") as vcf:
            for i, num in enumerate(numbers):
                vcf.write("BEGIN:VCARD\nVERSION:3.0\n")
                vcf.write(f"N:Contact{i}\n")
                vcf.write(f"TEL:{num}\nEND:VCARD\n")

        await update.message.reply_document(InputFile(filename))
        os.remove(filename)

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d+$'), number_handler))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()