# -*- coding: utf-8 -*-
import re

from maidchan.constant import Constants

DEFAULT_NICKNAME = "onii-chan"


def process_command(redis_client, recipient_id, query):
    # TODO: Check admin status (for admin-only help menu)
    if query == "subscribe offerings":
        return process_subscribe_offerings(redis_client, recipient_id)
    elif query == "unsubscribe offerings":
        return process_unsubscribe_offerings(redis_client, recipient_id)
    elif query == "update offerings":
        return process_update_offerings(redis_client, recipient_id)
    elif query == "subscribe japanese":
        return process_subscribe_japanese(redis_client, recipient_id)
    elif query == "unsubscribe japanese":
        return process_unsubscribe_japanese(redis_client, recipient_id)
    elif query == "update japanese":
        return process_update_japanese(redis_client, recipient_id)
    elif query == "update name":
        return process_update_name(redis_client, recipient_id)
    elif query == "show profile":
        return process_show_profile(redis_client, recipient_id)
    # query "help" as default query
    return process_help(redis_client, recipient_id)


def process_active_question(redis_client, recipient_id, question_id, query):
    redis_client.set_active_question(recipient_id, -1)  # Set back to default
    if question_id == 1:
        return process_morning_question(redis_client, recipient_id, query)
    elif question_id == 2:
        return process_night_question(redis_client, recipient_id, query)
    elif question_id == 3:
        return process_kanji_level_question(redis_client, recipient_id, query)
    elif question_id == 4:
        return process_update_name_question(redis_client, recipient_id, query)
    return "<3"


