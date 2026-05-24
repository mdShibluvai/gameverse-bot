import logging,random,sqlite3
from datetime import datetime,date
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CallbackQueryHandler,CommandHandler,ContextTypes

BOT_TOKEN="8656599791:AAHXX6KhbEe64TELutCxs1OUJZjNvql5a64"
BOT_USERNAME="gameverse_playbot"
logging.basicConfig(level=logging.INFO)

def init_db():
    conn=sqlite3.connect("game.db");c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users(uid INTEGER PRIMARY KEY,uname TEXT,tokens INTEGER DEFAULT 100,played INTEGER DEFAULT 0,wins INTEGER DEFAULT 0,last_daily TEXT DEFAULT '',referrals INTEGER DEFAULT 0,referred_by INTEGER DEFAULT 0)")
    conn.commit();conn.close()

def get_user(uid):
    conn=sqlite3.connect("game.db");c=conn.cursor()
    c.execute("SELECT * FROM users WHERE uid=?",(uid,));r=c.fetchone();conn.close();return r

def ensure_user(uid,uname,ref=0):
    if not get_user(uid):
        conn=sqlite3.connect("game.db");c=conn.cursor()
        c.execute("INSERT OR IGNORE INTO users(uid,uname) VALUES(?,?)",(uid,uname))
        if ref and ref!=uid:c.execute("UPDATE users SET tokens=tokens+25 WHERE uid=?",(uid,))
        conn.commit();conn.close()

def upd(uid,amt,won=None):
    conn=sqlite3.connect("game.db");c=conn.cursor()
    if won is True:c.execute("UPDATE users SET tokens=tokens+?,played=played+1,wins=wins+1 WHERE uid=?",(amt,uid))
    elif won is False:c.execute("UPDATE users SET tokens=tokens-?,played=played+1 WHERE uid=?",(amt,uid))
    else:c.execute("UPDATE users SET played=played+1 WHERE uid=?",(uid,))
    conn.commit();conn.close()

def get_tokens(uid):
    r=get_user(uid);return r[2] if r else 100

DEPOSIT_URL="https://willowy-cuchufli-cc0591.netlify.app/"

def main_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎮 Games",callback_data="games")],
        [InlineKeyboardButton("💰 Wallet",callback_data="wallet"),InlineKeyboardButton("🎁 Daily",callback_data="daily")],
        [InlineKeyboardButton("🏆 Leaderboard",callback_data="leaderboard"),InlineKeyboardButton("👥 Referral",callback_data="referral")],
        [InlineKeyboardButton("💳 Deposit / Withdraw",url=DEPOSIT_URL)]
    ])

def games_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🪙 Coin Flip",callback_data="g_coin")],
        [InlineKeyboardButton("🎲 Dice Roll",callback_data="g_dice")],
        [InlineKeyboardButton("🔢 Number Guess",callback_data="g_num")],
        [InlineKeyboardButton("✊ Rock Paper Scissors",callback_data="g_rps")],
        [InlineKeyboardButton("⬅️ Back",callback_data="menu")]
    ])

def bet_kb(g):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("10🪙",callback_data=f"b_{g}_10"),InlineKeyboardButton("25🪙",callback_data=f"b_{g}_25"),
         InlineKeyboardButton("50🪙",callback_data=f"b_{g}_50"),InlineKeyboardButton("100🪙",callback_data=f"b_{g}_100")],
        [InlineKeyboardButton("⬅️ Back",callback_data="games")]
    ])

def again_kb(g):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Abar Khelo",callback_data=f"g_{g}"),InlineKeyboardButton("🏠 Menu",callback_data="menu")]
    ])

def back_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back",callback_data="menu")]])

