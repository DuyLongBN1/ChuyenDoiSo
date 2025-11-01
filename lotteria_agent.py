import streamlit as st
import pandas as pd
import random
import smtplib
from email.message import EmailMessage
from datetime import datetime, time as dt_time, timedelta, date # <-- Đã thêm 'date'
import sqlite3 

# Thư viện Google GenAI
from google import genai
from google.genai import types

# --- 1. THIẾT LẬP CẤU HÌNH VÀ DATA DỮ LIỆU GIẢ LẬP ---

# Cấu hình trang
st.set_page_config(
    page_title="Lotteria AI Agent",
    page_icon="🍔",
    layout="wide"
)

st.title("🍔 Lotteria AI Assistant")
st.subheader("Trợ lý Đặt Bàn & Gợi Ý Món Ăn Tự Động")

# Tải dữ liệu giả lập Menu Lotteria
@st.cache_data
def load_menu_data():
    menu_data = {
        'Món Ăn': ['Gà Sốt Đậu Phộng HSG', 'Burger Tôm Thượng Hạng', 'Cơm Gà Xối Xả', 'Khoai Tây Lắc Phô Mai', 'Kem Sundae Dâu', 'Gà Sốt Phô Mai', 'Burger Bulgogi'],
        'Thể Loại': ['Gà Rán', 'Burger', 'Cơm', 'Đồ Ăn Vặt', 'Tráng Miệng', 'Gà Rán', 'Burger'],
        'Độ Phổ Biến': [9.5, 8.8, 7.5, 9.1, 8.0, 9.3, 8.5],
        'Giá (VND)': [39000, 55000, 45000, 25000, 15000, 42000, 60000],
        'Hương Vị': ['Cay Nhẹ/Sốt', 'Hải Sản', 'Mặn/Ngọt', 'Mặn/Phô Mai', 'Ngọt', 'Phô Mai', 'Thịt Bò/Sốt'],
        'Khuyến Mãi': [True, False, False, True, False, True, False]
    }
    return pd.DataFrame(menu_data)

df_menu = load_menu_data()

# --- 2. THIẾT LẬP GEMINI CHAT & EMAIL (Sử dụng st.secrets) ---

client = None
MODEL_NAME = "gemini-2.5-flash"
SYSTEM_INSTRUCTION = (
    "Bạn là Lotteria AI Assistant, trợ lý ảo chuyên nghiệp, nhiệt tình và thân thiện của chuỗi nhà hàng Lotteria tại Việt Nam. "
    "Nhiệm vụ của bạn là: "
    "1. Trả lời các câu hỏi về menu, giá cả, và chương trình khuyến mãi. "
    "2. Giữ giọng điệu chuyên nghiệp, ngắn gọn và sử dụng biểu tượng cảm xúc Lotteria (🍔🍟) khi thích hợp."
)

# Cấu hình Email mặc định (dùng để giả lập nếu không tìm thấy secrets)
SMTP_CONFIG = {
    "SERVER": "smtp.gmail.com",
    "PORT": 465,
    "EMAIL": "no-reply@lotteria.com.vn",
    "PASSWORD": "FAKE_APP_PASSWORD"
}

try:
    # Lấy API Key từ Streamlit Secrets
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    # Cấu hình Email 
    SMTP_CONFIG["SERVER"] = st.secrets.get("SMTP_SERVER", SMTP_CONFIG["SERVER"])
    SMTP_CONFIG["PORT"] = st.secrets.get("SMTP_PORT", SMTP_CONFIG["PORT"])
    SMTP_CONFIG["EMAIL"] = st.secrets.get("EMAIL_ADDRESS", SMTP_CONFIG["EMAIL"])
    SMTP_CONFIG["PASSWORD"] = st.secrets.get("EMAIL_PASSWORD", SMTP_CONFIG["PASSWORD"])
    
except KeyError as e:
    # Báo lỗi nếu thiếu khóa quan trọng
    st.error(f"Lỗi: Không tìm thấy khóa bí mật {e}. Vui lòng kiểm tra file .streamlit/secrets.toml.")
    if "GEMINI_API_KEY" in str(e):
        st.warning("Chatbot (Tab 3) sẽ không hoạt động nếu không có GEMINI_API_KEY.")
    
