---
applyTo: "src/actuator/**, src/capture/**, hardware/**, deploy/**"
description: Quy tắc an toàn và kỹ thuật khi làm việc với phần cứng Raspberry Pi 5 — GPIO, relay, mạch phát IR, camera, nguồn điện và triển khai systemd. Đọc trước khi đấu nối hoặc viết code điều khiển phần cứng.
---

# Instructions: An toàn & kỹ thuật phần cứng

Áp dụng khi động vào `src/actuator/`, `src/capture/`, `hardware/`, `deploy/`.

---

## ⚡ 1. An toàn điện — ĐỌC TRƯỚC KHI ĐẤU NỐI

> Đồ án có phần điều khiển đèn qua relay. Nếu chuyển sang **điện lưới 220 V** thì đây là
> hạng mục nguy hiểm nhất của cả đồ án.

### Quy tắc bắt buộc

1. **Ưu tiên mô phỏng bằng LED 5 V.** Đề cương đã cho phép: *"sản phẩm demo là mô phỏng với LED
   hoặc lắp đặt thật"*. Chỉ chuyển sang 220 V khi mọi logic đã chạy đúng hoàn toàn với LED.
2. **Ngắt nguồn hoàn toàn trước mọi thao tác đấu nối** — cả nguồn Pi và nguồn tải.
3. **Không bao giờ chạm vào phía 220 V khi mạch đang có điện.** Dùng relay có vỏ cách điện,
   bọc kín đầu nối phía AC, không để dây trần.
4. **Dùng relay có opto-isolation** (cách ly quang) — bắt buộc, để bảo vệ Pi khỏi xung điện từ tải.
5. **GPIO Raspberry Pi là 3,3 V** — cấp 5 V vào chân GPIO sẽ **hỏng vĩnh viễn** SoC.
   Kiểm tra module relay có hỗ trợ mức logic 3,3 V không (nhiều module chỉ chạy 5 V).
6. **Dòng tối đa mỗi chân GPIO: 16 mA; tổng toàn bộ chân: 50 mA.**
   LED phải có điện trở hạn dòng (220 Ω – 330 Ω). Relay/motor phải cấp nguồn riêng, không lấy từ GPIO.
7. **Nguồn Pi 5 phải là adapter USB-C 27 W chính hãng.** Nguồn yếu → undervoltage → throttling →
   FPS tụt và kết quả benchmark sai lệch.
8. **Chụp ảnh sơ đồ đấu nối trước khi cấp điện lần đầu**, lưu vào `hardware/` — cần cho báo cáo
   và để đấu lại nếu tháo.

### Nếu bắt buộc dùng 220 V

- Nhờ **người có chuyên môn kiểm tra** trước khi cấp điện.
- Dùng **aptomat/cầu chì** phía nguồn.
- Thử nghiệm với **bóng đèn công suất nhỏ** trước.
- **Không để hệ thống chạy 220 V không có người giám sát** trong giai đoạn thử nghiệm.
- Ghi mục "An toàn điện" trong báo cáo Chương 3.

---

## 2. Bảng chân GPIO — tài liệu hoá bắt buộc

Duy trì `hardware/gpio-pinout.md`:

```markdown
| Chức năng   | Chân BCM | Chân vật lý | Kiểu | Ghi chú |
|-------------|----------|-------------|------|---------|
| Relay đèn 1 | GPIO 17  | 11          | OUT  | Active LOW — module relay JQC-3FF |
| Relay đèn 2 | GPIO 27  | 13          | OUT  | Active LOW |
| LED phát IR | GPIO 18  | 12          | OUT  | PWM 38 kHz, qua transistor NPN 2N2222 |
| LED báo TT  | GPIO 22  | 15          | OUT  | Qua điện trở 330 Ω |
| Nút reset   | GPIO 23  | 16          | IN   | Pull-up nội, active LOW |
```

⚠️ **Lưu ý `active LOW`**: đa số module relay giá rẻ kích hoạt khi chân xuống LOW.
Ghi rõ trong `configs/actuator.yaml`, đừng để sai gây bật/tắt ngược:

```yaml
devices:
  den_phong_khach:
    pin: 17
    active_low: true      # module relay JQC-3FF kích hoạt ở mức LOW
```

⚠️ **Chân GPIO 2, 3** dành cho I2C — tránh dùng nếu có kế hoạch mở rộng cảm biến.
⚠️ **Chân GPIO 14, 15** là UART — tránh dùng nếu cần debug qua serial.

---

## 3. Trạng thái an toàn — fail-safe

**Nguyên tắc: mọi lỗi đều dẫn về trạng thái TẮT.**

```python
def dong(self) -> None:
    """Đưa mọi thiết bị về trạng thái an toàn và giải phóng GPIO."""
    for ten in self.thiet_bi:
        try:
            self.tat(ten)
        except Exception as e:                    # cố tắt cho bằng hết
            logger.error("Không tắt được %s: %s", ten, e)
    GPIO.cleanup()
    logger.info("Đã đưa mọi thiết bị về trạng thái tắt và giải phóng GPIO.")
```

Bắt buộc:
- Gọi `dong()` trong khối `finally` của vòng lặp chính.
- Đăng ký handler `SIGTERM`/`SIGINT` (systemd dừng dịch vụ bằng SIGTERM).
- **Khởi tạo GPIO ở trạng thái TẮT**, không để trạng thái không xác định lúc boot.
- **Không gọi `GPIO.cleanup()` giữa chừng** khi hệ thống còn chạy — sẽ làm relay nhả ngẫu nhiên.

---

## 4. Chống nhiễu & chống bật/tắt liên tục

Nhận diện theo frame rất dễ nhấp nháy (frame này nhận ra, frame sau không).
**Bắt buộc** có 3 cơ chế:

```yaml
# configs/actuator.yaml
decision:
  n_frame_xac_nhan: 3        # cần 3 frame liên tiếp cùng danh tính mới kích hoạt
  cooldown_giay: 10          # sau khi tác động, khoá 10 s không tác động lại cùng thiết bị
  timeout_vang_mat_giay: 30  # vắng mặt 30 s mới tự tắt đèn
```

- **N frame xác nhận**: chống nhận diện nhấp nháy.
- **Cooldown**: chống relay đóng/ngắt liên tục (hại relay, nguy hiểm với tải điện).
- **Timeout vắng mặt**: tránh tắt đèn ngay khi người vừa quay mặt đi.

Ba tham số này phải **ghi vào báo cáo** — chúng ảnh hưởng trực tiếp tới độ trễ end-to-end đo ở
Phase 5, nên phải nêu rõ khi trình bày kết quả (`n_frame_xac_nhan = 3` cộng thêm ~2 frame vào độ trễ).

---

## 5. Phát hồng ngoại (IR) điều khiển tivi

### Nguyên lý
- Sóng mang **38 kHz** (chuẩn phổ biến; một số hãng dùng 36/40 kHz).
- Giao thức thường gặp: **NEC** (địa chỉ 8 bit + lệnh 8 bit + bit đảo).
- LED IR cần **transistor khuếch đại** (2N2222 / S8050) — GPIO không đủ dòng để LED phát xa.

### Quy trình chuẩn
1. **Ghi mã remote thật trước**: dùng module thu IR (VS1838B) + `mode2`/`irrecord` của LIRC.
2. Lưu mã vào `hardware/ir-codes/<hãng tivi>.conf` + tài liệu hoá trong `hardware/README.md`.
3. Phát bằng `pigpio` (định thời chính xác hơn `RPi.GPIO` cho tín hiệu 38 kHz) hoặc LIRC.
4. **Kiểm tra LED IR có phát không**: nhìn qua camera điện thoại — mắt thường không thấy IR
   nhưng cảm biến camera thấy được ánh sáng tím nhạt.

### Hạn chế phải ghi trong báo cáo
- IR là **một chiều** — không có phản hồi, hệ thống **không biết** tivi đã bật hay chưa.
  → Trạng thái thiết bị trên web giám sát là **trạng thái giả định**, phải nói rõ điều này.
