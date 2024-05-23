# ----- IMPORTING REQUIRED MODULES ----- #

from telebot import TeleBot
from telebot.types import Message
from telebot import apihelper
import time
from threading import Lock

# Importing the inline keyboard markup and button to create inline button for the job links
from tgbot import jobs_post_inline_kb

# Initialize a lock for synchronization
message_lock = Lock()

def get_unclosed_tag(text: str) -> list:
    tags = ["```", "`", "*", "_"]
    stack = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and not stack:
            i += 2
            continue
        
        if stack:
            is_i_inceremented = False
            current_tag = stack[-1]
            if text.startswith(current_tag, i):
                is_i_inceremented = True
                i += len(current_tag)
                stack.pop()
                continue
        else:
            is_i_inceremented = False
            for tag in tags:
                if text.startswith(tag, i):
                    stack.append(tag)
                    is_i_inceremented = True
                    i += len(tag)
                    break
        if not is_i_inceremented:
            i += 1
    return stack

def is_valid(text: str) -> bool:
    return get_unclosed_tag(text) == []

def fix_markdown(text: str) -> str:
    tags = get_unclosed_tag(text)
    for tag in reversed(tags):
        text += tag
    return (text, tags)

def split_markdown(markdown: str, max_length: int = 4096) -> list:
    chunks = []
    tags = []
    start = 0
    while start < len(markdown):
        end = start + max_length
        if end >= len(markdown):
            chunk = markdown[start:]
            for tag in reversed(tags):
                chunk = tag + chunk
            if not is_valid(chunk):
                (chunk, tags) = fix_markdown(chunk)
            chunks.append(chunk)
            break

        split_pos = markdown.rfind("\n", start, end)
        if split_pos == -1 or split_pos == start:
            split_pos = end

        chunk = markdown[start:split_pos]
        for tag in reversed(tags):
            chunk = tag + chunk

        if not is_valid(chunk):
            (chunk, tags) = fix_markdown(chunk)
        
        chunks.append(chunk)
        start = split_pos

    return chunks

def send_job_posts(posts: list[dict], bot: TeleBot, msg: Message = None, channel_id: str = None) -> None:
    """Loops over the provided job post list and send each post in a separate message.
    
    Parameters
    ----------
    posts : list[dict]
        The list of job posts created by the telegram post creator.
    bot : TeleBot
        The bot instance.
    msg : Message
        The Message Object.
    channel_id : str, optional
        The channel id, by default None.
    """
    
    # Delay in seconds
    delay_between_messages = 1

    # Function to split text into chunks
    def split_text(text, chunk_size):
        return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    # Looping over the posts list and sending each post to the user.
    for post in posts:
        job_details = post["job_details"]

        # Split job details into chunks of maximum length
        job_detail_chunks = split_markdown(job_details)

        # Acquire the lock to ensure synchronous processing of the job listing
        with message_lock:
            # Send each chunk as a separate message
            for index, chunk in enumerate(job_detail_chunks):
                # Attempt to send the message and handle rate-limiting
                try:
                    # Check if current chunk is the last by comparing the index with the length of the list
                    is_last_chunk = (index == len(job_detail_chunks) - 1)
                    if is_last_chunk:
                        # Logic for the last chunk
                        bot.send_message(
                            chat_id=channel_id or msg.chat.id,
                            text=chunk,
                            reply_markup=jobs_post_inline_kb(post["job_link"]),
                            parse_mode="Markdown",
                            disable_web_page_preview=True
                        )
                    else:
                        # Logic for all other chunks
                        bot.send_message(
                            chat_id=channel_id or msg.chat.id,
                            text=chunk,
                            parse_mode="Markdown",
                            disable_web_page_preview=True
                        )
                    time.sleep(delay_between_messages)
                except apihelper.ApiTelegramException as e:
                    if e.error_code == 429:
                        # Extract retry-after time from the exception and wait
                        retry_after = int(e.result_json['parameters']['retry_after'])
                        print(f"Rate limited, sleeping for {retry_after} seconds")
                        time.sleep(retry_after)
                    elif e.error_code == 400:
                        print("Formatting error, skipping message")
                    else:
                        raise e
