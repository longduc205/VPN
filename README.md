# Hệ thống quản lý VPN

Dự án xây dựng một hệ thống quản lý VPN trên nền web, phục vụ cho việc quản trị, giám sát và kiểm soát truy cập an toàn.

## Tổng quan

Repository này được tổ chức theo hướng `modular monolith`, nhằm quản lý người dùng VPN, sinh cấu hình VPN, theo dõi phiên kết nối và ghi nhận các sự kiện bảo mật.

## Công nghệ sử dụng

- Frontend: Next.js + React
- Backend: FastAPI
- Cơ sở dữ liệu: PostgreSQL
- VPN: WireGuard
- Triển khai: Docker + Docker Compose

## Cấu trúc repository

```text
vpn-management-system/
├── frontend/               # Giao diện web dashboard
├── backend/                # API FastAPI và nghiệp vụ chính
├── vpn-controller/         # Lớp tích hợp VPN
├── monitoring/             # Hệ thống metrics và cảnh báo
├── infra/                  # File Docker và triển khai
├── docs/                   # Tài liệu kiến trúc và kế hoạch
└── README.md
```

## Yêu cầu trước khi chạy

Cài đặt các công cụ sau trước khi chạy dự án:

- Docker
- Docker Compose
- Python 3.11+
- Node.js 20+
- Git

## Cài đặt local

### 1. Clone repository

```bash
git clone <your-repo-url>
cd VPN
```

### 2. Khởi động database và các service nền

```bash
docker compose -f infra/compose/docker-compose.yml up -d postgres
```

### 3. Chạy backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Kiểm tra backend:

- `GET http://localhost:8000/health`

### 4. Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

Ứng dụng frontend:

- `http://localhost:3000`

## Chạy bằng Docker Compose

Bạn cũng có thể chạy toàn bộ hệ thống bằng Docker Compose:

```bash
docker compose -f infra/compose/docker-compose.yml up --build
```

## Những phần đã được dựng sẵn

- Backend FastAPI có endpoint kiểm tra trạng thái
- Frontend Next.js với trang khởi tạo
- Docker Compose cho backend, frontend và PostgreSQL
- Thư mục tài liệu kiến trúc

## Các bước tiếp theo dự kiến

- Xác thực và đăng nhập JWT
- RBAC và MFA
- Quản lý người dùng VPN
- Sinh cấu hình WireGuard
- Theo dõi phiên kết nối và audit log
- Phát hiện bất thường và cảnh báo

## Ghi chú

Dự án hiện đang ở giai đoạn skeleton. Repository được tổ chức để mỗi phân hệ có thể phát triển độc lập và mở rộng dần thành một nền tảng hoàn chỉnh.