- Cần **đường truyền thẳng** tới mắt nhận của tivi.
- Tầm hiệu quả thường 3 – 5 m tuỳ công suất LED.

---

## 6. Camera

- **Camera Module** dùng `libcamera` / `picamera2` (Pi OS Bookworm đã bỏ stack camera cũ).
- **USB Webcam** dùng OpenCV `VideoCapture(index)` — đơn giản hơn, khuyến nghị cho đồ án này.
- Đặt độ phân giải **thấp nhất chấp nhận được** (640×480 hoặc 1280×720) — cao hơn chỉ tốn CPU.
- **Tách thread đọc camera** khỏi thread xử lý, queue `maxsize=2`, bỏ frame cũ.
- Xử lý mất kết nối: thử kết nối lại có backoff, tối đa N lần rồi dừng an toàn.
- **Không để camera mở mà không đóng** — lần chạy sau sẽ báo "device busy".
  Luôn `cap.release()` trong `finally`.

---

## 7. Nhiệt độ & throttling

Pi 5 chạy inference liên tục **rất nóng**. Không có tản nhiệt → throttle → FPS tụt →
số liệu benchmark **không tái lập được**.

```bash
vcgencmd measure_temp        # nhiệt độ hiện tại
vcgencmd get_throttled       # 0x0 = bình thường
```

Mã cờ `get_throttled`:

| Bit | Ý nghĩa |
|---|---|
| 0 | Đang under-voltage |
| 1 | Đang giới hạn tần số ARM |
| 2 | Đang throttling |
| 16 | Đã từng under-voltage |
| 18 | Đã từng throttling |

**Bắt buộc:**
- Lắp **tản nhiệt + quạt** (Active Cooler chính hãng) trước khi đo benchmark chính thức.
- Ghi nhiệt độ vào `.meta.json` mỗi lần đo (xem `experiment-protocol.instructions.md`).
- Cảnh báo log khi nhiệt độ > 75 °C.
- Nếu `get_throttled != 0x0` trong phiên đo → **kết quả không hợp lệ, phải đo lại**.

---

## 8. Triển khai systemd (Phase 6)

`deploy/systemd/faceid.service`:

```ini
[Unit]
Description=He thong nhan dien khuon mat va dieu khien thiet bi
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/faceid
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/home/pi/faceid/.env
ExecStart=/home/pi/faceid/.venv/bin/python -m src.main --config configs/system.yaml
Restart=on-failure
RestartSec=10
TimeoutStopSec=20
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable faceid.service
sudo systemctl start faceid.service
journalctl -u faceid.service -f      # xem log realtime
```

Lưu ý:
- `TimeoutStopSec=20` để chương trình kịp chạy `dong()` đưa thiết bị về trạng thái an toàn.
- `Restart=on-failure` — **không dùng `always`**, vì lỗi cấu hình sẽ gây vòng lặp khởi động vô tận.
- Secrets đặt trong `EnvironmentFile`, **không viết trực tiếp** vào file `.service`.
- Kiểm chứng: `sudo reboot` → hệ thống phải tự chạy lại. Đây là tiêu chí Cổng C của Phase 6.

---

## 9. Checklist trước khi cấp điện lần đầu

- [ ] Đã ngắt nguồn khi đấu nối
- [ ] Kiểm tra lại từng dây theo `hardware/gpio-pinout.md`
- [ ] Không có chân GPIO nào bị cấp 5 V
- [ ] LED có điện trở hạn dòng
- [ ] Relay dùng nguồn riêng, có opto-isolation
- [ ] Không có dây trần / mối nối hở
- [ ] Đã chụp ảnh sơ đồ đấu nối lưu vào `hardware/`
- [ ] Chạy `--dry-run` với backend mock trước, xác nhận logic đúng
- [ ] Chạy thật với LED trước, chỉ chuyển sang tải thật khi LED đã đúng
- [ ] Đã lắp tản nhiệt + quạt
- [ ] Nguồn USB-C 27 W chính hãng
