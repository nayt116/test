import config
import bad_words
import filters
import sqlite3

from aiogram import Bot, Dispatcher, executor, types

from filter import IsAdmin

# активируем бота
bot = Bot(token=config.TOKEN)
dp = Dispatcher(bot)

# активируем фильтер
dp.filters_factory.bind(IsAdmin)

# подключаемся с бд
conn = sqlite3.connect("kick_members.db")
cursor = conn.cursor()


# функция которая удаляет сообщение когда новый пользователь присоеденился
# проверяем всех юзеров если их id совпадает в бд то ещёраз кикаем
@dp.message_handler(content_types=['new_chat_members'])
async def join(message: types.Message):
	await message.delete()
	
	tg_user_id = await message.bot.get_chat_member(message.chat.id, message.from_user.id)

	# достаем user_id из бд 
	bd_user_id = cursor.execute(" SELECT `user_id` FROM `members` WHERE `user_id` = ?", (tg_user_id,))

	# если id совпадают то кикаем этого пользователя
	if bd_user_id == tg_user_id:
		await message.bot.delete_message( chat_id = config.GROUP_ID, message.message_id )
		await message.bot.kick_chat_member( chat_id = config.GROUP_ID, user_id = message.from_user.id )


# функция которая удаляет плохие сообщения
@dp.message_handler()
async def filters_messages(message: types.Message):
	try:
		for words in bad_words:
			if words in message.text:
				await message.delete()
	except Exception as er:
		print(er)
		print('[Error]:FileWordsError in line >> 43.')


# функция бан
@dp.message_handler(is_admin=True, commands=['ban'], commands_prefix='!/')
async def ban(message: types.Message):
	if not message.reply_to_message:
		await message.reply("Эта команда предназначена для ответа!\nПричина с новой строки...")
		return

	try:
		# удаляем и кикаем пользователя
		await message.bot.delete_message( chat_id = config.GROUP_ID, message.message_id )
		await message.bot.kick_chat_member( chat_id = config.GROUP_ID, user_id = message.reply_to_message.from_user.id )

		# сохраняем данные пользователя в переменные чтобы работать с бд
		user_id = await message.reply_to_message.from_user.id
		name = await message.reply_to_message.from_user
		why = await message.reply_to_message[1:].text

		# сохраняем данные пользователя в бд
		cursor.execute(" INSERT INTO `members` (`user_id`) VALUES (?) ", (user_id,))
		cursor.execute(" INSERT INTO `members` (`name`) VALUES (?) ", (name,))
		cursor.execute(" INSERT INTO `members` (`why`) VALUES (?) ", (why,))
		conn.commit()

		await message.reply_to_message.reply( 'Пользователь был забанен!' )

	except Exception:
		print("[Error]:Exception in line >>> 60.")

	conn.close()


if __name__=='__main__':
	executor.start_polling( dp, skip_updates=False ) # skip_updates=False чтобы все важные данные не терялись, а сохранялись