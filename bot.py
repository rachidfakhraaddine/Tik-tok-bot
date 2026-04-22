import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import yt_dlp
from flask import Flask
from threading import Thread

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# إعداد Flask لإبقاء الاستضافة تعمل (Web Server)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # استخدام المنفذ الافتراضي 8080 أو المنفذ الذي تحدده المنصة
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# دالة تحميل الفيديو
def download_tiktok(url):
    # خيارات yt-dlp لتحميل أفضل جودة بدون علامة مائية (تعتمد على الموقع)
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': 'video_%(id)s.mp4',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logging.error(f"Error downloading video: {e}")
        return None

# معالج الرسائل
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if 'tiktok.com' in url or 'v.douyin.com' in url:
        sent_message = await update.message.reply_text("⏳ جاري التحميل... يرجى الانتظار")
        
        # تحميل الفيديو في خيط منفصل لتجنب حظر البوت
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, download_tiktok, url)
        
        if file_path and os.path.exists(file_path):
            try:
                await update.message.reply_video(video=open(file_path, 'rb'), caption="تم التحميل بواسطة بوتك الخاص ✅")
                await sent_message.delete()
            except Exception as e:
                await sent_message.edit_text(f"❌ حدث خطأ أثناء إرسال الفيديو: {e}")
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            await sent_message.edit_text("❌ عذراً، فشل تحميل الفيديو. تأكد من أن الرابط صحيح أو أن الفيديو متاح.")
    else:
        await update.message.reply_text("الرجاء إرسال رابط تيك توك صحيح.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل لي رابط تيك توك وسأقوم بتحميله لك.")

if __name__ == '__main__':
    # تشغيل Flask في خيط منفصل
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

    # الحصول على التوكن من متغيرات البيئة
    TOKEN = os.environ.get('TELEGRAM_TOKEN')
    
    if not TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not set.")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        
        application.add_handler(start_handler)
        application.add_handler(msg_handler)
        
        print("Bot is starting...")
        application.run_polling()
