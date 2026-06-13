# Hướng Dẫn Kiến Thức Cốt Lõi Hệ Thống Quản Trị VPN

Tài liệu này cung cấp các kiến thức cơ bản, thuật ngữ và cơ chế hoạt động đằng sau dự án **AEGIS VPN Management Platform** để phục vụ việc hiểu sâu hệ thống và báo cáo học tập.

---

## 1. Kiến Trúc Modular Monolith (Đơn Khối Mô-đun)

Dự án được xây dựng theo mô hình **Modular Monolith**:
*   **Khái niệm**: Toàn bộ hệ thống chạy chung một tiến trình duy nhất (Backend FastAPI) nhưng mã nguồn được phân rã rõ ràng thành các miền nghiệp vụ (domain) độc lập tại thư mục `backend/app/modules/` (`auth`, `users`, `vpn`, `sessions`, `audit`, `threats`).
*   **Ưu điểm**:
    *   Giữ cho việc triển khai (deploy) đơn giản qua Docker Compose (chỉ gồm 3 dịch vụ chính: Frontend, Backend, PostgreSQL).
    *   Hạn chế tối đa độ trễ truyền tin so với mô hình Microservices.
    *   Dễ viết kiểm thử tích hợp (Integration Tests) và dễ debug khi trình bày demo.

---

## 2. Xác Thực 2 Lớp TOTP (Time-Based One-Time Password)

TOTP là thuật toán cốt lõi cho tính năng xác thực hai lớp (2FA) trong dự án (tuân thủ tiêu chuẩn **RFC 6238**):
*   **Cơ chế hoạt động**:
    1.  **Secret Key**: Hệ thống tạo ngẫu nhiên một chuỗi Base32 bảo mật lưu trong database của User (`User.mfa_secret`).
    2.  **Mã hóa theo thời gian**: Cả điện thoại (ứng dụng Authenticator) và máy chủ Backend cùng sử dụng hàm băm mật mã học **HMAC-SHA1** trên một bộ đếm thời gian (Interval) có giá trị thay đổi mỗi **30 giây** (`time_step = int(time.time() / 30)`).
    3.  **Trích xuất mã**: Kết quả băm được rút gọn động (Dynamic Truncation) để lấy ra một số nguyên 6 chữ số (mã OTP).
*   **Độ trễ thời gian (Clock Drift Window)**: Hệ thống cho phép sai lệch thời gian (Drift Window) bằng `1` bước (tức chấp nhận mã OTP ở 30 giây trước đó và 30 giây tiếp theo). Điều này giúp người dùng không bị đăng nhập thất bại nếu đồng hồ trên điện thoại bị lệch nhẹ so với server.

---

## 3. Quản Lý Phiên Bằng JWT Trong Cookie HttpOnly

Dự án áp dụng cơ chế quản lý JWT (JSON Web Token) đạt tiêu chuẩn bảo mật doanh nghiệp:
*   **Rủi ro của LocalStorage**: Nếu lưu JWT trong `localStorage`, kẻ tấn công có thể dễ dàng ăn trộm token này thông qua các mã độc JavaScript (tấn công XSS - Cross-Site Scripting).
*   **Giải pháp HttpOnly Cookie**:
    *   Token JWT được lưu trong Cookie tên là `session_token` (hoặc `__Host-session` khi chạy HTTPS).
    *   Cookie này được gán cờ `HttpOnly`, nghĩa là **JavaScript phía client hoàn toàn không thể đọc hoặc chỉnh sửa nó**. Chỉ có trình duyệt mới tự động gửi cookie này kèm theo các API request.
    *   Gán cờ `SameSite=Lax` để ngăn chặn việc gửi cookie tự động từ các trang web lạ, giúp chống lại tấn công **CSRF** (Cross-Site Request Forgery).
    *   Đồng thời đính kèm tiêu đề HTTP Header `X-Requested-With` cho các cuộc gọi trạng thái để tăng thêm lớp phòng vệ CSRF thứ hai.

---

## 4. Ngăn Chặn Lỗ Hổng IDOR Bằng UUID v4

*   **IDOR (Insecure Direct Object Reference)**: Là lỗ hổng xảy ra khi kẻ tấn công thay đổi tham số ID trong URL/API (ví dụ thay đổi `/api/vpn/profiles/1` thành `/api/vpn/profiles/2`) để truy cập trái phép tài nguyên của người dùng khác khi hệ thống chỉ sử dụng ID số tự tăng đơn giản.
*   **Giải pháp UUID**: Hệ thống đã được chuyển đổi toàn bộ khóa chính sang **UUID v4** (ví dụ: `7baaed46-88ba-465c-8ffe-9a30eedf50da`). Vì UUID là chuỗi ngẫu nhiên dài 36 ký tự và có không gian mẫu khổng lồ, kẻ tấn công không thể đoán hoặc tự dò quét ID của người dùng khác.

---

## 5. Quản Lý Khóa Cấu Hình WireGuard VPN

Hệ thống hoạt động giống như một **VPN Controller**:
*   Khi Admin nhấn "Provision", hệ thống tự động sinh 3 loại khóa bảo mật của giao thức WireGuard:
    1.  **Private Key**: Khóa riêng tư của client (không bao giờ lộ ra ngoài, lưu trong cấu hình client).
    2.  **Public Key**: Khóa công khai gửi cho máy chủ VPN để nhận diện client.
    3.  **Preshared Key**: Khóa đối xứng chia sẻ trước để tăng độ bảo mật chống giải mã lưu lượng sau này.
*   Địa chỉ IP của mỗi User (`assigned_ip`) được tính toán **deterministic** bằng cách băm chuỗi UUID của người dùng qua hàm MD5, lấy phần dư chia cho 200 để map vào dải subnet `10.8.0.x/32`. Điều này đảm bảo mỗi người dùng có một IP cố định và duy nhất.

---

## 6. Nhật Ký Kiểm Toán (Audit Logging)

Để phục vụ vai trò **Auditor (Giám sát viên)**:
*   Mọi hành động nhạy cảm (Đăng nhập, đăng xuất, tạo user, tắt/bật 2FA, cấp phát/thu hồi VPN) đều được ghi nhận vào bảng `audit_logs`.
*   Hệ thống kiểm tra tiêu đề `X-Forwarded-For` để phân tích và lưu lại địa chỉ IP thật của người dùng kể cả khi hệ thống chạy phía sau các proxy/load balancer như Nginx.