def process_help(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    message = "Hello {}, welcome to Maid-chan Help System!\n\n".format(
        user.get("nickname", DEFAULT_NICKNAME)
    )
    message += "You could ask me for these commands:\n"
    for keyword in Constants.RESERVED_KEYWORDS:
        message += "- \"{}\": {}\n".format(
            keyword[0],
            keyword[1]
        )
    message += "And also, time is handled in UTC+9, te-hee~"
    return message


def process_subscribe_offerings(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    if user["offerings_status"] == "subscribed":
        return "You have been subscribed to Maid-chan offerings, {}!".format(
            user.get("nickname", DEFAULT_NICKNAME)
        )
    # Update DB information
    user["offerings_status"] = "subscribed"
    redis_client.set_user(recipient_id, user)
    # Ask for user's preference
    message = "Thanks for subscribing to Maid-chan offerings <3\n"
    redis_client.set_active_question(recipient_id, 1)
    message += Constants.QUESTIONS[1].format(
        user.get("nickname", DEFAULT_NICKNAME)
    )
    return message


def process_unsubscribe_offerings(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    # Update DB information
    user["offerings_status"] = "unsubscribed"
    redis_client.set_user(recipient_id, user)
    # TODO: Remove schedulers
    return "Maid-chan wish she could serve {} in the future :)".format(
        user.get("nickname", DEFAULT_NICKNAME)
    )


def process_update_offerings(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    if user["offerings_status"] != "subscribed":
        return "You need to subscribe first, {}!".format(
            user.get("nickname", DEFAULT_NICKNAME)
        )
    # Ask for user's preference
    redis_client.set_active_question(recipient_id, 1)
    return Constants.QUESTIONS[1].format(
        user.get("nickname", DEFAULT_NICKNAME)
    )


def process_subscribe_japanese(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    if user["japanese_status"] == "subscribed":
        return "You have been subscribed to Japanese lesson, {}!".format(
            user.get("nickname", DEFAULT_NICKNAME)
        )
    # Update DB information
    user["japanese_status"] = "subscribed"
    redis_client.set_user(recipient_id, user)
    # TODO: Update schedulers
    # Ask for user's preference
    message = "Thanks for subscribing to Maid-chan Japanese lessons <3\n"
    redis_client.set_active_question(recipient_id, 3)
    message += Constants.QUESTIONS[3].format(
        user.get("nickname", DEFAULT_NICKNAME)
    )
    return message


def process_unsubscribe_japanese(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    # Update DB information
    user["japanese_status"] = "unsubscribed"
    redis_client.set_user(recipient_id, user)
    # TODO: Remove schedulers
    return "Maid-chan wish she could serve {} in the future :)".format(
        user.get("nickname", DEFAULT_NICKNAME)
    )


def process_update_japanese(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    if user["japanese_status"] != "subscribed":
        return "You need to subscribe first, {}!".format(
            user.get("nickname", DEFAULT_NICKNAME)
        )
    # Ask for user's preference
    redis_client.set_active_question(recipient_id, 3)
    return Constants.QUESTIONS[3].format(
        user.get("nickname", DEFAULT_NICKNAME)
    )


def process_update_name(redis_client, recipient_id):
    redis_client.set_active_question(recipient_id, 4)
    return Constants.QUESTIONS[4]


def process_show_profile(redis_client, recipient_id):
    user = redis_client.get_user(recipient_id)
    message = "Hi, {}!\n\n".format(user.get("nickname", DEFAULT_NICKNAME))
    if not user.get("nickname"):
        message += "Maid-chan haven't learned how to call you properly :'(\n\n"
    message += "Offerings status: {}\n".format(user["offerings_status"])
    if user["offerings_status"] == "subscribed":
        message += "Morning message: around {} UTC+9\n".format(
            user["morning_time"]
        )
        message += "Night message: around {} UTC+9\n".format(
            user["night_time"]
        )
    message += "Japanese status: {}\n".format(user["japanese_status"])
    if user["japanese_status"] == "subscribed":
        message += "Kanji level: {}".format(user["kanji_level"])
    return message


def process_morning_question(redis_client, recipient_id, query):
    user = redis_client.get_user(recipient_id)
    match = re.search(r'^([01]?\d|2[0-3]):([0-5]?\d)$', query)
    if not match:
        user["morning_time"] = "09:00"
        message = "Since I couldn't understand your message, "
        message += "I set your morning time to around 09:00 UTC+9, sorry :(\n"
    else:
        user["morning_time"] = match.group(0)
        message = "Thank you!\n"
    redis_client.set_user(recipient_id, user)
    # TODO: Update schedulers
    # If the next one is "morning_offering" / none
    # Check if the next "night_offering" is closer to this value or not
    # If it is closer, change the type
    redis_client.set_active_question(recipient_id, 2)
    message += Constants.QUESTIONS[2].format(
        user.get("nickname", DEFAULT_NICKNAME)
    )
    return message


def process_night_question(redis_client, recipient_id, query):
    user = redis_client.get_user(recipient_id)
    match = re.search(r'^([01]?\d|2[0-3]):([0-5]?\d)$', query)
    if not match:
        user["night_time"] = "23:00"
        message = "Since I couldn't understand your message, "
        message += "I set your night time to around 23:00 UTC+9, sorry :(\n"
    else:
        user["night_time"] = match.group(0)
        message = "Thank you for answering Maid-chan question!\n"
    redis_client.set_user(recipient_id, user)
    # TODO: Update schedulers
    # If the next one is "night_offering" / none
    # Check the next "morning_offering" is closer to this value or not
    # If it is closer, change the type
    message += "Your information for my offerings has been updated <3"
    return message


def process_kanji_level_question(redis_client, recipient_id, query):
    user = redis_client.get_user(recipient_id)
    match = re.search(r'^N?[1-4]$', query)
    if not match:
        user["kanji_level"] = "N3"
        message = "Since I couldn't understand your message, "
        message += "I set your Kanji level to N3, sorry :("
    else:
        user["kanji_level"] = match.group(0)
        message = "Your information for Kanji level has been updated <3"
    redis_client.set_user(recipient_id, user)
    return message


def process_update_name_question(redis_client, recipient_id, query):
    user = redis_client.get_user(recipient_id)
    # Ensure name is not empty or space-only
    if not query or query.isspace():
        return "That's not a proper name, buu-buu~"
    # Update DB information
    user["nickname"] = query
    redis_client.set_user(recipient_id, user)
    message = "Maid-chan will start calling you {} from now onwards!\n".format(
        user.get("nickname", DEFAULT_NICKNAME)
    )
    message += "よろしくお願いします~"
    return message