except Exception as e:
    st.error(f"Lỗi khởi tạo hệ thống: {e}")
    
# --- 3. ĐỊNH NGHĨA CÁC HÀM XỬ LÝ DATABASE VÀ API ---

# Khởi tạo Database (Chỉ chạy một lần)
@st.cache_resource
def init_db():
    conn = sqlite3.connect('reservations.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id TEXT UNIQUE,
            customer_name TEXT,
            email TEXT,
            phone TEXT,
            branch TEXT,
            time TEXT, 
            num_people INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    return 'reservations.db'

# Hàm lưu thông tin đặt bàn vào DB
def save_reservation(data):
    conn = sqlite3.connect('reservations.db')
    cursor = conn.cursor()
    # data: (reservation_id, user_name, email, phone, branch, full_datetime_str, num_people)
    cursor.execute('''
        INSERT INTO reservations (reservation_id, customer_name, email, phone, branch, time, num_people)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()


def generate_gemini_response(prompt):
    """Gửi prompt đến Gemini và nhận phản hồi."""
    if not client:
        return "Xin lỗi, chức năng Chatbot đang tạm thời không hoạt động do lỗi kết nối Gemini API."
    
    try:
        # Lấy lịch sử chat từ session state
        history = []
        # Bỏ qua tin nhắn chào mừng đầu tiên
        for msg in st.session_state.messages[1:]: 
            # Đảm bảo nội dung là chuỗi để tránh lỗi validation
            content_text = str(msg["content"])
            history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [{"text": content_text}]
            })
        
        # Cấu hình cho Chat Session
        config = {
            "system_instruction": SYSTEM_INSTRUCTION,
            "temperature": 0.6,
        }

        # Khởi tạo một đối tượng Chat (Session) với lịch sử hiện tại
        chat = client.chats.create(
            model=MODEL_NAME,
            history=history[:-1] if history else [], 
            config=config
        )

        # Gửi prompt hiện tại (prompt được truyền vào hàm)
        response = chat.send_message(prompt)
        
        return response.text
        
    except Exception as e:
        # Báo lỗi 503 hoặc 429 nếu có
        return f"Xin lỗi, tôi đang gặp lỗi kỹ thuật khi kết nối với Gemini. (Lỗi: {e})"

# Đã thêm date_str vào tham số hàm
def send_email_confirmation(email_to, user_name, branch, date_str, time_str, num_people, reservation_id):
    """
    Hàm gửi Email xác nhận đặt bàn.
    """
    
    msg = EmailMessage()
    msg['Subject'] = f"✅ XÁC NHẬN ĐẶT BÀN THÀNH CÔNG - Lotteria - Mã: {reservation_id}"
    msg['From'] = SMTP_CONFIG['EMAIL']
    msg['To'] = email_to
    
    html_content = f"""
    <html>
        <body>
            <h3>Xin chào {user_name},</h3>
            <p>Lotteria rất hân hạnh thông báo đặt bàn của quý khách đã được xác nhận thành công!</p>
            <table border="1" cellpadding="10" cellspacing="0" style="width: 100%; border-collapse: collapse;">
                <tr><td style="background-color: #f2f2f2;"><b>Mã xác nhận:</b></td><td>{reservation_id}</td></tr>
                <tr><td style="background-color: #f2f2f2;"><b>Chi nhánh:</b></td><td>{branch}</td></tr>
                <tr><td style="background-color: #f2f2f2;"><b>Thời gian:</b></td><td>{time_str} ngày {date_str}</td></tr> 
                <tr><td style="background-color: #f2f2f2;"><b>Số lượng khách:</b></td><td>{num_people} người</td></tr>
            </table>
            <p style="margin-top: 20px;">Vui lòng đến đúng giờ để Lotteria phục vụ quý khách tốt nhất. Cảm ơn!</p>
            <p>Trân trọng,<br>Lotteria AI Assistant.</p>
        </body>
    </html>
    """
    msg.add_alternative(html_content, subtype='html')

    try:
        # Kiểm tra nếu đang ở chế độ giả lập (Chưa cấu hình secrets)
        if SMTP_CONFIG['EMAIL'] == "no-reply@lotteria.com.vn":
             # Nâng Exception để chuyển sang thông báo giả lập
             raise Exception("Giả lập: Chưa cấu hình SMTP thực tế trong secrets.toml.")
             
        # Gửi Email thực tế
        with smtplib.SMTP_SSL(SMTP_CONFIG['SERVER'], SMTP_CONFIG['PORT']) as server:
            server.login(SMTP_CONFIG['EMAIL'], SMTP_CONFIG['PASSWORD'])
            server.send_message(msg)
            return True, "Email đã được gửi thành công!"
            
    except smtplib.SMTPAuthenticationError:
        return False, "Lỗi xác thực SMTP. Vui lòng kiểm tra Email/Mật khẩu ứng dụng trong secrets.toml."
    except Exception as e:
        # Bắt cả lỗi giả lập và lỗi hệ thống
        return False, f"{e}"
        
# --- KHỞI TẠO DATABASE ---
DB_NAME = init_db()


# --- 4. GIAO DIỆN CHÍNH (TABS) ---

tab1, tab2, tab3 = st.tabs(["🛎️ Đặt Bàn Tự Động", "🌟 Gợi Ý Món Ăn", "💬 Chatbot Trợ Lý"])

# =========================================================================
# TAB 1: ĐẶT BÀN TỰ ĐỘNG (LOGIC GIỚI HẠN GIỜ 09:00 - 22:00)
# =========================================================================
with tab1:
    st.header("1. Đặt Bàn Tại Chi Nhánh Lotteria")
    
    col1, col2 = st.columns(2)
    
    # Định nghĩa giới hạn thời gian mở cửa (09:00 - 22:00)
    MIN_BOOKING_TIME = dt_time(9, 0)
    MAX_BOOKING_TIME = dt_time(22, 0) 
    
    # Tính thời gian đặt bàn sớm nhất có thể (30 phút từ bây giờ)
    now_plus_30 = datetime.now() + timedelta(minutes=30)
    
    # Thiết lập thời gian mặc định cho widget (30 phút tới, nhưng không sớm hơn 9h)
    time_default_value = dt_time(now_plus_30.hour, now_plus_30.minute)
    if datetime.now().time() < MIN_BOOKING_TIME:
        time_default_value = MIN_BOOKING_TIME
    elif datetime.now().time() > MAX_BOOKING_TIME:
        # Nếu đã qua giờ đóng cửa, đặt default vào giờ mở cửa ngày mai
        time_default_value = MIN_BOOKING_TIME 


    with col1:
        st.selectbox("Chọn Tỉnh/Thành phố", ["Hà Nội", "TP. Hồ Chí Minh", "Đà Nẵng"], key="city")
        branch = st.selectbox("Chọn Chi Nhánh", ["Lotteria Vincom Bà Triệu", "Lotteria Tràng Tiền Plaza", "Lotteria Lotte Center"], key="branch")
        
    with col2:
        num_people = st.slider("Số lượng Khách", min_value=1, max_value=10, value=2, key="people")
        
        # THÊM CHỌN NGÀY
        date_booking = st.date_input(
            "Chọn Ngày Đặt bàn", 
            value=datetime.today().date(), 
            min_value=datetime.today().date(), # Chỉ cho phép đặt từ hôm nay trở đi
            key="date_booking"
        )
        
        # Cập nhật biến local để dễ dàng kiểm tra
        time_input = st.time_input(
            "Thời gian Đặt bàn (9:00 - 22:00)", 
            value=time_default_value, 
            key="time"
        )
        # Lưu trữ giá trị thời gian dưới dạng biến local để xử lý
        time_booking = time_input

    st.divider()
    
    user_name = st.text_input("Họ tên Khách hàng", key="name")
    email = st.text_input("Địa chỉ Email", key="email") 
    phone = st.text_input("Số điện thoại (Tùy chọn)", key="phone")

    if st.button("Xác Nhận Đặt Bàn & Gửi Email", use_container_width=True, type="primary"):
        
        # 1. KIỂM TRA THỜI GIAN THEO GIỜ LÀM VIỆC (09:00 - 22:00)
        if time_booking < MIN_BOOKING_TIME or time_booking > MAX_BOOKING_TIME:
            st.error(f"❌ Đặt bàn thất bại! Lotteria chỉ nhận đặt bàn từ {MIN_BOOKING_TIME.strftime('%H:%M')} đến {MAX_BOOKING_TIME.strftime('%H:%M')}.")
            st.stop()
            
        # TÍNH TOÁN VÀ KIỂM TRA TRÙNG LẶP THỜI GIAN
        booking_datetime = datetime.combine(date_booking, time_booking)
        current_datetime = datetime.now()
        now_plus_30 = current_datetime + timedelta(minutes=30)
        
        # 2. KIỂM TRA THỜI GIAN TỐI THIỂU (30 PHÚT TRƯỚC)
        if booking_datetime < now_plus_30:
            min_date_str = now_plus_30.strftime('%d/%m/%Y')
            min_time_str = now_plus_30.strftime('%H:%M')
            st.error(f"❌ Đặt bàn thất bại! Vui lòng đặt bàn ít nhất 30 phút sau thời điểm hiện tại ({min_time_str} ngày {min_date_str}).")
            st.stop()
        
        # 3. XỬ LÝ ĐẶT BÀN
        if user_name and email:
            reservation_id = f"LT{random.randint(10000, 99999)}"
            time_str = time_booking.strftime('%H:%M')
            date_str = date_booking.strftime('%d/%m/%Y') # Format ngày cho hiển thị
            
            # *** BƯỚC: LƯU VÀO DATABASE ***
            try:
                # Lưu toàn bộ datetime vào DB
                full_datetime_str = booking_datetime.strftime('%Y-%m-%d %H:%M:%S')
                reservation_data = (reservation_id, user_name, email, phone, branch, full_datetime_str, num_people)
                save_reservation(reservation_data)
                st.toast(f"Đã lưu đặt bàn vào database thành công. Mã: {reservation_id}")
            except Exception as e:
                st.error(f"❌ Lỗi khi lưu vào database: {e}")
                
            # GỬI EMAIL XÁC NHẬN
            with st.spinner("Đang xử lý và gửi Email xác nhận..."):
                # Đã thêm date_str vào tham số hàm
                success, message = send_email_confirmation(email, user_name, branch, date_str, time_str, num_people, reservation_id)
            
            # XỬ LÝ KẾT QUẢ VÀ HIỂN THỊ
            if success:
                st.success(f"🎉 ĐẶT BÀN THÀNH CÔNG! Mã: **{reservation_id}**.\n\n"
                           f"Vui lòng kiểm tra Email **{email}** để xem chi tiết đặt bàn.")
                st.balloons()
            else:
                st.warning(f"ĐẶT BÀN VẪN THÀNH CÔNG (Mã: {reservation_id}) nhưng **Gửi Email Xác Nhận Thất Bại**.")
                st.error(f"Chi tiết lỗi Email: {message}")
                # Đã loại bỏ thông báo st.info
                
        else:
            st.warning("Vui lòng nhập đầy đủ Họ tên và Địa chỉ Email để xác nhận đặt bàn.")


# =========================================================================
# TAB 2: GỢI Ý MÓN ĂN 
# =========================================================================
with tab2:
    st.header("2. AI Gợi Ý Món Ăn & Combo Hấp Dẫn")
    
    st.markdown("##### 🔍 Bạn đang muốn thưởng thức món gì hôm nay?")
    
    col_filters = st.columns(4)
    
    food_type = col_filters[0].selectbox("Thể loại:", ['Tất cả'] + df_menu['Thể Loại'].unique().tolist())
    flavor = col_filters[1].selectbox("Hương vị:", ['Bất kỳ'] + df_menu['Hương Vị'].unique().tolist())
    max_price = col_filters[2].slider("Giá tối đa (K VND):", min_value=10, max_value=100, value=60, step=5)
    popular = col_filters[3].checkbox("Món Phổ Biến (Top 3)", value=True)

    # Lọc dữ liệu
    filtered_df = df_menu.copy()
    
    if food_type != 'Tất cả':
        filtered_df = filtered_df[filtered_df['Thể Loại'] == food_type]
    
    if flavor != 'Bất kỳ':
        filtered_df = filtered_df[filtered_df['Hương Vị'] == flavor]
        
    filtered_df = filtered_df[filtered_df['Giá (VND)'] <= max_price * 1000]

    filtered_df = filtered_df.sort_values(by='Độ Phổ Biến', ascending=False)
    if popular:
        filtered_df = filtered_df.head(3)
    
    st.divider()
    
    if not filtered_df.empty:
        st.markdown(f"#### 💡 Top {len(filtered_df)} Món Ăn Lotteria được gợi ý cho bạn:")
        
        cols = st.columns(len(filtered_df))
        
        for i, row in filtered_df.reset_index(drop=True).iterrows():
            with cols[i]: 
                with st.container(border=True):
                    # Đã sửa tham số width
                    st.image("https://via.placeholder.com/300x150.png?text=Lotteria+Product", caption=row['Món Ăn'], use_container_width=True)
                    st.write(f"**{row['Món Ăn']}**")
                    st.markdown(f"**{row['Giá (VND)']:,.0f} VND** {'🔥' if row['Khuyến Mãi'] else ''}")
                    st.caption(f"Thể loại: {row['Thể Loại']} | Vị: {row['Hương Vị']}")
                    if st.button("Thêm vào Giỏ hàng", key=f"add_menu_{i}", use_container_width=True):
                        st.toast(f"Đã thêm **{row['Món Ăn']}** vào đơn hàng để thanh toán!")
    else:
        st.info("Không tìm thấy món ăn nào phù hợp với tiêu chí của bạn. Hãy thử thay đổi bộ lọc!")

# =========================================================================
# TAB 3: CHATBOT TRỢ LÝ (SỬ DỤNG GEMINI)
# =========================================================================
with tab3:
    st.header("3. Trò Chuyện Trực Tiếp với AI (Powered by Gemini)")
    
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "Xin chào! Tôi là Lotteria AI Assistant 🍔. Bạn muốn đặt bàn hay có câu hỏi gì về menu Lotteria không?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Hỏi về menu, chi nhánh, hoặc yêu cầu đặt bàn..."):
        if not client:
            st.warning("Chức năng Chatbot đang bị lỗi kết nối API.")
            
        # Thêm prompt hiện tại vào session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Hiển thị prompt
        with st.chat_message("user"):
            st.write(prompt)

        # Tạo và hiển thị phản hồi
        with st.chat_message("assistant"):
            with st.spinner("Lotteria AI đang suy nghĩ..."):
                # Gọi hàm đã sửa lỗi bằng client.chats.create
                response = generate_gemini_response(prompt)
                st.write(response)
        
        # Thêm phản hồi vào session state (nếu response không phải là thông báo lỗi)
        if "Lỗi kỹ thuật khi kết nối với Gemini" not in response:
            st.session_state.messages.append({"role": "assistant", "content": response})

# --- 5. HƯỚNG DẪN CHẠY APP (SIDEBAR) ---
st.sidebar.markdown("---") 

st.sidebar.markdown(
    """
    #### ⚙️ THIẾT LẬP DỰ ÁN
    ---
    **1. Tên File:** `lotteria_agent.py`
    
    **2. Khóa Bí mật (.streamlit/secrets.toml):**
    
    * `GEMINI_API_KEY = "..."` (Bắt buộc cho Chatbot)
    
    **3. Lệnh Chạy (Đã kích hoạt venv):**
    
    `streamlit run lotteria_agent.py`
    
    ***LƯU Ý:*** File database `reservations.db` sẽ được tạo ra cùng thư mục.
    """
)