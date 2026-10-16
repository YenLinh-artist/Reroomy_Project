# Re:Room — Website decor phòng

Website bán đồ decor phòng trọ và căn hộ nhỏ, xây dựng bằng Django. Hướng dẫn này dành cho chạy thử và trình bày demo trên máy Windows.

## Yêu cầu

- Windows 10/11
- Python 3.10 trở lên
- PowerShell

## Cài đặt và chạy

Mở PowerShell tại thư mục chứa `manage.py`, sau đó chạy:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Nếu lệnh `py` không hoạt động, thay `py` bằng `python` ở lệnh tạo môi trường ảo.

Mở website tại <http://127.0.0.1:8000/>. Dừng server bằng `Ctrl+C` trong terminal.

### Nếu PowerShell chặn kích hoạt môi trường ảo

Có thể bỏ qua bước kích hoạt và gọi Python trong môi trường ảo bằng đường dẫn đầy đủ:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

## Tài khoản quản trị

Để tạo tài khoản quản trị riêng trên máy demo:

```powershell
python manage.py createsuperuser
```

Làm theo hướng dẫn trong terminal để đặt tên đăng nhập và mật khẩu. Đăng nhập tại <http://127.0.0.1:8000/dang-nhap/>; trang quản trị website ở <http://127.0.0.1:8000/quan-tri/>. Django Admin có tại <http://127.0.0.1:8000/admin/>. Không đưa mật khẩu vào mã nguồn hoặc tài liệu nộp bài.

Khách hàng có thể tạo tài khoản tại <http://127.0.0.1:8000/dang-ky/> hoặc mua hàng với tư cách khách.

## Kịch bản demo gợi ý

1. Trang chủ `/`: xem danh mục, sản phẩm và phòng mẫu.
2. Thêm sản phẩm vào giỏ, mở `/gio-hang/` và tiếp tục đến trang thanh toán.
3. Điền tên, số điện thoại và địa chỉ nhận hàng, chọn COD, rồi đặt hàng.
4. Trang xác nhận cung cấp liên kết theo dõi đơn hàng. Khách đã đăng nhập có thể xem đơn trong tài khoản.
5. Đăng nhập bằng tài khoản quản trị, vào `/quan-tri/` để xem và xử lý đơn.

Trong cấu hình demo hiện tại, thanh toán được hỗ trợ là COD. Khi chưa có sản phẩm trong cơ sở dữ liệu, website dùng danh sách sản phẩm minh họa. Hai mã demo `ROOM25` và `XINH10` chỉ có sẵn khi chế độ demo được bật.

## Dữ liệu và lệnh kiểm tra

- Django dùng SQLite tại `db.sqlite3`; dữ liệu được giữ lại giữa các lần chạy. Không xóa file này nếu muốn giữ dữ liệu demo hiện có.
- Ảnh tải lên được lưu trong thư mục `media/`.
- Nếu có thay đổi schema trong bản mã mới, chạy `python manage.py migrate`.
- Kiểm tra cấu hình Django bằng `python manage.py check`.

## Công nghệ

- Python 3.10+
- Django 5.2.17
- SQLite
- HTML, CSS và JavaScript

Đây là cấu hình chạy demo cục bộ, không phải cấu hình triển khai website công khai.

