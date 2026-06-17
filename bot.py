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

# ⚠️ আপনার চ্যানেল দুটির ইউজারনেম (@ সহ) অথবা প্রাইভেট আইডি এখানে বসান
CHANNEL_1_ID = "@Cyber_Shield_official" 
CHANNEL_2_ID = "@fegasus_1" 

# Google Sheets Setup
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.getenv("GOOGLE_JSON"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
# নিশ্চিত করুন আপনার গুগল শিটের নাম এখানে "MyDataSheet" দেওয়া আছে
sheet = client.open("mydatasheet").sheet1

# বট ইনিশিয়ালাইজেশন
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ফাইল সাইজ লিমিট (১০ এমবি)
MAX_FILE_SIZE = 10 * 1024 * 1024 

class OrderState(StatesGroup):
    waiting_for_file = State()
    waiting_for_payment_method = State()
    waiting_for_payment_number = State()

# --- Keyboards ---
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

def get_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Get All Data (XML)", callback_data="admin_get_data")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🔍 Search Order", callback_data="admin_search")]
    ])

# --- Logic ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Welcome to Secure Surf Zone X. Please verify your membership.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Join Channel 1", url="https://t.me/Cyber_Shield_official")],
            [InlineKeyboardButton(text="Join Channel 2", url="https://t.me/fegasus_1")],
            [InlineKeyboardButton(text="Verify Join", callback_data="verified")]
        ]))

@dp.callback_query(F.data == "verified")
async def process_verify(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        # উভয় চ্যানেলের মেম্বারশিপ স্ট্যাটাস চেক করা হচ্ছে
        member1 = await bot.get_chat_member(chat_id=CHANNEL_1_ID, user_id=user_id)
        member2 = await bot.get_chat_member(chat_id=CHANNEL_2_ID, user_id=user_id)
        
        # অনুমোদিত স্ট্যাটাসগুলোর তালিকা
        allowed_statuses = ["member", "administrator", "creator"]
        
        if member1.status in allowed_statuses and member2.status in allowed_statuses:
            await callback.message.edit_text("Verified! Select Service:", reply_markup=get_main_menu())
        else:
            await callback.answer("❌ Access Denied! Please join both channels first and try again.", show_alert=True)
            
    except Exception as e:
        # বট যদি চ্যানেলে অ্যাডমিন না থাকে তবে এই এরর আসতে পারে
        await callback.answer("⚠️ Verification Error! Make sure the bot is an Admin in the channels.", show_alert=True)

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

# --- Admin Panel ---

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛡️ **Secure Surf Zone X Admin Panel**", reply_markup=get_admin_kb())
    else:
        await message.answer("Access Denied! You are not an admin.")

@dp.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID: return
    action = callback.data.split("_")[1]
    
    if action == "get_data":
        records = sheet.get_all_records()
        root = ET.Element("SecureSurfZoneX_Data")
        for record in records:
            order = ET.SubElement(root, "Order")
            for k, v in record.items():
                child = ET.SubElement(order, str(k).replace(" ", "_"))
                child.text = str(v)
        file_path = "orders.xml"
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        await callback.message.answer_document(FSInputFile(file_path))
    elif action == "broadcast":
        await callback.message.answer("To broadcast, type: /broadcast your_message")
    elif action == "search":
        await callback.message.answer("To search, type: /search [TOKEN]")

@dp.message(Command("done"))
async def mark_done(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            token = message.text.split(" ")[1].upper()
            cell = sheet.find(token)
            sheet.update_cell(cell.row, 10, "Success")
            user_id = sheet.cell(cell.row, 3).value
            await bot.send_message(user_id, f"✅ Your order has been successful! Token: {token}")
            await message.answer(f"Token {token} marked Success!")
        except: await message.answer("Error processing request.")

@dp.message(Command("broadcast"))
async def broadcast(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        text = message.text.replace("/broadcast ", "")
        users = set(sheet.col_values(3)[1:])
        for user_id in users:
            try: await bot.send_message(user_id, text)
            except: continue
        await message.answer("Broadcast sent successfully.")

@dp.message(Command("search"))
async def search_order(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        try:
            token = message.text.split(" ")[1].upper()
            cell = sheet.find(token)
            row = sheet.row_values(cell.row)
            await message.answer(f"Token: {row[0]}\nStatus: {row[9]}\nFile: {row[7]}\nUser: @{row[1]}\nPayment Number: {row[6]}")
        except: await message.answer("Token not found!")

if __name__ == "__main__":
    dp.run_polling(bot)
