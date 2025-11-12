<div align="center">

# 🎯 LotteriaAI
<img src="lotteria.png" alt="Lotteria" width="150" />

### *AI Agent Đặt Bàn & Gợi Ý Món Ăn Tự Động Cho Chuỗi Nhà Hàng Lotteria*

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.25+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![SQLite](https://img.shields.io/badge/SQLite-3.x-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![MIT License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<p align="center">
  <img src="logoDaiNam.png" alt="DaiNam University Logo" width="200"/>
  <img src="LogoAIoTLab.png" alt="AIoTLab Logo" width="170"/>
</p>

**Sử dụng AI (Google Gemini) để quản lý đặt bàn, gợi ý món ăn dựa trên sở thích và lịch sử khách hàng.**

[🚀 Demo](#-demo) • [✨ Tính Năng](#-tính-năng) • [📦 Cài Đặt](#-cài-đặt) • [📖 Tài Liệu](#-tài-liệu) • [🤝 Đóng Góp](#-đóng-góp)

---

</div>

## 📋 Mục Lục

- [Giới Thiệu](#-giới-thiệu)
- [Tính Năng](#-tính-năng)
- [Công Nghệ](#-công-nghệ)
- [Google Gemini AI](#-google-gemini-ai)
- [Cài Đặt](#-cài-đặt)
- [Sử Dụng](#-sử-dụng)
- [Roadmap](#-roadmap)
- [Đóng Góp](#-đóng-góp)
- [License](#-license)

---

## 🎯 Giới Thiệu

**LotteriaAI** là hệ thống AI Agent tự động cho chuỗi nhà hàng Lotteria, giúp khách hàng:

- 🤖 **Đặt bàn tự động** - AI quản lý lịch trống, gợi ý khung giờ phù hợp  
- 🍔 **Gợi ý món ăn thông minh** - Dựa trên sở thích, lịch sử, combo hot  
- 📊 **Quản lý đơn hàng** - Theo dõi đơn, cập nhật trạng thái  
- 📈 **Thống kê nhu cầu** - Biểu đồ món được order nhiều nhất, khung giờ đông khách  

### 🌟 Điểm Đặc Biệt

- ✅ **Hoàn toàn tự động** - Khách hàng không cần gọi trực tiếp  
- ✅ **AI Gợi Ý Thông Minh** - Combo và món phổ biến được đề xuất  
- ✅ **Streamlit UI** - Giao diện web trực quan  
- ✅ **SQLite Database** - Lưu trữ thông tin khách, đơn, món ăn  
- ✅ **Tiếng Việt** - Giao diện và thông tin hoàn toàn tiếng Việt  

---

## ✨ Tính Năng

### 🤖 1. Đặt Bàn Thông Minh

- Kiểm tra lịch trống theo chi nhánh và khung giờ  
- Đề xuất khung giờ tối ưu dựa trên số lượng khách  
- Tự động xác nhận hoặc gợi ý giờ khác nếu hết chỗ  

### 🍔 2. Gợi Ý Món Ăn

- Dựa trên sở thích cá nhân (lịch sử order, món yêu thích)  
- Combo đề xuất cho nhóm hoặc gia đình  
- Phân tích xu hướng món ăn - Top món hot hiện tại  

### 📊 3. Quản Lý Đơn Hàng

- Lưu thông tin khách hàng: tên, số điện thoại, chi nhánh  
- Lưu chi tiết đơn: món, số lượng, tổng tiền  
- Cập nhật trạng thái: đang chuẩn bị, sẵn sàng, đã thanh toán  

### 🔍 4. Dashboard & Thống Kê

- Món ăn phổ biến theo tuần/tháng  
- Khung giờ đông khách  
- Tổng doanh thu & số lượng khách  
- Gợi ý điều chỉnh menu dựa trên dữ liệu  

---

## 🛠️ Công Nghệ

| Công Nghệ | Phiên Bản | Mục Đích |
|-----------|-----------|----------|
| Python | 3.12+ | Ngôn ngữ chính |
| Streamlit | 1.25+ | Frontend & dashboard |
| SQLite | 3.x | Database |
| Google Gemini | 2.5 Flash | AI gợi ý món ăn & đặt bàn |

---

## 🤖 Google Gemini AI

**Tích hợp AI Agent để:**  

- Gợi ý món ăn dựa trên sở thích khách, lịch sử order, combo hot  
- Đề xuất khung giờ đặt bàn tối ưu dựa trên số lượng khách và lịch trống  
- Giải thích lý do gợi ý: "Tại sao món này phù hợp với bạn" hoặc "Khung giờ này ít đông khách"  

---
## 🏗️ Kiến Trúc Hệ Thống
STREAMLIT UI --> AI Agent (Gemini) --> SQLite DB
- Trang đặt bàn
- Trang gợi ý món ăn
- Dashboard

---
## 📦 Cài Đặt
1. Clone repo & tạo virtual environment
git clone https://github.com/username/LotteriaAI.git
cd LotteriaAI
python -m venv venv

- Windows:
venv\Scripts\activate
- Linux/Mac:
source venv/bin/activate

2. Cài dependencies
pip install -r requirements.txt

3. Tạo .env lưu API key Gemini
GOOGLE_API_KEY=<YOUR_API_KEY>

4. Chạy ứng dụng
streamlit run app.py

Truy cập: http://localhost:8501

---

## 🚀 Sử Dụng

- Đặt bàn: chọn chi nhánh, số lượng khách, khung giờ

- Gợi ý món ăn: AI đề xuất combo và món phù hợp


---
## 🎓 Roadmap

- SMS/Email thông báo khi đặt bàn thành công

- Mobile App (React Native)

- Multi-language support

---

## 🤝 Đóng Góp

- Fork repo → tạo branch → commit → push → pull request

---
## 📄 License

- MIT License
