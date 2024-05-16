# ----- IMPORTING REQUIRED MODULES ----- #

# Importing telegram bot api
from telebot import TeleBot
from telebot.types import Message

# Importing the inline keyboard markup and button to create inline button for the job links
from tgbot import jobs_post_inline_kb


def send_job_posts(
    posts: list[dict], bot: TeleBot, msg: Message = None, channel_id: str = None
) -> None:
    """_summary_ : Loops over the provided job post list and send each post in a separate message.

    Parameters
    ----------
    posts : list[dict]
        _description_ : The list of job posts created by the telegram post creator.
    bot : TeleBot
        _description_
    msg : Message
        _description_ : The Message Object
    channel_id : str, optional
        _description_, by default None : The channel id.
    """

    # Function to split text into chunks
    def split_text(text, chunk_size):
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Looping over the posts list and sending each post to the user.
    for post in posts:
        job_details = post["job_details"].rstrip()  # Remove trailing newlines
        job_link = post["job_link"]

        # Split job details into chunks of maximum length
        max_chunk_length = 4096  # Maximum length of a Telegram message
        job_detail_chunks = split_text(job_details, max_chunk_length)

        # Concatenate job link with the last chunk
        if len(job_detail_chunks) > 1:
            job_detail_chunks[-1] += f"\n\n[👆 Click Here To Apply 👆]({job_link})"
        else:
            job_detail_chunks[0] += f"\n\n[👆 Click Here To Apply 👆]({job_link})"

        # Send each chunk as a separate message
        for chunk in job_detail_chunks:
            bot.send_message(
                chat_id=channel_id or msg.chat.id,
                text=chunk,
                parse_mode="Markdown",
                disable_web_page_preview=True  # Prevents link preview
            )
