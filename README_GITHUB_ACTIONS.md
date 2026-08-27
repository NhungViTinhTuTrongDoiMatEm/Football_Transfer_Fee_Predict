# 🚀 Hướng dẫn cấu hình Secrets chạy GitHub Actions (Mùa giải 2026)

Để tự động hóa hoàn toàn quy trình cào dữ liệu mới, chạy dbt cập nhật Supabase và huấn luyện lại AI định kỳ vào sáng thứ Hai hàng tuần, bạn cần cấu hình các khóa bảo mật (Secrets) trên Repository GitHub mới này.

---

## 🔑 Danh sách các Secrets cần cấu hình

| Tên Secret (chính xác) | Mô tả | Giá trị ví dụ / Mật khẩu của bạn |
| :--- | :--- | :--- |
| **`DB_PASSWORD`** | Mật khẩu tài khoản database Supabase của bạn | `Kartrider8806` |
| **`API_KEY`** | Mã API-Key bóng đá (API-Sports / API-Football) | *Mã key cào dữ liệu bóng đá của bạn* |

---

## 🛠️ Hướng dẫn cấu hình chi tiết (Từng bước)

1. Truy cập vào trang web Repository này trên GitHub: **`NhungViTinhTuTrongDoiMatEm/Football_Transfer_Fee_Predict`**
2. Nhấp chuột vào tab **`Settings`** (Biểu tượng bánh răng trên thanh menu ngang đầu trang).
3. Nhìn vào danh mục bên trái, tìm đến mục **`Security`** ➜ Chọn **`Secrets and variables`** ➜ Chọn **`Actions`**.
4. Tại khu vực **`Repository secrets`**, bấm nút màu xanh **`New repository secret`**:
   * **Lần 1 (Tạo khoá DB):**
     * Ô **Name**: điền `DB_PASSWORD`
     * Ô **Secret**: điền `Kartrider8806`
     * Bấm **Add secret**.
   * **Lần 2 (Tạo khoá API):**
     * Bấm lại **New repository secret**.
     * Ô **Name**: điền `API_KEY`
     * Ô **Secret**: điền mã API key bóng đá của bạn.
     * Bấm **Add secret**.

---

## ⚡ Cách kích hoạt và theo dõi chạy thử thủ công

Sau khi đã điền đủ 2 secret ở trên, bạn làm như sau để kiểm tra:
1. Vào tab **`Actions`** (nằm cạnh tab Pull Requests trên thanh menu ngang).
2. Cột bên trái mục **Workflows**, chọn **`Weekly ELT & AI Pipeline`** (hoặc tên file `.github/workflows/weekly_elt.yml`).
3. Góc phải màn hình sẽ có nút **`Run workflow`** màu xanh dương ➜ Bấm vào và chọn nút xanh lá cây **`Run workflow`** để kích hoạt chạy thử.
4. Nhấp vào tiến trình đang chạy (vòng tròn xoay màu vàng) để xem màn hình dòng lệnh trực tiếp (Console logs) của cả 5 bước chạy tự động!
