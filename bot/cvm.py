from telethon import events
from moviepy import VideoFileClip
import subprocess

from script import client
from util import authorize, log_error, clean_files

@client.on(events.NewMessage(pattern='/cvm'))
async def convert(event):
    if not authorize(event): return

    try:
        reply = await event.get_reply_message()
        async with client.action(event.chat_id, 'record-round'):
            input_path = await reply.download_media()
            output_path = convert_to_video_note(input_path)
        async with client.action(event.chat_id, 'round'):
            await client.send_file(event.chat_id, output_path, video_note=True)
    except:
        await event.reply(f"Unsupported video format, covert the file to .mp4(roecommended) format.")
    finally:
        clean_files(input_path, output_path)

def convert_to_video_note(input_path):
    try:
        fixed_path = f"fixed_{input_path}"

        clip = VideoFileClip(input_path)
        if clip.duration > 60:
            clip = clip.subclip(0, 60)
        width, height = clip.size
        size = min(width, height)
        croped = clip.cropped(x_center=width/2, y_center=height/2, width=size, height=size)
        resized = croped.resized(new_size=(640, 640))
        # Export
        resized.write_videofile(fixed_path, codec='libx264', audio_codec='aac', fps=30, threads=4)
        clip.close()
        resized.close()

        clean_files(input_path)
        fix_video_note(fixed_path, input_path) # over write
        return input_path  # output_path
    except Exception as e:
        log_error(f"Error Converting to video note:\n{e}")

def fix_video_note(input_path, output_path):
    try:
        cmd = ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", "-preset", "fast", "-crf", "23", output_path]
        # Run FFmpeg
        subprocess.run(cmd, check=True)

        # Verify with MoviePy (optional)
        clip = VideoFileClip(output_path)
        clip.close()
    except Exception as e:
        log_error(f"Error ffmpeg:\n{e}")