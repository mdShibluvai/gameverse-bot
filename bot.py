import logging,random,sqlite3
from datetime import datetime
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,CallbackQueryHandler,ContextTypes
BOT_TOKEN="8656599791:AAHXX6KhbEe64TELutCxs1OUJZjNvql5a64"
BOT_USERNAME="gameverse_playbot"
logging.basicConfig(level=logging.INFO)
def init_db():
 conn=sqlite3.connect("game.db");c=conn.cursor()
 c.execute("CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY,username TEXT,tokens INTEGER DEFAULT 100,last_daily TEXT DEFAULT '',referrals INTEGER DEFAULT 0,played INTEGER DEFAULT 0,wins INTEGER DEFAULT 0)")
 conn.commit();conn.close()
def get_user(uid):
 conn=sqlite3.connect("game.db");c=conn.cursor()
 c.execute("SELECT * FROM users WHERE user_id=?",(uid,));r=c.fetchone();conn.close();return r
def ensure_user(uid,uname,ref=0):
 if not get_user(uid):
  conn=sqlite3.connect("game.db");c=conn.cursor()
  c.execute("INSERT OR IGNORE INTO users VALUES(?,?,100,'',0,0,0)",(uid,uname))
  if ref and ref!=uid:c.execute("UPDATE users SET tokens=tokens+50,referrals=referrals+1 WHERE user_id=?",(ref,))
  conn.commit();conn.close()
def upd(uid,amt,won=None):
 conn=sqlite3.connect("game.db");c=conn.cursor()
 c.execute("UPDATE users SET tokens=tokens+? WHERE user_id=?",(amt,uid))
 if won is not None:
  c.execute("UPDATE users SET played=played+1 WHERE user_id=?",(uid,))
  if won:c.execute("UPDATE users SET wins=wins+1 WHERE user_id=?",(uid,))
 conn.commit();conn.close()
def main_kb():
 return InlineKeyboardMarkup([[InlineKeyboardButton("Games",callback_data="games")],[InlineKeyboardButton("Wallet",callback_data="wallet"),InlineKeyboardButton("Daily",callback_data="daily")],[InlineKeyboardButton("Leaderboard",callback_data="lb"),InlineKeyboardButton("Referral",callback_data="ref")]])
def game_kb():
 return InlineKeyboardMarkup([[InlineKeyboardButton("Coin Flip",callback_data="g_coin")],[InlineKeyboardButton("Dice Roll",callback_data="g_dice")],[InlineKeyboardButton("Number Guess",callback_data="g_num")],[InlineKeyboardButton("Back",callback_data="main")]])
def bet_kb(g):
 return InlineKeyboardMarkup([[InlineKeyboardButton("10",callback_data=f"b_{g}_10"),InlineKeyboardButton("25",callback_data=f"b_{g}_25"),InlineKeyboardButton("50",callback_data=f"b_{g}_50")],[InlineKeyboardButton("100",callback_data=f"b_{g}_100"),InlineKeyboardButton("Back",callback_data="games")]])
def back_kb():
 return InlineKeyboardMarkup([[InlineKeyboardButton("Back",callback_data="main")]])
async def start(u:Update,c):
 uid=u.effective_user.id;uname=u.effective_user.first_name
 ref=int(c.args[0]) if c.args else 0
 ensure_user(uid,uname,ref)
 await u.message.reply_text(f"GameVerse Bot e swagotom {uname}! 100 Tokens peyecho!",reply_markup=main_kb())
async def btn(u:Update,c):
 q=u.callback_query;await q.answer()
 uid=q.from_user.id;uname=q.from_user.first_name
 ensure_user(uid,uname);d=q.data;row=get_user(uid)
 if d=="main":await q.edit_message_text("GameVerse Menu",reply_markup=main_kb())
 elif d=="games":await q.edit_message_text("Game beche nao:",reply_markup=game_kb())
 elif d=="wallet":
  t=row[2];p=row[5];w=row[6];wr=round(w/p*100,1) if p else 0
  await q.edit_message_text(f"Wallet\nTokens: {t}\nPlayed: {p}\nWins: {w}\nWinRate: {wr}%\nReferrals: {row[4]}",reply_markup=back_kb())
 elif d=="daily":
  today=datetime.now().strftime("%Y-%m-%d")
  if row[3]==today:await q.edit_message_text("Aaj er reward niyecho! Kal esho.",reply_markup=back_kb())
  else:
   r=random.randint(20,100);conn=sqlite3.connect("game.db");c2=conn.cursor()
   c2.execute("UPDATE users SET tokens=tokens+?,last_daily=? WHERE user_id=?",(r,today,uid));conn.commit();conn.close()
   await q.edit_message_text(f"Daily Reward! +{r} Tokens! Ekhon: {row[2]+r}",reply_markup=back_kb())
 elif d=="lb":
  conn=sqlite3.connect("game.db");c2=conn.cursor()
  c2.execute("SELECT username,tokens,wins FROM users ORDER BY tokens DESC LIMIT 10");rows=c2.fetchall();conn.close()
  m="Leaderboard\n"
  for i,(n,t,w) in enumerate(rows):m+=f"{i+1}. {n} - {t} ({w}wins)\n"
  await q.edit_message_text(m,reply_markup=back_kb())
 elif d=="ref":
  link=f"https://t.me/{BOT_USERNAME}?start={uid}"
  await q.edit_message_text(f"Referral\nBondhu invite koro 50 Tokens pao!\nLink: {link}\nReferrals: {row[4]}",reply_markup=back_kb())
 elif d in("g_coin","g_dice","g_num"):
  names={"g_coin":"Coin Flip","g_dice":"Dice Roll","g_num":"Number Guess"}
  await q.edit_message_text(f"{names[d]}\nKot Token bet korbe?",reply_markup=bet_kb(d[2:]))
 elif d.startswith("b_"):
  parts=d.split("_");g=parts[1];bet=int(parts[2]);t=row[2]
  if t<bet:await q.edit_message_text(f"Token kom! Tomar: {t}",reply_markup=back_kb());return
  if g=="coin":
   res=random.choice(["HEADS","TAILS"]);pc=random.choice(["HEADS","TAILS"]);won=res==pc
   rw=bet if won else -bet;upd(uid,rw,won)
   msg=f"Coin Flip\nTomar: {pc}\nResult: {res}\n{'Jitecho' if won else 'Herecho'}! {'+' if won else '-'}{bet}\nEkhon: {t+rw}"
  elif g=="dice":
   res=random.randint(1,6);pc=random.randint(1,6);won=res==pc
   rw=bet*4 if won else -bet;upd(uid,rw,won)
   msg=f"Dice Roll\nTomar: {pc}\nResult: {res}\n{'Jitecho 5x!' if won else 'Herecho'}! {'+' if won else '-'}{abs(rw)}\nEkhon: {t+rw}"
  else:
   res=random.randint(1,10);pc=random.randint(1,10);won=res==pc
   rw=bet*7 if won else -bet;upd(uid,rw,won)
   msg=f"Number Guess\nTomar: {pc}\nSecret: {res}\n{'Jitecho 8x!' if won else 'Herecho'}! {'+' if won else '-'}{abs(rw)}\nEkhon: {t+rw}"
  await q.edit_message_text(msg,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Abar khelo",callback_data=f"g_{g}"),InlineKeyboardButton("Menu",callback_data="main")]]))
def main():
 init_db();app=Application.builder().token(BOT_TOKEN).build()
 app.add_handler(CommandHandler("start",start))
 app.add_handler(CallbackQueryHandler(btn))
 print("Bot chalu!")
 app.run_polling()
if __name__=="__main__":main()
