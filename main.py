from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = "8180480897:AAFvjK_DpADaEWPvoHBKRVKUuVEUUqNp1iY"

game = {
    'board': [' '] * 9,
    'player_turn': 'X',
    'players': {},
    'move_mode': False,
    'round': 1,
    'scores': {'X': 0, 'O': 0}
}
MAX_ROUNDS = 3

def get_keyboard():
    keyboard = []
    for i in range(0, 9, 3):
        row = [
            InlineKeyboardButton(game['board'][i + j], callback_data=str(i + j))
            for j in range(3)
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def check_winner():
    b = game['board']
    wins = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
    for i, j, k in wins:
        if b[i] == b[j] == b[k] != ' ':
            return True
    return False

def is_draw():
    return ' ' not in game['board']

def reset_board():
    game['board'] = [' '] * 9
    game['move_mode'] = False
    game['player_turn'] = 'X'

async def end_game(update, winner=None):
    if winner:
        game['scores'][winner] += 1
        await update.edit_message_text(
            f"🏆 الجولة {game['round']} انتهت! الفائز: {winner}\n\n"
            f"النتيجة:\nX: {game['scores']['X']} | O: {game['scores']['O']}",
            reply_markup=get_keyboard()
        )
    else:
        await update.edit_message_text(
            f"🤝 تعادل في الجولة {game['round']}!\n\n"
            f"النتيجة:\nX: {game['scores']['X']} | O: {game['scores']['O']}",
            reply_markup=get_keyboard()
        )

    game['round'] += 1
    if game['round'] > MAX_ROUNDS:
        final = "🏁 انتهت اللعبة!\n"
        if game['scores']['X'] > game['scores']['O']:
            final += "الفائز النهائي: X 🎉"
        elif game['scores']['O'] > game['scores']['X']:
            final += "الفائز النهائي: O 🎉"
        else:
            final += "اللعبة انتهت بتعادل 🔁"
        await update.message.reply_text(final)
        game['round'] = 1
        game['scores'] = {'X': 0, 'O': 0}
        game['players'] = {}

    reset_board()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset_board()
    game['players'] = {}
    await update.message.reply_text("لعبة XO بدأت! اللاعب X يبدأ:", reply_markup=get_keyboard())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data)
    user = query.from_user.id
    board = game['board']

    if game['player_turn'] not in game['players'].values():
        if user not in game['players']:
            game['players'][user] = game['player_turn']

    symbol = game['players'].get(user)
    if symbol != game['player_turn']:
        await query.reply_text("ليس دورك!")
        return

    if not game['move_mode']:
        if board[idx] == ' ':
            board[idx] = game['player_turn']
        else:
            await query.reply_text("الخانة مشغولة!")
            return
    else:
        if board[idx] == game['player_turn']:
            context.user_data['move_from'] = idx
            await query.edit_message_text("اختر الخانة الجديدة لنقل الحجر.", reply_markup=get_keyboard())
            return
        elif 'move_from' in context.user_data and board[idx] == ' ':
            board[context.user_data['move_from']] = ' '
            board[idx] = game['player_turn']
            del context.user_data['move_from']
        else:
            await query.reply_text("اختر حجرك أولاً ثم خانة فارغة.")
            return

    if check_winner():
        await end_game(query, winner=game['player_turn'])
        return

    if is_draw() and not game['move_mode']:
        game['move_mode'] = True
        await query.edit_message_text("تعادل! يمكن الآن تحريك الحجارة.", reply_markup=get_keyboard())
        return

    game['player_turn'] = 'O' if game['player_turn'] == 'X' else 'X'
    await query.edit_message_text(f"دور اللاعب {game['player_turn']}", reply_markup=get_keyboard())

if __name__ == '__main__':
    from telegram.ext import ApplicationBuilder
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
