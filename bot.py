import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8728590289:AAGNcv-CPqJ-17xoyBhscU9mBFhJeZRadG8"
ADMIN_ID = 7447021326
PAYMENT_UID = "1041142293"
PRICE = "1 USDT"

allowed_users = set()

user_steps = {}

menu = [["TXT ➜ VCF","VCF ➜ TXT"],["Numbers ➜ VCF"]]
back = [["Back"]]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.from_user.id

    if user_id not in allowed_users and user_id != ADMIN_ID:

        await update.message.reply_text(
f"""Access Required

Pay {PRICE} to Binance UID:
{PAYMENT_UID}

After payment send:
/pay TXID"""
        )
        return

    await update.message.reply_text(
"Choose option:",
reply_markup=ReplyKeyboardMarkup(menu,resize_keyboard=True)
)


async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):

    txid = " ".join(context.args)

    await context.bot.send_message(
ADMIN_ID,
f"Payment request\nUser: {update.message.from_user.id}\nTXID: {txid}"
)

    await update.message.reply_text("Payment sent for verification.")


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])

    allowed_users.add(uid)

    await context.bot.send_message(uid,"Payment verified. Access granted.")
    await update.message.reply_text("User approved.")


async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    uid = int(context.args[0])

    if uid in allowed_users:
        allowed_users.remove(uid)

    await update.message.reply_text("User removed.")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    text = "\n".join(str(u) for u in allowed_users)

    await update.message.reply_text(text if text else "No users")


async def adminfile(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.from_user.id != ADMIN_ID:
        return

    user_steps[ADMIN_ID]={"step":"name"}

    await update.message.reply_text(
"Enter contact name:",
reply_markup=ReplyKeyboardMarkup(back,resize_keyboard=True)
)


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.message.from_user.id
    text = update.message.text

    if text=="Back":
        user_steps[uid]={}
        await update.message.reply_text(
"Menu",
reply_markup=ReplyKeyboardMarkup(menu,resize_keyboard=True)
)
        return

    if uid not in allowed_users and uid!=ADMIN_ID:
        return

    if uid in user_steps:

        step=user_steps[uid].get("step")

        if step=="name":
            user_steps[uid]["name"]=text
            user_steps[uid]["step"]="vcfname"
            await update.message.reply_text("Enter VCF name")
            return

        if step=="vcfname":
            name=user_steps[uid]["name"]
            filename=text+".vcf"

            with open(filename,"w") as f:

                for i in range(10):

                    f.write(
f"BEGIN:VCARD\nVERSION:3.0\nFN:{name}{i}\nTEL;TYPE=CELL:900000000{i}\nEND:VCARD\n"
)

            await update.message.reply_document(open(filename,"rb"))
            os.remove(filename)

            user_steps[uid]={}                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      

            await update.message.reply_text("Admin VCF created.")


def main():

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("pay",pay))
    app.add_handler(CommandHandler("approve",approve))
    app.add_handler(CommandHandler("remove",remove))
    app.add_handler(CommandHandler("users",users))
    app.add_handler(CommandHandler("adminfile",adminfile))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text_handler))

    print("Bot running")

    app.run_polling()


if __name__=="main":
    main()