async def start(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    u=update.effective_user;args=ctx.args
    ref=int(args[0][4:]) if args and args[0].startswith("ref_") else 0
    ensure_user(u.id,u.first_name,ref)
    if ref and ref!=u.id:
        conn=sqlite3.connect("game.db");c=conn.cursor()
        c.execute("UPDATE users SET tokens=tokens+50,referrals=referrals+1 WHERE uid=?",(ref,))
        conn.commit();conn.close()
    t=get_tokens(u.id)
    await update.message.reply_text(
        f"🎮 *GameVerse Bot এ স্বাগতম {u.first_name}!*\n\n🪙 তোমার Tokens: *{t}*\n\nGame বেছে নাও!",
        parse_mode="Markdown",reply_markup=main_kb())

async def cb(update:Update,ctx:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query;await q.answer()
    d=q.data;u=q.from_user
    ensure_user(u.id,u.first_name)
    t=get_tokens(u.id)

    if d=="menu":
        r=get_user(u.id)
        wr=round(r[4]/r[3]*100) if r[3]>0 else 0
        await q.edit_message_text(
            f"🎮 *GameVerse Hub*\n\n🪙 Tokens: *{t}*\n📊 Played: {r[3]} | Wins: {r[4]} | WR: {wr}%",
            parse_mode="Markdown",reply_markup=main_kb())

    elif d=="games":
        await q.edit_message_text(
            "🎮 *Game বেছে নাও:*\n\n🪙 Coin Flip — *2x*\n🎲 Dice Roll — *5x*\n🔢 Number Guess — *8x*\n✊ Rock Paper Scissors — *2x*",
            parse_mode="Markdown",reply_markup=games_kb())

    elif d=="wallet":
        r=get_user(u.id);wr=round(r[4]/r[3]*100) if r[3]>0 else 0
        await q.edit_message_text(
            f"💰 *Wallet*\n\n🪙 Tokens: *{r[2]}*\n🎮 Played: *{r[3]}*\n✅ Wins: *{r[4]}*\n📈 Win Rate: *{wr}%*",
            parse_mode="Markdown",reply_markup=back_kb())

    elif d=="daily":
        today=str(date.today());r=get_user(u.id)
        if r[5]==today:
            await q.edit_message_text("🎁 আজকের Daily নিয়েছ!\n\nকাল আবার এসো! 😊",reply_markup=back_kb())
        else:
            reward=random.randint(20,100)
            conn=sqlite3.connect("game.db");c=conn.cursor()
            c.execute("UPDATE users SET tokens=tokens+?,last_daily=? WHERE uid=?",(reward,today,u.id))
            conn.commit();conn.close()
            await q.edit_message_text(
                f"🎁 *Daily Reward!*\n\n+*{reward} Tokens* 🎉\n🪙 এখন: *{t+reward} Tokens*",
                parse_mode="Markdown",reply_markup=back_kb())

    elif d=="leaderboard":
        conn=sqlite3.connect("game.db");c=conn.cursor()
        c.execute("SELECT uname,tokens FROM users ORDER BY tokens DESC LIMIT 10")
        rows=c.fetchall();conn.close()
        medals=["🥇","🥈","🥉"]
        txt="🏆 *Top Players*\n\n"
        for i,row in enumerate(rows):
            txt+=f"{medals[i] if i<3 else str(i+1)+'.'} {row[0]} — 🪙 {row[1]}\n"
        await q.edit_message_text(txt,parse_mode="Markdown",reply_markup=back_kb())

    elif d=="referral":
        bot=ctx.bot;me=await bot.get_me()
        link=f"https://t.me/{me.username}?start=ref_{u.id}"
        r=get_user(u.id)
        await q.edit_message_text(
            f"👥 *Referral*\n\nতোমার link:\n`{link}`\n\n✅ প্রতি referral: *+50 Tokens*\n🎁 নতুন user: *+25 Tokens*\n\n👥 Referrals: *{r[6]}*",
            parse_mode="Markdown",reply_markup=back_kb())

    # ===== COIN FLIP =====
    elif d=="g_coin":
        await q.edit_message_text("🪙 *Coin Flip — 2x*\n\nBet করো:",parse_mode="Markdown",reply_markup=bet_kb("coin"))
    elif d.startswith("b_coin_"):
        bet=int(d.split("_")[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        await q.edit_message_text(f"🪙 *Coin Flip* — Bet: {bet}🪙\n\nChoice করো:",parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🌕 HEADS",callback_data=f"coin_h_{bet}"),InlineKeyboardButton("🌑 TAILS",callback_data=f"coin_t_{bet}")],
                [InlineKeyboardButton("⬅️ Back",callback_data="g_coin")]]))
    elif d.startswith("coin_"):
        p=d.split("_");choice=p[1];bet=int(p[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        result=random.choice(["h","t"])
        em={"h":"🌕 HEADS","t":"🌑 TAILS"}
        won=choice==result
        if won:upd(u.id,bet,True);txt=f"✅ *জিতেছ!* +{bet} Tokens! 🎉"
        else:upd(u.id,bet,False);txt=f"❌ *হেরেছ!* -{bet} Tokens 😢"
        nt=get_tokens(u.id)
        await q.edit_message_text(
            f"🪙 *Coin Flip Result*\n\nতুমি: {em[choice]}\nResult: {em[result]}\n\n{txt}\n\n🪙 এখন: *{nt}*",
            parse_mode="Markdown",reply_markup=again_kb("coin"))

    # ===== DICE ROLL =====
    elif d=="g_dice":
        await q.edit_message_text("🎲 *Dice Roll — 5x*\n\nBet করো:",parse_mode="Markdown",reply_markup=bet_kb("dice"))
    elif d.startswith("b_dice_"):
        bet=int(d.split("_")[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        de=["⚀","⚁","⚂","⚃","⚄","⚅"]
        y=random.randint(1,6);c2=random.randint(1,6)
        won=y==c2
        if won:gain=bet*5;upd(u.id,gain,True);txt=f"✅ *Match! জিতেছ!* +{gain} Tokens! 🎉"
        else:upd(u.id,bet,False);txt=f"❌ *Match হয়নি!* -{bet} Tokens 😢"
        nt=get_tokens(u.id)
        await q.edit_message_text(
            f"🎲 *Dice Roll Result*\n\nতোমার: {de[y-1]} ({y})\nComputer: {de[c2-1]} ({c2})\n\n{txt}\n\n🪙 এখন: *{nt}*",
            parse_mode="Markdown",reply_markup=again_kb("dice"))

    # ===== NUMBER GUESS =====
    elif d=="g_num":
        await q.edit_message_text("🔢 *Number Guess — 8x*\n\nBet করো:",parse_mode="Markdown",reply_markup=bet_kb("num"))
    elif d.startswith("b_num_"):
        bet=int(d.split("_")[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        rows=[[InlineKeyboardButton(str(i),callback_data=f"num_{i}_{bet}") for i in range(j,j+5)] for j in range(1,11,5)]
        rows.append([InlineKeyboardButton("⬅️ Back",callback_data="g_num")])
        await q.edit_message_text(f"🔢 *Number Guess* — Bet: {bet}🪙\n\n1-10 বেছে নাও:",parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(rows))
    elif d.startswith("num_") and not d.startswith("num_g"):
        p=d.split("_");guess=int(p[1]);bet=int(p[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        secret=random.randint(1,10);won=guess==secret
        if won:gain=bet*8;upd(u.id,gain,True);txt=f"✅ *সঠিক!* +{gain} Tokens! 🎉🎉"
        else:upd(u.id,bet,False);txt=f"❌ *ভুল!* Secret: *{secret}*\n-{bet} Tokens 😢"
        nt=get_tokens(u.id)
        await q.edit_message_text(
            f"🔢 *Number Guess Result*\n\nতোমার guess: *{guess}*\nSecret: *{secret}*\n\n{txt}\n\n🪙 এখন: *{nt}*",
            parse_mode="Markdown",reply_markup=again_kb("num"))

    # ===== ROCK PAPER SCISSORS =====
    elif d=="g_rps":
        await q.edit_message_text("✊ *Rock Paper Scissors — 2x*\n\nBet করো:",parse_mode="Markdown",reply_markup=bet_kb("rps"))
    elif d.startswith("b_rps_"):
        bet=int(d.split("_")[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        await q.edit_message_text(f"✊ *RPS* — Bet: {bet}🪙\n\nChoice করো:",parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✊ Rock",callback_data=f"rps_rock_{bet}"),
                 InlineKeyboardButton("✋ Paper",callback_data=f"rps_paper_{bet}"),
                 InlineKeyboardButton("✌️ Scissors",callback_data=f"rps_scissors_{bet}")],
                [InlineKeyboardButton("⬅️ Back",callback_data="g_rps")]]))
    elif d.startswith("rps_"):
        p=d.split("_");choice=p[1];bet=int(p[2])
        if t<bet:await q.answer("❌ Token কম!",show_alert=True);return
        bot_c=random.choice(["rock","paper","scissors"])
        em={"rock":"✊","paper":"✋","scissors":"✌️"}
        wins_against={"rock":"scissors","paper":"rock","scissors":"paper"}
        if choice==bot_c:
            upd(u.id,0);txt="🤝 *Draw! Token ফেরত!*"
        elif wins_against[choice]==bot_c:
            upd(u.id,bet,True);txt=f"✅ *জিতেছ!* +{bet} Tokens! 🎉"
        else:
            upd(u.id,bet,False);txt=f"❌ *হেরেছ!* -{bet} Tokens 😢"
        nt=get_tokens(u.id)
        await q.edit_message_text(
            f"✊ *Rock Paper Scissors*\n\nতুমি: {em[choice]}\nBot: {em[bot_c]}\n\n{txt}\n\n🪙 এখন: *{nt}*",
            parse_mode="Markdown",reply_markup=again_kb("rps"))

def main():
    init_db()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CallbackQueryHandler(cb))
    print("✅ Bot চালু!")
    app.run_polling()

if __name__=="__main__":
    main()

