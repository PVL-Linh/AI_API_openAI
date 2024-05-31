import streamlit as st
import csv
import json
import openai
from fuzzywuzzy import fuzz
import os

# Đường dẫn tới tệp CSV và tệp JSON
csv_file_path = 'chat_history.csv'
json_file_path = 'data.json'
api_key_file_path = 'API.txt'

# Đọc dữ liệu từ file JSON
with open(json_file_path, 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Đọc khóa API từ tệp
def read_api_key(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

# Thiết lập thông tin xác thực OpenAI API từ tệp
openai.api_key = read_api_key(api_key_file_path)

# Hàm kiểm tra độ đúng của câu hỏi dựa trên dữ liệu từ file JSON
def check_question(question):
    max_similarity = 0
    best_match = None
    for key, value in json_data.items():
        similarity = fuzz.ratio(question, key.lower())
        if similarity > max_similarity:
            max_similarity = similarity
            best_match = value
    return best_match if max_similarity > 60 else None

# Hàm xử lý câu hỏi nhập vào và trả về câu trả lời
def process_question(question):
    # Kiểm tra độ đúng của câu hỏi dựa trên dữ liệu từ file JSON
    json_response = check_question(question)
    if json_response:
        return json_response

    # Gửi câu hỏi đến OpenAI để nhận câu trả lời
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are chatting with a chatbot."},
            {"role": "user", "content": question}
        ]
    )

    # Kiểm tra xem có phản hồi từ OpenAI không
    if response and response.choices:
        return response.choices[0].message['content'].strip()
    else:
        return "Xin lỗi, không thể xử lý yêu cầu của bạn vào lúc này."


# Tiêu đề ứng dụng
st.title('Trò chuyện với Chatbot sử dụng OpenAI và Streamlit')

# Trường nhập câu hỏi mới
new_question = st.text_input('Nhập câu hỏi mới:')

# Nút "Gửi"
if st.button('Gửi') and new_question:
    # Gửi câu hỏi mới và nhận câu trả lời từ chatbot
    response = process_question(new_question)

    # Lưu lịch sử chat vào tệp CSV
    with open(csv_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["User", new_question])
        csv_writer.writerow(["Chatbot", response])

# Hiển thị lịch sử chat từ tệp CSV
if os.path.exists(csv_file_path):
    st.markdown('### Lịch sử chat:')
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.reader(csvfile)
        # Đọc tất cả các dòng vào danh sách và đảo ngược thứ tự
        chat_history = list(csv_reader)[::-1]
        for idx, row in enumerate(chat_history):
            if len(row) == 2:  # Kiểm tra xem dòng có đủ 2 giá trị không
                sender, message = row
                if sender == "User":
                    st.text(f"You :\n{message}")

                elif sender == "Chatbot":
                    st.text(f"Chatbot :\n{message}")
            else:
                st.write('')
            # Tạo một thẻ div để xuống dòng sau mỗi 100 từ
            if len(message.split()) % 100 == 0:
                st.write('')
