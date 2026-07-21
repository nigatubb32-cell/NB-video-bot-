import os
import asyncio
import random
import requests
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import edge_tts

TOKEN = "8936266292:AAHGISbO_RIz6oGlrJOX1t9RZ1z7v_CFqOY"
PEXELS_API_KEY = "Y2RENBYCivCATAYVqllsg12TLyqprsdCK9whYKzAKyGtlkyU9LqwKSsX"

def download_stock_video(keyword, output_path):
    url = f"https://api.pexels.com/videos/search?query={keyword}&per_page=5&orientation=landscape"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            if videos:
                selected_video = random.choice(videos)
                video_files = selected_video.get("video_files", [])
                
                download_url = None
                for vf in video_files:
                    if vf.get("quality") == "hd" or vf.get("height") >= 720:
                        download_url = vf.get("link")
                        break
                if not download_url and video_files:
                    download_url = video_files[0].get("link")
                
                if download_url:
                    v_res = requests.get(download_url, timeout=30)
                    with open(output_path, 'wb') as f:
                        f.write(v_res.content)
                    return True
    except Exception as e:
        print(f"Pexels Error: {e}")
    
    sample_url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
    try:
        res = requests.get(sample_url, timeout=20)
        with open(output_path, 'wb') as f:
            f.write(res.content)
        return True
    except:
        return False

async def text_to_speech(text, output_path):
    communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
    await communicate.save(output_path)

def create_final_video(video_path, audio_path, final_output):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            final_output
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        print(f"FFmpeg Error: {e}")
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ሰላም! እኔ NB Video Bot ነኝ። የፈለጉትን የእንግሊዘኛ ታሪክ ይጻፉልኝ፣ ከጽሑፉ ጋር የሚሄድ ቪዲዮ አዘጋጅቼ እልክልዎታለሁ።")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.message.chat_id
    
    await update.message.reply_text("⏳ ታሪኩን በማንበብና ተስማሚ ቪዲዮ ከ Pexels በመፈለግ ላይ ነኝ... እባክዎ ትንሽ ይጠብቁ...")
    
    video_tmp = f"video_{chat_id}.mp4"
    audio_tmp = f"audio_{chat_id}.mp3"
    output_final = f"final_{chat_id}.mp4"
    
    try:
        await text_to_speech(user_text, audio_tmp)
        
        words = user_text.split()
        search_keyword = words[0] if words else "nature"
        download_stock_video(search_keyword, video_tmp)
        
        if create_final_video(video_tmp, audio_tmp, output_final):
            with open(output_final, 'rb') as video_file:
                await context.bot.send_video(chat_id=chat_id, video=video_file, caption="🎬 ይኸውልዎት የእርስዎ ቪዲዮ ዝግጁ ነው!")
        else:
            await update.message.reply_text("❌ ይቅርታ፣ ቪዲዮውን ማዋሃድ አልተቻለም።")
            
    except Exception as e:
        await update.message.reply_text(f"❌ ስህተት አጋጥሟል: {str(e)}")
        
    finally:
        for f in [video_tmp, audio_tmp, output_final]:
            if os.path.exists(f):
                os.remove(f)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("ቦቱ በትክክል ሥራ ጀምሯል...")
    app.run_polling()

if __name__ == "__main__":
    main()

