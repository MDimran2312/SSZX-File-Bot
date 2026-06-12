import logging
import os
import uuid
import gspread
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

# এনভায়রনমেন্ট লোড করা
load_dotenv()

# Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
SHEET_NAME = os.getenv("SHEET_NAME")

# --- Google Sheets Setup (Updated) ---
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']

creds_dict = {
    "type": "service_account",
    "project_id": "cool-beanbag-499205-a4",
    "private_key_id": "99dd1db3a2773bc3ac7a2e2ff7d049a14a6413c0",
    "private_key": "-----BEGIN PRIVATE KEY-----\n" + 
                   "MIIEvwIBADANBgkqhkiG9w0BAQEFAASCBKkwggSlAgEAAoIBAQC3xZoSqJEgERI/\n" +
                   "5hE5/GIyrGv7jPNA+yim0R5bEGcuEvhhoIvWr6gsQ6vdW/Ayd/ry/rYfUUAOyPYP\n" +
                   "jngye3jR4KesWQVbixj3hpqIHc3qk6izve8ke5Xrat8lGUlfwtbTRINcCIpJsjCa\n" +
                   "mWctGH2JhzQRxI2lTqcm3GIyYU3J5p66Kwu0zxNKozq67Ewd0n3NbQ+ztausyOZ2\n" +
                   "TMabdevAzPDvgrDEVdLErX/hma9mLtL2uZHfat8ZKG4DtnzF8YJaW9PNrBRA8mOj\n" +
                   "3WT5lqOM0h8EWLO8O0ZTVkYd2vMpGuNoH/GBEYZ6NJwv4GAF5G0D3hsymIZyg77v\n" +
                   "4lmRQfLNAgMBAAECggEABMh4GuG3y0Oee7rHeoCi5qo9skGoKCoRVAwv09NwuA6G\n" +
                   "1/Wnhhoy0JofTEbjENE2HyJ5h4WkGu5olx2Qa9HyYlYMTyxO+yO67eBbP800yZT3\n" +
                   "yFvacFLmI0c4ER1gH0WxNTT8jUXsoX/pi3CQMqiHRe/Wr1q0DBgouhZ02NZXAbj7\n" +
                   "Wl1BYMcK6RYl68cdozL0LzCCEubodWjmfMWrHUJAhJXEEM15Y3WMDpduxYd5a2Jd\n" +
                   "X9Qzt3xHcQpvyxSwPpGCrry1wMrlk3o8fZQcwn+/q4zFtonoA1ARmttR5MqxaAbc\n" +
                   "LicvpcsftwAf7GSFldhtacxD/EpdlHfuNg6gbnq6MQKBgQDnueDZgvTVKnQ0QYWG\n" +
                   "ZLpO33yMuEGdKSOq41vz27T15L85NIhsvWYfP75CP52iBUqdJ1xt/j3YAW6FtijH\n" +
                   "UZbFfONSzxJqvi1Ua4Oulo8nC236KGAL6Khcbh6xmvleemtF+iVxk2u59T6M7NEQ\n" +
                   "d25C5u34DzMpQV2TTf3vSPxbXQKBgQDLBcBivaodFq6q76jSDrOllYz3+8szDHcP\n" +
                   "kxFB+D3caGlRvYXjFcQ2hNLSLkXmTcBDvQrjnfC+Z9mZbtYvu03n3RL5zx1gqmG1\n" +
                   "/MpfSS00zBCfR0LTPe5mb5pLqvoqDfwWZIGG8pjaa7JY37b0QJr4cKf7IiSC2YAd\n" +
                   "5uDtb9TuMQKBgQC3ALAXd3m9wzpkbn5yBaixU4Q8aeO/p1a4xbe/3XqLWyy9k8RO\n" +
                   "BEHbWe76yNzHsOAdPpGbeFcE+RR82sBXsRKeQqQQqOJFlI2eBw7G2baSQk+HaU14\n" +
                   "+jPEU19AKkDYIVwItqXNjXxdLtZIW1o8Y+WbRl8XMYHZCftJsyVhTUWnLQKBgQCB\n" +
                   "Nqzma05M6zXKB3SMFN1TouYwoqoGWIWifPi74vIESNPXOWdwS1cxV8ISEW9dj9ix\n" +
                   "hCzdB5XEqbX9iGR7xptj2fmM0rwg3PAJctWeZaWG9+YQabtnVQBZY+hxBmXnxDTQ\n" +
                   "T7F8oQSV53uAQwpfVIsNWi4fkPBp82IuJda8Z7O+0QKBgQDZHwxUqm81Bl9yZ2cV\n" +
                   "kwsI/zhd9ydjzn/iYAbX5qLjxuheO35F/CvPFgdixll0F3jLUXkLf9B6O8YRsbeW\n" +
                   "nd7xFe12Nw8dsFdgW/5uspkxcNZCz6m49haY+sIrcNI3JFzNw4zLFRaqARUcXOC1\n" +
                   "ofwyY/qy80zFsqRqHd6zvzfQUQ==\n-----END PRIVATE KEY-----",
    "client_email": "sszx-file-bot@cool-beanbag-499205-a4.iam.gserviceaccount.com",
    "client_id": "118306384012241479853",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sszx-file-bot%40cool-beanbag-499205-a4.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# বট ইনিশিয়ালাইজেশন
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ফাইল সাইজ লিমিট (১০ এমবি)
MAX_FILE_SIZE = 10 * 1024 * 1024 

class OrderState(StatesGroup):
    waiting_for_file = State()
    waiting_for_payment_method = State()
    waiting_for_payment_number = State()

# --- Keyboards (আপনার সব কিবোর্ড ঠিক আছে) ---
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Instagram", callback_data="insta_menu")]])

def get_insta_submenu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Instagram 2FA Account", callback_data="type_2fa")],
        [InlineKeyboardButton(text="Instagram Cookies Account", callback_data="type_cookies")]
    ])

