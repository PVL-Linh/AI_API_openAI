import streamlit as st
import json
from fuzzywuzzy import fuzz
import string
import openai
import sqlite3

# Thiết lập thông tin xác thực OpenAI API
openai.api_key = 'MyKey'

# Kết nối tới cơ sở dữ liệu SQLite
conn = sqlite3.connect('chatbot.db')
c = conn.cursor()

# Tạo bảng để lưu các câu hỏi và câu trả lời
c.execute('''CREATE TABLE IF NOT EXISTS chat_logs 
             (sender TEXT, message TEXT)''')

# Đường dẫn tới file JSON chứa dữ liệu huấn luyện
json_file_path = 'data.json'

# Đọc dữ liệu từ file JSON
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

# Hàm xử lý câu hỏi nhập vào và tìm câu trả lời tương ứng
# Hàm xử lý câu hỏi nhập vào và tìm câu trả lời tương ứng
def process_question(question):
    # Loại bỏ dấu câu và chuyển thành chữ thường
    question = question.translate(str.maketrans('', '', string.punctuation)).lower()

    # Tìm câu trả lời dựa trên sự tương đồng với câu hỏi trong dữ liệu có sẵn
    max_similarity = 0
    best_match = None
    for key, value in data.items():
        similarity = fuzz.ratio(question, key.lower())
        if similarity > max_similarity:
            max_similarity = similarity
            best_match = value

    # Nếu độ tương đồng vượt qua ngưỡng, sử dụng OpenAI để trả lời
    if max_similarity < 80:  # Ngưỡng có thể điều chỉnh
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are chatting with a chatbot."},
                {"role": "user", "content": question}
            ]
        )
        best_match = response.choices[0].message['content']

    # Lưu câu hỏi và câu trả lời vào cơ sở dữ liệu
    c.execute("INSERT INTO chat_logs (sender, message) VALUES (?, ?)", ("User", question))
    c.execute("INSERT INTO chat_logs (sender, message) VALUES (?, ?)", ("Chatbot", best_match))
    conn.commit()

    return best_match


# Tiêu đề ứng dụng
st.title('Trò chuyện với Chatbot sử dụng OpenAI và Streamlit')

# Trường nhập câu hỏi mới
new_question = st.text_input('Nhập câu hỏi mới:')

# Nút "Gửi"
if st.button('Gửi') and new_question:
    response = process_question(new_question)
    st.text_input("You:", value=new_question, key='user_input_new', disabled=True)
    st.text_input("Chatbot:", value=response, key='chatbot_response_new', disabled=True)

    # Lưu câu hỏi và câu trả lời vào cơ sở dữ liệu
    c.execute("INSERT INTO chat_logs (sender, message) VALUES (?, ?)", ("User", new_question))
    c.execute("INSERT INTO chat_logs (sender, message) VALUES (?, ?)", ("Chatbot", response))
    conn.commit()

# Lấy lịch sử chat từ cơ sở dữ liệu và sắp xếp ngược lại
query = "SELECT * FROM chat_logs ORDER BY ROWID DESC"
result = c.execute(query).fetchall()

if result:
    for idx, row in enumerate(result):
        sender = row[0]
        message = row[1]
        if sender == 'User':
            st.text_input(f"You {idx}:", value=message, key=f'user_input_{idx}', disabled=True)
        elif sender == 'Chatbot':
            st.text_input(f"Chatbot {idx}:", value=message, key=f'chatbot_response_{idx}', disabled=True)
else:
    st.write('Chưa có dữ liệu.')

# Đóng kết nối với cơ sở dữ liệu khi ứng dụng kết thúc
conn.close()
