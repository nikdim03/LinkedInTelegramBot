# ----- IMPORTING REQUIRED MODULES ----- #

# Importing re for regex.
import re

# Importing telegram bot API.
from telebot import TeleBot, util

# Importing telegram API Message object.
from telebot.types import Message

# Importing jobs factory function to create scrap jobs => create job posts.
from job_posts.job_post_factory import jobs_factory

# Importing job posts sender function to loop over created job data and send each with inline keyboard.
from job_posts.job_post_sender import send_job_posts


# ----- DEFINING INTERFACES  ----- #


# Command Functions Protocol
def command_name(msg: Message, bot: TeleBot) -> None:
    """Implement command."""
    pass


# ----- HELPER FUNCTIONS ----- #


def param_validator(parameter: str) -> bool:
    """_summary_ : This function takes in the job command parameter and validates it.

    Parameters
    ----------
    parameter : str
        _description_ : The parameter extracted from the message.

    Returns
    -------
    bool
        _description_ : True if is valid, False it not.
    """
    # Compiling the command valid pattern.
    pattern = re.compile(r"\D+,\D+")

    # lowering the param case and removing spaces.
    params = parameter.lower().replace(" ", "")

    # Checking if passed parameters is valid of not, and returning the result as a bool True | False.
    return bool(re.search(pattern, params))


# ----- JOBS COMMANDS ----- #


def ljobs(msg: Message, bot: TeleBot) -> None:
    """This function handles the '/ljobs' command."""

    # Send a waiting message to the user.
    wait_message = bot.reply_to(msg, "Please wait while we gather the latest vacancies for you⏳...")

    try:
        # If search parameters were provided:
        if search_params := util.extract_arguments(msg.text).strip():
            # Strip space for the string if any and check parameters format.
            if not param_validator(search_params):
                bot.edit_message_text(
                    chat_id=msg.chat.id,
                    message_id=wait_message.message_id,
                    text=f"*{msg.text}* is not a valid search pattern. Please follow this pattern: /ljobs Job Title, Location",
                    parse_mode="markdown"
                )
                return
            # Convert search parameters into a tuple.
            search_params = tuple(search_params.split(","))

            # Pass the new search params to create jobs using the jobs factory function.
            jobs = jobs_factory(search_params)
        else:
            # Create jobs using the jobs factory function without parameters.
            jobs = jobs_factory()

        # Delete the waiting message.
        bot.delete_message(chat_id=msg.chat.id, message_id=wait_message.message_id)

        # Loop over the list of created posts and send each one.
        send_job_posts(posts=jobs, bot=bot, msg=msg)

    except Exception as e:
        # In case scrapping fails or an error occurs, update the waiting message to show an error.
        error_message = f"Something went wrong while fetching the vacancies🙊: {e}"
        try:
            error_message = f"Something went wrong while fetching the vacancies🙊: {e}"
            bot.edit_message_text(
                chat_id=msg.chat.id,
                message_id=wait_message.message_id,
                text=error_message
            )
        except Exception:
            error_message = f"Something went wrong while posting the vacancies🙊: {e}"
            bot.send_message(
                chat_id=msg.chat.id,
                text=error_message,
            )
