from pyrogram import Client, filters
from transformers import pipeline

# إعدادات البايروجرام
api_id = "21669021"
api_hash = "bcdae25b210b2cbe27c03117328648a2"
session_string = "AgG3g3kApd78GwAqaQWmENs9hVqzk_OtCUnLth_i7HLdoRItCtk1zE8xaHeiYDwZWVO0WfE0sa_56iDP7FVCJ3hLkxI7xk-7lbkbsUCYqPRc71FcFO4S2_szBiUSHDBoVFmxEFMdHGWjQmfiZ6629o15M-K-n-_gNng2rRxOrUg9PzmDN79ueYu3bPU3LSHLSQCZnmq4J36UNBe7cOG-Xpu2U6ZKldNZlPn32BFMraKuNMqh81R2mbF2XcABLzpIPIdOxySXID5GojwqFX3GeSMa4ysN_yRBA_5Pd0DRDba2cMB6cGwONAb1ATaKwsdkAfrAItkVI09ie7YLuWE0TRlIMK-CRwAAAAGiCJ3NAA"  # مكان وضع الجلسة

# إعداد نموذج الذكاء الاصطناعي باستخدام Hugging Face Transformers
chatbot = pipeline("conversational", model="microsoft/DialoGPT-medium")

# إنشاء عميل البايروجرام باستخدام الجلسة المحفوظة
app = Client(session_string, api_id=api_id, api_hash=api_hash)

# دالة للتواصل مع نموذج الذكاء الاصطناعي للحصول على رد ذكي
def get_ai_response(user_input):
    conversation = chatbot(user_input)
    message = conversation[0]["generated_text"]
    return message

# الرد على جميع الرسائل الواردة في المحادثات الخاصة باستخدام الذكاء الاصطناعي
@app.on_message(filters.text & filters.private)
def auto_reply(client, message):
    user = message.from_user
    user_input = message.text
    ai_response = get_ai_response(user_input)
    message.reply_text(f"مرحبًا {user.first_name}! {ai_response}")

# بدء التطبيق
app.run()
