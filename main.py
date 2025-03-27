import telebot
from telebot import types
import os

from repository import Repository


bot = telebot.TeleBot("token")
repository = Repository("***","***","***", "***", "***")

blacklist = [***]



@bot.message_handler(commands=["useful_links"])
def f(message):
    bot.send_message(message.chat.id,
    f"<em>Интернет ресурсы:</em>\n"
    f"https://ege.sdamgia.ru - сайт для решения пробных экзаменов\n"
    f"https://gramota.ru — справочно-информационный портал о русском языке\n"
    f"https://skysmart.ru - это сайт на котором можно купить, или бесплатно "
                                     f"попробовать занятия для подготовки к экзаменам\n"
    f"https://uchi.ru - образовательная онлайн-платформа для изучения различных учебных предметов\n"
    f"https://www.yaklass.ru - думаю все и так знают😩\n"
    f"<em>Нейронки:</em>\n"
    f"https://chat.deepseek.com - deepseek\n"
    f"https://chat.qwenlm.ai - qwen\n"
    f"https://giga.chat - giga_chat\n"
    f"https://chat.mistral.ai - le_chat"
                                     f"",parse_mode="html")


@bot.message_handler(commands=["schedule"])
def send_schedule(message):
    try:
        class_name = "10Б"

        schedule_path = repository.get_schedule_path(class_name)

        if not schedule_path or not os.path.exists(schedule_path):
            bot.send_message(
                message.chat.id,
                f"Расписание не найдено."
            )
            return

        with open(schedule_path, 'rb') as photo_file:
            bot.send_photo(
                chat_id=message.chat.id,
                photo=photo_file,
                caption=f"Расписание для класса {class_name}"
            )

    except Exception as e:
        print(f"Ошибка при отправке расписания: {e}")
        bot.send_message(
            message.chat.id,
            "Произошла ошибка при отправке расписания. Попробуйте позже."
        )




@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,
    f"🌟 Добро пожаловать! Этот бот создан для школьников, "
    f"которые хотят делиться своими знаниями "
    f"и получать полезные конспекты от других учащихся.\n"
    f"Загружайте только качественные конспекты, которые помогут "
    f"другим разобраться в сложных темах.\n\n"
    f"<em>Опции:</em>\n"
    f"/subjects - вывести предметы\n"
    f"/useful_links - интернет ресурсы для учебы\n"
    f"/schedule - расписание уроков\n\n"
    f"☎️ По все вопросам писать сюда: @jn_7548",
                     parse_mode="html")



@bot.message_handler(commands=["subjects"])
def starts(message):
    subjects = repository.get_subjects()
    markup = types.InlineKeyboardMarkup()
    for subject in subjects:
        markup.add(types.InlineKeyboardButton(subject[1], callback_data=f'subject_{subject[0]}'))
    bot.send_message(message.chat.id, "<em>Выберите предмет:</em>", reply_markup=markup, parse_mode='html')

    repository.add_user(message.from_user.id)



@bot.callback_query_handler(func=lambda callback: callback.data.startswith('subject_'))
def callback_message(callback):
    subject_id = callback.data.split('_')[-1]
    subject_name, topics = repository.get_topics(subject_id)

    markup = types.InlineKeyboardMarkup()
    for topic in topics:
        markup.add(types.InlineKeyboardButton(topic[1], callback_data=f'topic_{topic[0]}'))

    btn = types.InlineKeyboardButton("➕ Добавить тему", callback_data=f"add_topic_{subject_id}")
    markup.add(btn)

    bot.send_message(callback.message.chat.id, f"<em>Темы по предмету {subject_name[0]}:</em>", reply_markup=markup, parse_mode='html')



@bot.callback_query_handler(func=lambda callback: callback.data.startswith("add_topic_"))
def add_topic_prompt(callback):
    subject_id = callback.data.split('_')[-1]
    if callback.from_user.id in blacklist:
        bot.send_message(callback.message.chat.id, "Вам отказано в доступе")
        return
    msg = bot.send_message(callback.message.chat.id, "Отправьте название новой темы")
    bot.register_next_step_handler(msg, add_topic_to_db, subject_id)



def add_topic_to_db(message, subject_id):
    topic_name = message.text.strip()
    if not topic_name:
        bot.send_message(message.chat.id, "Название темы не может быть пустым 😠 . Попробуйте еще раз.")
        return
    if repository.add_topic_to(topic_name, subject_id):
        bot.send_message(message.chat.id, f"Тема «{topic_name}» успешно добавлена")
    else:
        bot.send_message(message.chat.id, f"Тема «{topic_name}» уже существует")