def get_submit_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Submit", callback_data="ready_to_upload")]])

def get_payment_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Bkash", callback_data="pay_bkash"), InlineKeyboardButton(text="Nagad", callback_data="pay_nagad")],
        [InlineKeyboardButton(text="Rocket", callback_data="pay_rocket"), InlineKeyboardButton(text="Binance", callback_data="pay_binance")]
    ])

# --- Logic (আপনার আগের সব লজিক অটুট) ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Welcome to Secure Surf Zone X. Please verify your membership.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Join Channel 1", url="https://t.me/yourchannel1")],
            [InlineKeyboardButton(text="Join Channel 2", url="https://t.me/yourchannel2")],
            [InlineKeyboardButton(text="Verify Join", callback_data="verified")]
        ]))

@dp.callback_query(F.data == "verified")
async def process_verify(callback: types.CallbackQuery):
    await callback.message.edit_text("Verified! Select Service:", reply_markup=get_main_menu())

@dp.callback_query(F.data == "insta_menu")
async def insta_menu(callback: types.CallbackQuery):
    await callback.message.edit_text("Select Account Type:", reply_markup=get_insta_submenu())

@dp.callback_query(F.data.startswith("type_"))
async def select_type(callback: types.CallbackQuery, state: FSMContext):
    service_type = callback.data.replace('type_', '').upper()
    await state.update_data(service=service_type)
    await callback.message.edit_text(f"Selected: {service_type}\nClick Submit to upload your file.", reply_markup=get_submit_kb())

@dp.callback_query(F.data == "ready_to_upload")
async def ready_to_upload(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Now, please send your file (Document only).")
    await state.set_state(OrderState.waiting_for_file)

@dp.message(OrderState.waiting_for_file, F.document)
async def handle_file(message: types.Message, state: FSMContext):
    if message.document.file_size > MAX_FILE_SIZE:
        await message.answer("Error: File is too large! Max 10MB.")
        return

    token = str(uuid.uuid4())[:8].upper()
    await state.update_data(token=token, file_id=message.document.file_id, 
                            file_name=message.document.file_name, 
                            username=message.from_user.username, user_id=message.from_user.id)
    
    await message.answer(f"File '{message.document.file_name}' received! Token: {token}.\nNow select your payment method.", reply_markup=get_payment_kb())
    await state.set_state(OrderState.waiting_for_payment_method)

@dp.callback_query(OrderState.waiting_for_payment_method, F.data.startswith("pay_"))
async def process_payment(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(pay_method=callback.data.replace('pay_', ''))
    await callback.message.edit_text("Success! Please send your payment number.")
    await state.set_state(OrderState.waiting_for_payment_number)

@dp.message(OrderState.waiting_for_payment_number)
async def finalize_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    payment_number = message.text
    try:
        row = [data['token'], data.get('username', 'None'), str(data['user_id']), str(datetime.now()), data['service'], data['pay_method'], payment_number, data['file_name'], data['file_id'], "Pending"]
        sheet.append_row(row)
        
        admin_text = (f"✅ New Order!\nToken: {data['token']}\nType: {data['service']}\n"
                      f"User: @{data.get('username', 'None')}\nPayment Number: {payment_number}\nFile: {data['file_name']}")
        await bot.send_document(ADMIN_ID, data['file_id'], caption=admin_text)
        await message.answer("Submission Successful! Your request is under review.")
    except Exception as e:
        await message.answer(f"Error saving data: {e}")
    await state.clear()

# --- Admin Panel (সব কমান্ড ঠিক আছে) ---
@dp.message(Command("get_data"))
async def export_data(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        records = sheet.get_all_records()
        root = ET.Element("SecureSurfZoneX_Data")
        for record in records:
            order = ET.SubElement(root, "Order")
            for k, v in record.items():
                child = ET.SubElement(order, str(k).replace(" ", "_"))
                child.text = str(v)
        tree = ET.ElementTree(root)
        tree.write("orders.xml", encoding="utf-8", xml_declaration=True)
        await message.answer_document(FSInputFile("orders.xml"))

@dp.message(Command("done"))
async def mark_done(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            token = message.text.split(" ")[1].upper()
            cell = sheet.find(token)
            sheet.update_cell(cell.row, 10, "Success")
            user_id = sheet.cell(cell.row, 3).value
            await bot.send_message(user_id, f"✅ আপনার পেমেন্ট সাকসেসফুল হয়েছে! টোকেন: {token}")
            await message.answer(f"Token {token} marked Success!")
        except Exception as e:
            await message.answer("Token not found or error occurred.")

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/broadcast ", "")
        users = set(sheet.col_values(3)[1:])
        for user_id in users:
            try: await bot.send_message(user_id, text)
            except: continue
        await message.answer("Broadcast sent.")

@dp.message(Command("search"))
async def search_order(message: types.Message):
    try:
        token = message.text.split(" ")[1].upper()
        cell = sheet.find(token)
        row = sheet.row_values(cell.row)
        await message.answer(f"Token: {row[0]}\nStatus: {row[9]}\nFile: {row[7]}\nUser: @{row[1]}\nPayment Number: {row[6]}")
    except:
        await message.answer("Token not found!")

if __name__ == "__main__":
    dp.run_polling(bot)
