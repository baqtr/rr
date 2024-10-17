import os
import threading
import requests
from ssl import CERT_NONE
from gzip import decompress
from random import choice, choices
from concurrent.futures import ThreadPoolExecutor
from json import dumps
import telebot
from websocket import create_connection


failed = 0
success = 0
retry = 0
accounts = []
lock = threading.Lock()  


token = '7302034329:AAGzCfFZzHNIIhtOxe2yBCek0hZI0Wpf5Oo'
bot = telebot.TeleBot(token)
ID = '6365543397'

def work(mes):
    global failed, success, retry, accounts
    username = choice("qwertyuioasdfghjklzxcvbnpm1234567890") + "".join(
        choices(list("qwertyuioasdfghjklzxcvbnpm1234567890"), k=12)
    )
    try:
        con = create_connection(
            "wss://51.79.208.190:8080/Reg",
            header=[
                "app: com.safeum.android",
                "host: None",
                "remoteIp: 51.79.208.190",
                "remotePort: 8080",
                "sessionId: None",
                "time: 2024-04-11 11:00:00",
                "url: wss://51.79.208.190:8080/Reg",
            ],
            sslopt={"cert_reqs": CERT_NONE},
        )
        con.send(dumps({
            "action": "Register",
            "subaction": "Desktop",
            "locale": "ar_IQ",
            "gmt": "+03",
            "password": {
                "m1x": "75097785def8dfddb7a5afeaa0f4076d01917475d8724483fd1f276bd8ae4797",
                "m1y": "b66f4d55d281ac11bd68f5842788ced1757873dc7bdd1ac5b00bddbde8ede16a",
                "m2": "ffec1e2d77f3a09b860bf038bbebae3fadd5b796acc99394ca668237542cb2ff",
                "iv": "c052e647fe61d0ab5d56439da8b1118c",
                "message": "426eb53ca91516a7a0569f711e0433b9728a03043fc93488fb860bfb7446699a027452b528f9e1efc146fbb2036ef6d303095426cd212c74d58f4dc0fc6274759a45a2b8d4fc9ca4c01cd22b0da41e16"
            },
            "magicword": {
                "m1x": "aa0f2593c97af160b35a14c9ec9cd48b2115b3ae16c53eda021baf24d18f08c8",
                "m1y": "cbeb17605d8d9f6637ffd311a4e89e4d98f0ec003b90dbaa98674c4e93524620",
                "m2": "5e2c8fbe7ed3ac6e371ba3108123dfcc810511f1da5941532f283e4f4651f621",
                "iv": "0d19c58775eb51becd5fc787c8818e38",
                "message": "f975c09d6741a19b2ff76f6acf5591e2"
            },
            "magicwordhint": "0000",
            "login": str(username),
            "devicename": "Realme RMX3269",
            "softwareversion": "1.1.0.1640",
            "nickname": "usueudujdjhd",
            "os": "AND",
            "deviceuid": "f7a88f3e39abf27a",
            "devicepushuid": "*cME2FmjeSj6-869LtFwnwI:APA91bGyMZ_7-tmCzlep7Fz_mWJ9AnTimC83urrBkFMXxTpZhD7Q2xBpUc4DFJIUcKzfzI9H5SqZ0_sY36rc1QJd61kprv7iHSyHtELbuPVTPBbdE75qqs6eTaCoBpmRL_i6RTZEYbFF",
            "osversion": "and_11.0.0",
            "id": "697978842"
        }))

        response = decompress(con.recv()).decode("utf-8")
        if '"status":"Success"' in response:
            with lock:
                success += 1
                accounts.append(username)
                with open('users.txt', 'a') as file:
                    file.write(username + "\n")
                bot.send_message(mes.id, f'<strong> <code>{username}</code> </strong>', parse_mode='html')
        else:
            with lock:
                failed += 1
    except Exception as e:
        print(f"Error: {e}")
        with lock:
            retry += 1



start = ThreadPoolExecutor(max_workers=1000)

def main():
    global success, failed, retry, accounts
    mes = type('obj', (object,), {'id': ID}) 

    while True:
        start.submit(work, mes)
        print(
            f"\n{' ' * 25}Success : {success}\n"
            '\n'
            '\n'
            f"{' ' * 25}Failed : {failed}\n"
            '\n'
            '\n'
            f"{' ' * 25}ReTry : {retry}\n"
        )
        if success >= 2900:
            print("Created Accounts Successfully Sent To Owner Group")
            break

        if success > 0:
            z = "\n".join(accounts)
            print("\n", z)

        os.system("clear")

if __name__ == "__main__":
    main()
