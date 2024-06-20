from pyrogram import Client, filters

# إعدادات البايروجرام
api_id = "21669021"
api_hash = "bcdae25b210b2cbe27c03117328648a2"
session_string = "AgG3g3kApd78GwAqaQWmENs9hVqzk_OtCUnLth_i7HLdoRItCtk1zE8xaHeiYDwZWVO0WfE0sa_56iDP7FVCJ3hLkxI7xk-7lbkbsUCYqPRc71FcFO4S2_szBiUSHDBoVFmxEFMdHGWjQmfiZ6629o15M-K-n-_gNng2rRxOrUg9PzmDN79ueYu3bPU3LSHLSQCZnmq4J36UNBe7cOG-Xpu2U6ZKldNZlPn32BFMraKuNMqh81R2mbF2XcABLzpIPIdOxySXID5GojwqFX3GeSMa4ysN_yRBA_5Pd0DRDba2cMB6cGwONAb1ATaKwsdkAfrAItkVI09ie7YLuWE0TRlIMK-CRwAAAAGiCJ3NAA"  # مكان وضع الجلسة

# إنشاء عميل البايروجرام باستخدام الجلسة المحفوظة
app = Client(session_string, api_id=api_id, api_hash=api_hash)

# ترحيب بالمستخدمين الجدد
@app.on_message(filters.new_chat_members)
def welcome(client, message):
    for member in message.new_chat_members:
        message.reply_text(f"مرحبًا بك {member.mention} في المجموعة!")

# الرد على جميع الرسائل الواردة
@app.on_message(filters.text & filters.private)
def auto_reply(client, message):
    user = message.from_user
    message.reply_text(f"مرحبًا {user.first_name}! شكرًا لرسالتك. كيف يمكنني مساعدتك؟")

# بدء التطبيق
app.run()