@bot.callback_query_handler(func=lambda callback: callback.data.startswith('topic_'))
def callback_message(callback):
    topic_id = callback.data.split('_')[-1]

    markup = types.InlineKeyboardMarkup()

    btn1 = types.InlineKeyboardButton("Добавить конспект", callback_data=f"add_foto_{topic_id}")
    btn2 = types.InlineKeyboardButton("Посмотреть конспект", callback_data=f"open_foto_{topic_id}")
    markup.row(btn1, btn2)

    bot.send_message(callback.message.chat.id, f"<em>Выберите действие</em>: ", reply_markup=markup, parse_mode='html')




@bot.callback_query_handler(func=lambda callback: callback.data.startswith("add_foto_"))
def add_state(callback):

    if callback.from_user.id in blacklist:
        bot.send_message(callback.message.chat.id, "Вам отказано в доступе")

    try:
        topic_id = callback.data.split('_')[-1]
        user_id = callback.from_user.id

        repository.begin_photo_recieving(user_id, topic_id)

        markup = types.ReplyKeyboardMarkup(True, True)
        btn = types.KeyboardButton("✅ Завершить отправку")
        markup.add(btn)

        bot.send_message(callback.message.chat.id, "Отправьте фотографии\nНажмите <em><b>Завершить отправку</b></em>, чтобы закончить.",
                         reply_markup=markup, parse_mode='html')

    except Exception as e:
        print(f"Ошибка при обработке: {e}")
        bot.send_message(callback.message.chat.id, f"Произошла ошибка 😭")




@bot.message_handler(content_types=["photo"])
def get_photo(message):
    user_id = message.from_user.id
    try:
        user_data = repository.check_the_user_status(user_id)

        if user_data[2] != "ожидание": 
            bot.send_message(message.chat.id, "Сначала выберите тему для отправки фото. 😠")
            return


        if not message.photo:
            return
        topic_id, abstract_id, _ = user_data

        largest_photo = message.photo[-1]
        file_id = largest_photo.file_id

        if not os.path.exists('chat_bot_abstracts'):
            os.makedirs('chat_bot_abstracts')

        photo_path = os.path.join('chat_bot_abstracts', f"{file_id}.jpg")
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        with open(photo_path, 'wb') as photo_file:
            photo_file.write(downloaded_file)

        repository.save_abstract(abstract_id, photo_path)

    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Произошла ошибка при обработке фото 😭.")



@bot.message_handler(func=lambda message: message.text == "✅ Завершить отправку")
def finish_upload(message):
    user_id = message.from_user.id
    try:

        repository.status_completed(user_id)

        markup = types.ReplyKeyboardRemove()

        bot.send_message(message.chat.id, "✔️ Конспект успешно добавлен! 😘\n"
                                          "В <em><b>меню</b></em> можно вывести предметы",
                         reply_markup=markup, parse_mode = 'html')


    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "Произошла ошибка при завершении загрузки 😱.")



@bot.callback_query_handler(func=lambda callback: callback.data.startswith("open_foto_"))
def open_abstract_from_db(callback):

    try:
        topic_id = callback.data.split('_')[-1]

        repository.cleanup_empty_abstracts()

        abstract_ids = repository.availability_abstracts(topic_id)

        if not abstract_ids:
            bot.send_message(
                chat_id=callback.message.chat.id,
                text="Конспекты для этой темы не найдены"
            )
            return

        for (abstract_id,) in abstract_ids:  
            photo_paths = repository.open_abstract(abstract_id)

            if not photo_paths:
                bot.send_message(
                    chat_id=callback.message.chat.id,
                    text=f"Конспект отсутствует."
                )
                continue


            for (photo_path,) in photo_paths:  
                if photo_path and os.path.exists(photo_path):
                    with open(photo_path, 'rb') as photo_file:
                        bot.send_photo(
                            chat_id=callback.message.chat.id,
                            photo=photo_file,
                        )
                else:
                    print(f"Файл {photo_path} не найден.")
        bot.send_message(
            chat_id=callback.message.chat.id,
            text="Вот все фото конспекта ☝️😘\n"
                 "В <em><b>меню</b></em> можно вывести предметы",
            parse_mode = 'html'
        )
    except Exception as e:
        print(f"Ошибка при отправке фото: {e}")
        bot.send_message(
            chat_id=callback.message.chat.id,
            text="Произошла ошибка при отправке фото 😱. Попробуйте позже"
        )


bot.polling(non_stop=True)
