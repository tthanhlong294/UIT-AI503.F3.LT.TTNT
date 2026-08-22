# Chương 2 — Cơ sở lý thuyết

> **Khung làm việc.** Ngân sách **~11 trang** — chương dài nhất báo cáo.
> Không phụ thuộc kết quả thực nghiệm nên viết được sớm, viết dần theo Cổng D của từng Phase.
>
> Nguyên tắc: chương này trình bày **phương pháp**, không trình bày **kết quả**. Mọi con số đo được
> của nghiên cứu này thuộc Chương 4. Số liệu của công trình khác phải kèm trích dẫn và nói rõ đó là
> kết quả của họ.

| Mục | Trang | Viết ở Cổng D của | Trạng thái |
|---|---|---|---|
| **2.1 Mạng nơ-ron tích chập** | ~1,5 | Phase 2 | ✅ **bản nháp 1** |
| **2.2 Phát hiện khuôn mặt — YOLOv8n-face** | ~2 | Phase 2 | ✅ **bản nháp 1** |
| **2.3 Trích xuất đặc trưng khuôn mặt** | ~2,5 | Phase 3 | ✅ **bản nháp 1** |
| **2.4 Học đo lường và độ tương đồng cosine** | ~1,5 | Phase 3 | ✅ **bản nháp 1** |
| **2.5 Phát hiện giả mạo** | ~2 | Phase 4 | ✅ **bản nháp 1** |
| **2.6 Suy luận trên thiết bị biên** | ~1 | Phase 2 | ✅ **bản nháp 1** |
| 2.7 Điều khiển thiết bị — GPIO và hồng ngoại | ~0,5 | Phase 5 | ⛔ **chặn — chưa có Pi 5** |

---

## 2.1. Mạng nơ-ron tích chập trong thị giác máy tính

### 2.1.1. Phép tích chập và trường tiếp nhận

Mạng nơ-ron kết nối đầy đủ không phù hợp với dữ liệu ảnh. Một khung hình 1280 × 720 điểm ảnh ba kênh
màu chứa gần 2,8 triệu giá trị đầu vào; chỉ riêng lớp kết nối đầy đủ đầu tiên với một nghìn nơ-ron đã
cần gần 2,8 tỉ tham số. Con số này vượt xa khả năng huấn luyện lẫn khả năng lưu trữ, và quan trọng hơn,
nó bỏ qua hai đặc tính vốn có của ảnh: thông tin có tính **cục bộ** — các điểm ảnh lân cận liên quan
chặt chẽ với nhau hơn các điểm ở xa — và mẫu hình có tính **lặp lại** — một cạnh hay một góc mang cùng
ý nghĩa dù xuất hiện ở đâu trong khung hình.

**Phép tích chập** (convolution) khai thác đúng hai đặc tính này. Một bộ lọc (kernel) kích thước nhỏ,
thường 3 × 3, trượt qua toàn bộ ảnh; tại mỗi vị trí, giá trị đầu ra là tổng có trọng số của vùng ảnh
nằm dưới bộ lọc. Hai hệ quả trực tiếp:

- **Kết nối cục bộ**: mỗi giá trị đầu ra chỉ phụ thuộc một vùng nhỏ của đầu vào, thay vì toàn bộ ảnh.
- **Chia sẻ trọng số**: cùng một bộ lọc dùng lại ở mọi vị trí, nên số tham số không phụ thuộc kích
  thước ảnh. Một bộ lọc 3 × 3 trên ảnh ba kênh chỉ cần 27 trọng số, bất kể ảnh lớn hay nhỏ.

Chia sẻ trọng số còn mang lại tính **tương đương tịnh tiến** (translation equivariance): khuôn mặt dịch
sang phải trong khung hình thì đặc trưng tương ứng cũng dịch sang phải, không cần mạng học lại từ đầu.
Đây là tính chất thiết yếu với bài toán phát hiện khuôn mặt, nơi vị trí người trước camera thay đổi
liên tục.

**Trường tiếp nhận** (receptive field) của một giá trị đầu ra là vùng ảnh gốc thực sự ảnh hưởng tới nó.
Một lớp tích chập 3 × 3 cho trường tiếp nhận 3 × 3. Xếp chồng `L` lớp như vậy với bước nhảy bằng 1,
trường tiếp nhận mở rộng theo công thức:

```
RF = 1 + 2L
```

Hai lớp cho 5 × 5, ba lớp cho 7 × 7. Đây là lý do các mạng thị giác đi theo hướng **xếp nhiều lớp nhỏ**
thay vì dùng ít lớp có bộ lọc lớn: hai lớp 3 × 3 nhìn được vùng 5 × 5 nhưng chỉ tốn 18 trọng số mỗi
kênh, trong khi một lớp 5 × 5 tốn 25 trọng số mà lại thiếu một tầng phi tuyến ở giữa.

Cách tổ chức này cũng tạo ra **phân cấp đặc trưng**: lớp nông với trường tiếp nhận hẹp học các mẫu hình
đơn giản như cạnh và góc; lớp sâu với trường tiếp nhận rộng tổ hợp chúng thành bộ phận rồi thành đối
tượng hoàn chỉnh.

### 2.1.2. Hàm kích hoạt và lớp gộp

**Hàm kích hoạt** đưa tính phi tuyến vào mạng. Không có nó, một chuỗi lớp tích chập dù sâu đến đâu vẫn
tương đương một phép biến đổi tuyến tính duy nhất, và toàn bộ chiều sâu trở nên vô nghĩa. Hàm **ReLU**
giữ nguyên giá trị dương và đặt giá trị âm về không, được ưa chuộng nhờ chi phí tính toán gần như bằng
không và khả năng giảm hiện tượng tiêu biến gradient. Các kiến trúc gần đây thường dùng những hàm trơn
hơn như SiLU, đánh đổi một chút chi phí tính toán để lấy chất lượng hội tụ tốt hơn.

**Lớp gộp** (pooling) giảm độ phân giải không gian bằng cách thay mỗi vùng nhỏ — thường 2 × 2 — bằng
một giá trị đại diện, là giá trị lớn nhất hoặc giá trị trung bình của vùng đó. Việc này phục vụ ba mục
đích: giảm khối lượng tính toán cho các lớp phía sau, mở rộng nhanh trường tiếp nhận, và tạo mức bất
biến nhất định với những dịch chuyển nhỏ. Nhiều kiến trúc hiện đại thay lớp gộp bằng tích chập có bước
nhảy lớn hơn 1, đạt cùng hiệu quả giảm độ phân giải nhưng phép biến đổi có tham số học được thay vì cố
định.

### 2.1.3. Tích chập tách theo chiều sâu

Với ảnh đầu vào kích thước `H × W`, số kênh vào `C_in`, số kênh ra `C_out` và bộ lọc `k × k`, phép tích
chập thường có chi phí tính toán tỉ lệ với:

```
H × W × C_in × C_out × k²
```

Tích số `C_in × C_out` là phần tăng nhanh nhất khi mạng sâu dần, vì cả hai đều lớn ở các lớp phía sau.

**Tích chập tách theo chiều sâu** (depthwise separable convolution) tách phép toán trên thành hai bước
kế tiếp `[n]`:

1. **Tích chập theo chiều sâu** (depthwise): mỗi kênh vào được lọc độc lập bằng một bộ lọc `k × k`
   riêng, không trộn thông tin giữa các kênh. Chi phí: `H × W × C_in × k²`.
2. **Tích chập điểm** (pointwise): bộ lọc `1 × 1` trộn thông tin giữa các kênh và đổi số kênh từ
   `C_in` sang `C_out`. Chi phí: `H × W × C_in × C_out`.

Tỉ lệ chi phí so với tích chập thường là:

```
1/C_out + 1/k²
```

Với bộ lọc 3 × 3 và 256 kênh ra, tỉ lệ này xấp xỉ 0,115 — nghĩa là chi phí giảm khoảng **tám đến chín
lần**. Phần tiết kiệm đến từ việc tách bạch hai nhiệm vụ vốn bị gộp chung trong tích chập thường: lọc
theo không gian và trộn theo kênh. Cái giá phải trả là khả năng biểu diễn giảm, thường được bù lại bằng
cách tăng số lớp hoặc số kênh — vẫn rẻ hơn nhiều so với giữ nguyên tích chập thường.

Đây là nền tảng của họ kiến trúc MobileNet và các mạng dẫn xuất dành cho thiết bị di động `[n]`.

### 2.1.4. Hai con đường tới mạng nhẹ trong nghiên cứu này

Ba mô hình được sử dụng trong nghiên cứu này đều thuộc nhóm nhẹ, nhưng đạt được điều đó theo **hai con
đường khác nhau** — một điểm cần phân biệt rõ để tránh quy mọi kiến trúc hiệu quả về cùng một kỹ thuật.

**Con đường thứ nhất — thu nhỏ theo tỉ lệ.** YOLOv8n giữ nguyên tích chập thường trong toàn bộ mạng,
và đạt kích thước nhỏ bằng cách nhân chiều sâu và chiều rộng của kiến trúc gốc với các hệ số nhỏ hơn 1.
Cùng một thiết kế được phát hành ở nhiều mức quy mô, cho phép chọn điểm đánh đổi phù hợp với phần cứng
đích mà không phải thay đổi kiến trúc.

**Con đường thứ hai — thay đổi phép toán cơ sở.** MobileFaceNet và MiniFASNet dựa trên họ MobileNet,
sử dụng tích chập tách theo chiều sâu ở phần lớn khối tính toán `[n]`. Ở đây, tiết kiệm đến từ bản thân
phép toán chứ không từ việc giảm quy mô.

Hai con đường không loại trừ nhau và có thể kết hợp. Điểm chung là cả ba mô hình đều được thiết kế với
ràng buộc tài nguyên đặt ra ngay từ đầu, thay vì lấy một kiến trúc lớn rồi cắt gọt về sau — đặc điểm
quyết định tính khả thi của việc triển khai toàn bộ chuỗi xử lý trên một thiết bị nhúng đơn lẻ.

---

## 2.2. Phát hiện khuôn mặt — YOLOv8n-face

### 2.2.1. Bài toán và hai hướng kiến trúc

Phát hiện đối tượng (object detection) yêu cầu đồng thời hai việc trên một ảnh đầu vào: **định vị** —
xác định vị trí và kích thước của từng đối tượng bằng một khung bao (bounding box) — và **phân loại** —
gán nhãn lớp cho từng khung. Phát hiện khuôn mặt là trường hợp riêng với duy nhất một lớp cần phân
biệt, nên phần phân loại suy giảm thành bài toán xác định một vùng ảnh có chứa khuôn mặt hay không.

Các kiến trúc học sâu giải bài toán này chia thành hai hướng.

**Hướng hai giai đoạn** tách quá trình thành hai bước nối tiếp. Bước thứ nhất sinh ra một tập vùng đề
xuất (region proposal) có khả năng chứa đối tượng; bước thứ hai trích đặc trưng của từng vùng rồi phân
loại và tinh chỉnh toạ độ khung. Họ mô hình R-CNN, Fast R-CNN và Faster R-CNN thuộc hướng này `[n]`.
Việc dành riêng một giai đoạn để lọc vùng ứng viên cho phép bước sau tập trung tài nguyên vào số ít
vùng có triển vọng, nhờ đó độ chính xác thường cao hơn. Đổi lại, ảnh phải đi qua mạng nhiều lần và
số lượng vùng đề xuất thay đổi theo nội dung ảnh, khiến thời gian xử lý mỗi khung hình không ổn định.

**Hướng một giai đoạn** bỏ bước sinh vùng đề xuất. Mạng nhận toàn bộ ảnh, chia thành lưới ô, và tại mỗi
vị trí trên lưới dự đoán trực tiếp toạ độ khung cùng độ tin cậy trong **một lượt truyền xuôi duy nhất**.
Họ YOLO (You Only Look Once) và SSD là đại diện `[n]`. Do cấu trúc tính toán cố định, thời gian xử lý
mỗi khung hình gần như không đổi bất kể ảnh chứa bao nhiêu khuôn mặt — tính chất quan trọng đối với hệ
thống thời gian thực, nơi cần bảo đảm một ngưỡng tốc độ khung hình tối thiểu chứ không chỉ giá trị
trung bình.

Trước khi học sâu trở nên phổ biến, bài toán phát hiện khuôn mặt được giải bằng các phương pháp **xếp
tầng** (cascade): bộ phát hiện Viola-Jones dùng đặc trưng Haar kết hợp AdaBoost, hoặc HOG kết hợp SVM
`[n]`. Về sau, MTCNN đưa học sâu vào theo mô hình **đa giai đoạn** với ba mạng nối tiếp `[n]`. Điểm
chung của cả ba là chia bài toán thành nhiều bước lọc dần, mỗi bước loại bớt vùng ứng viên.

Như §1.3 đã chỉ ra, các công trình được khảo sát đều dừng lại ở nhóm phương pháp xếp tầng hoặc đa giai
đoạn. Nghiên cứu này lựa chọn hướng một giai đoạn, và §2.2.5 trình bày căn cứ của lựa chọn đó.

### 2.2.2. Kiến trúc YOLOv8 và biến thể nano

YOLOv8 gồm ba phần nối tiếp `[n]`.

**Backbone** trích xuất đặc trưng từ ảnh đầu vào qua một chuỗi khối tích chập, giảm dần độ phân giải
không gian và tăng dần số kênh đặc trưng. Kiến trúc dựa trên CSPDarknet với khối C2f, trong đó luồng
đặc trưng được tách đôi rồi hợp nhất trở lại nhằm giảm khối lượng tính toán mà vẫn giữ được đường
truyền gradient.

**Neck** hợp nhất đặc trưng giữa các mức độ phân giải khác nhau theo cấu trúc kim tự tháp đặc trưng
(PAN-FPN). Đặc trưng ở độ phân giải cao mang thông tin chi tiết phù hợp cho đối tượng nhỏ; đặc trưng ở
độ phân giải thấp mang ngữ nghĩa tổng quát phù hợp cho đối tượng lớn. Việc trộn hai chiều — từ sâu lên
nông và từ nông xuống sâu — cho phép mạng phát hiện tốt cả khuôn mặt ở gần lẫn ở xa camera.

**Head** sinh dự đoán tại ba mức tỉ lệ tương ứng với bước nhảy (stride) 8, 16 và 32 điểm ảnh. Với ảnh
đầu vào cạnh `S`, số vị trí dự đoán là tổng của ba lưới:

```
N = (S/8)² + (S/16)² + (S/32)²
```

Với `S = 320` được `N = 40² + 20² + 10² = 2 100` vị trí; với `S = 640` được `N = 8 400`. Head của
YOLOv8 có hai đặc điểm đáng chú ý: **tách nhánh** (decoupled) — nhánh dự đoán toạ độ và nhánh dự đoán
độ tin cậy dùng tham số riêng thay vì chung một lớp đầu ra; và **không dùng khung neo** (anchor-free) —
mạng dự đoán trực tiếp khoảng cách từ điểm lưới tới bốn cạnh khung thay vì hiệu chỉnh một tập khung neo
định sẵn. Việc bỏ khung neo loại được một nhóm siêu tham số vốn phải điều chỉnh theo phân bố kích thước
đối tượng của từng tập dữ liệu.

YOLOv8 phát hành ở năm biến thể `n`, `s`, `m`, `l`, `x`, khác nhau ở hệ số nhân chiều sâu và chiều rộng
mạng. Biến thể **`n` (nano)** nhỏ nhất, đánh đổi một phần độ chính xác để lấy tốc độ suy luận và dung
lượng bộ nhớ thấp nhất. Đây là biến thể phù hợp với thiết bị nhúng có tài nguyên hạn chế.

**YOLOv8n-face** là YOLOv8n được huấn luyện lại trên tập dữ liệu khuôn mặt quy mô lớn WIDER FACE, đồng
thời bổ sung nhánh dự đoán điểm mốc `[n]`. Mô hình chỉ có một lớp đối tượng duy nhất là `face`.

### 2.2.3. Đầu ra: khung bao, độ tin cậy và năm điểm mốc

Tại mỗi vị trí dự đoán, mô hình sinh ra một vectơ gồm ba nhóm giá trị:

| Nhóm | Số giá trị | Nội dung |
|---|---|---|
| Khung bao | 4 | Toạ độ tâm và kích thước `(cx, cy, w, h)` |
| Độ tin cậy | 1 | Xác suất vị trí này chứa khuôn mặt, thang `[0, 1]` |
| Điểm mốc | 15 | 5 điểm × 3 giá trị `(x, y, độ hiện rõ)` |

Năm điểm mốc theo thứ tự: **mắt trái, mắt phải, mũi, khoé miệng trái, khoé miệng phải**. Đây là bộ năm
điểm chuẩn được dùng rộng rãi trong các hệ thống nhận diện khuôn mặt, và cũng chính là bộ điểm mà bước
căn chỉnh ở §2.3 cần đến.

Việc mô hình phát hiện đồng thời sinh ra điểm mốc là một lợi thế thiết kế đáng kể. Nếu bộ phát hiện chỉ
trả về khung bao, hệ thống buộc phải bổ sung một mô hình định vị điểm mốc riêng chạy nối tiếp sau đó,
làm tăng cả độ trễ lẫn số lượng mô hình phải nạp vào bộ nhớ. Ở đây, một lượt truyền xuôi duy nhất cung
cấp đủ thông tin cho toàn bộ khâu tiền xử lý phía sau.

### 2.2.4. Khử khung trùng lặp bằng non-maximum suppression

Do dự đoán được sinh dày đặc tại mọi vị trí trên ba lưới, một khuôn mặt thường được nhiều vị trí lân
cận cùng phát hiện, tạo ra một cụm khung bao chồng lấn. Bước **non-maximum suppression (NMS)** rút cụm
này về một khung duy nhất.

Thuật toán trước hết loại bỏ mọi khung có độ tin cậy thấp hơn một ngưỡng cho trước, sau đó sắp xếp các
khung còn lại theo độ tin cậy giảm dần và lặp: giữ lại khung đứng đầu, loại bỏ mọi khung còn lại có
mức chồng lấn với nó vượt ngưỡng, rồi tiếp tục với khung kế tiếp cho tới khi hết danh sách.

Mức chồng lấn được đo bằng **tỉ số giao trên hợp** (Intersection over Union):

```
IoU(A, B) = diện tích(A ∩ B) / diện tích(A ∪ B)
```

Giá trị bằng 1 khi hai khung trùng khít, bằng 0 khi hai khung rời nhau. Như vậy khâu hậu xử lý chịu chi
phối của hai ngưỡng độc lập: **ngưỡng độ tin cậy** quyết định một dự đoán có được xét hay không, và
**ngưỡng IoU** quyết định hai khung có được coi là cùng một khuôn mặt hay không. Ngưỡng độ tin cậy đặt
thấp làm tăng số phát hiện sai; đặt cao làm bỏ sót khuôn mặt ở điều kiện khó. Ngưỡng IoU đặt thấp có
thể gộp nhầm hai người đứng sát nhau thành một; đặt cao khiến một khuôn mặt bị báo thành nhiều khung.

### 2.2.5. Lựa chọn của nghiên cứu này

**Bảng 2.x.** Đối chiếu các hướng phát hiện khuôn mặt theo ràng buộc triển khai của nghiên cứu

| Tiêu chí | Xếp tầng (Viola-Jones, HOG-SVM) | Đa giai đoạn (MTCNN) | Một giai đoạn (YOLOv8n-face) |
|---|---|---|---|
| Số lượt truyền xuôi | nhiều tầng lọc | ba mạng nối tiếp | **một** |
| Thời gian mỗi khung hình | thay đổi theo nội dung ảnh | thay đổi theo số ứng viên | **gần như cố định** |
| Điểm mốc khuôn mặt | không có | có | **có, cùng một lượt** |
| Độ bền với góc nghiêng và thiếu sáng | thấp | trung bình | **cao hơn** |
| Xuất sang định dạng suy luận nhẹ | không áp dụng | phức tạp do nhiều mạng | **một tệp đồ thị duy nhất** |

Nghiên cứu này chọn YOLOv8n-face dựa trên bốn căn cứ.

**Thứ nhất, tính ổn định của thời gian xử lý.** Chỉ tiêu cam kết đặt ra một ngưỡng tốc độ khung hình
tối thiểu chứ không phải giá trị trung bình. Kiến trúc một giai đoạn có khối lượng tính toán cố định
nên bảo đảm được ràng buộc dạng này, trong khi các hướng còn lại có thời gian xử lý phụ thuộc nội dung
ảnh.

**Thứ hai, điểm mốc được cung cấp sẵn.** Như §2.2.3 đã nêu, điều này loại bỏ một mô hình trung gian
khỏi chuỗi xử lý, tiết kiệm cả độ trễ lẫn bộ nhớ trên thiết bị.

**Thứ ba, khả năng xuất sang định dạng suy luận nhẹ.** Mô hình một giai đoạn là một đồ thị tính toán
liền mạch nên xuất sang ONNX không đòi hỏi xử lý đặc biệt. §2.6 trình bày vì sao bước chuyển
đổi này là điều kiện bắt buộc để triển khai trên Raspberry Pi 5.

**Thứ tư, lấp khoảng trống đã nêu ở §1.3.** Các công trình được khảo sát đều sử dụng phương pháp xếp
tầng hoặc đa giai đoạn. Việc áp dụng mô hình một giai đoạn hiện đại lên bài toán điều khiển thiết bị
gia đình trên thiết bị biên, kèm đo đạc định lượng trên phần cứng thật, chính là phần đóng góp mà
nghiên cứu này hướng tới.

> Kết quả đo tốc độ và độ chính xác thực tế của mô hình trên Raspberry Pi 5 được trình bày ở Chương 4.
> Chi tiết cấu hình xuất mô hình và thiết kế khối phát hiện thuộc Chương 3.

---

## 2.3. Trích xuất đặc trưng khuôn mặt

### 2.3.1. Từ ảnh khuôn mặt sang vectơ đặc trưng

Sau khi phát hiện và căn chỉnh, mỗi khuôn mặt trở thành một ảnh có kích thước chuẩn. Bước tiếp theo
biến ảnh đó thành một **vectơ đặc trưng** (embedding) — một dãy số có độ dài cố định, đóng vai trò
biểu diễn cô đọng cho danh tính.

Điều làm cho cách biểu diễn này hữu ích không nằm ở bản thân các con số, mà ở **cấu trúc của không
gian chứa chúng**: hai ảnh của cùng một người phải cho hai vectơ gần nhau, hai ảnh của hai người khác
nhau phải cho hai vectơ xa nhau. Khoảng cách trong không gian đặc trưng vì thế mang ý nghĩa ngữ nghĩa,
chứ không chỉ là chênh lệch điểm ảnh.

Điểm mấu chốt về mặt phương pháp là mô hình **không phải bộ phân loại theo danh tính**. Một bộ phân
loại có số lớp đầu ra cố định, nên thêm một người mới đồng nghĩa với việc phải huấn luyện lại. Mô hình
trích xuất đặc trưng thì ánh xạ ảnh sang không gian vectơ mà không cần biết trước tập danh tính; việc
nhận diện được thực hiện bằng cách so sánh khoảng cách ở §2.4.

Hệ quả trực tiếp cho hệ thống thực tế là quy trình **đăng ký** (enrollment), cần được phân biệt rõ với
huấn luyện:

| | Huấn luyện | Đăng ký |
|---|---|---|
| Việc phải làm | Cập nhật trọng số mô hình | Tính vectơ đặc trưng và lưu lại |
| Dữ liệu cần | Hàng nghìn ảnh, nhiều danh tính | Vài chục ảnh của một người |
| Thời gian | Hàng giờ, cần phần cứng chuyên dụng | Vài giây, chạy ngay trên thiết bị |
| Thêm người mới | Huấn luyện lại toàn bộ | Thêm một mục vào danh sách |

Nghiên cứu này sử dụng mô hình **đã huấn luyện sẵn** và chỉ thực hiện đăng ký. Đây vừa là ràng buộc
về tài nguyên, vừa là điều kiện để hệ thống có thể thêm người dùng mới ngay tại chỗ mà không cần
kết nối tới máy chủ bên ngoài.

Thao tác đăng ký thông thường lấy **trung bình** các vectơ đặc trưng của nhiều ảnh cùng một người,
với kỳ vọng phần dao động do góc chụp và ánh sáng sẽ triệt tiêu lẫn nhau, còn phần đặc trưng ổn định
của danh tính thì được giữ lại.

### 2.3.2. Phương án A — dlib với mạng ResNet 128 chiều

Thư viện **dlib** cung cấp một mô hình nhận diện khuôn mặt dựa trên kiến trúc ResNet thu gọn, sinh ra
vectơ đặc trưng **128 chiều** `[n]`. Mô hình được huấn luyện bằng **hàm mất mát bộ ba** (triplet loss):
mỗi mẫu huấn luyện gồm ba ảnh — một ảnh neo, một ảnh cùng danh tính, một ảnh khác danh tính — và hàm
mất mát ép khoảng cách tới ảnh cùng danh tính nhỏ hơn khoảng cách tới ảnh khác danh tính ít nhất một
biên độ cho trước.

Quy trình chuẩn của dlib dùng bộ **68 điểm mốc** để căn chỉnh khuôn mặt trước khi trích đặc trưng, khác
với bộ 5 điểm mốc mà §2.2 đã trình bày. Đây là một khác biệt cần lưu ý khi đưa hai phương án về cùng
một điều kiện so sánh; cách xử lý cụ thể thuộc phần thiết kế ở Chương 3.

Ưu điểm của phương án này là mức độ trưởng thành: thư viện ổn định lâu năm, tài liệu đầy đủ, và mô hình
được dùng rộng rãi làm mốc đối chiếu. Hạn chế nằm ở chỗ dlib là thư viện C++ có phần mở rộng Python,
cần biên dịch khi cài trên kiến trúc ARM, và số chiều đặc trưng thấp hơn giới hạn khả năng phân biệt
khi số danh tính tăng lên.

### 2.3.3. Phương án B — MobileFaceNet và hàm mất mát biên góc

**MobileFaceNet** là kiến trúc trích xuất đặc trưng thiết kế riêng cho thiết bị di động, dựa trên họ
MobileNet đã trình bày ở §2.1.3 `[n]`. Mô hình nhận ảnh 112 × 112 và sinh vectơ đặc trưng **512 chiều**.

Điểm khác biệt quan trọng nhất so với phương án A không nằm ở kiến trúc mà ở **hàm mất mát dùng khi
huấn luyện**. **ArcFace** (Additive Angular Margin Loss) xuất phát từ nhận xét rằng khi cả vectơ đặc
trưng lẫn vectơ trọng số của lớp cuối đều được chuẩn hoá về độ dài đơn vị, tích vô hướng giữa chúng
chính là **cosin của góc** giữa hai vectơ `[n]`. Bài toán phân loại khi đó quy về bài toán góc: mẫu
thuộc lớp nào thì góc tới vectơ đại diện của lớp đó phải nhỏ nhất.

Trên nền tảng đó, ArcFace cộng thêm một **biên góc** `m` vào góc của lớp đúng trước khi tính hàm mất
mát. Mô hình vì vậy không chỉ phải phân loại đúng, mà phải phân loại đúng **với một khoảng dư an
toàn**: góc tới lớp đúng phải nhỏ hơn góc tới mọi lớp khác ít nhất một lượng `m`. Kết quả là các vectơ
đặc trưng của cùng một danh tính co cụm chặt hơn, còn các cụm khác danh tính tách xa nhau hơn.

Ưu điểm của việc cộng biên trực tiếp vào **góc** thay vì vào tích vô hướng là biên độ giữ nguyên ý
nghĩa hình học trên toàn bộ mặt cầu đơn vị, không phụ thuộc vị trí của mẫu. Đây cũng chính là lý do
độ tương đồng cosin ở §2.4 là phép đo tự nhiên để so khớp các vectơ này — mô hình được huấn luyện
trong không gian góc thì nên được so khớp bằng phép đo góc.

So với triplet loss, ArcFace không đòi hỏi chiến lược chọn bộ ba khi huấn luyện — một khâu vốn nhạy
cảm và tốn công. Về phía triển khai, MobileFaceNet phát hành dưới dạng đồ thị tính toán nên xuất sang
ONNX theo đúng quy trình ở §2.6, không cần biên dịch thư viện riêng trên thiết bị đích.

### 2.3.4. Hai phương án được đặt ngang nhau

**Bảng 2.x.** Đối chiếu đặc điểm hai phương án trích xuất đặc trưng

| Tiêu chí | Phương án A — dlib | Phương án B — MobileFaceNet |
|---|---|---|
| Số chiều đặc trưng | 128 | 512 |
| Hàm mất mát khi huấn luyện | Triplet loss | ArcFace — biên góc cộng thêm |
| Kích thước ảnh đầu vào | theo quy ước của dlib | 112 × 112 |
| Căn chỉnh theo | 68 điểm mốc | 5 điểm mốc |
| Cách triển khai trên thiết bị | thư viện C++ và phần mở rộng Python | đồ thị ONNX |

Nghiên cứu này **không chọn trước phương án nào**. Cả hai được cài đặt sau cùng một interface, chạy
trên cùng cơ sở dữ liệu, cùng điều kiện ánh sáng và cùng phần cứng, rồi đối chiếu bằng số đo. Việc so
sánh định lượng hai phương án chính là một trong những đóng góp mà đề tài đặt ra, nên kết luận phải
đến từ Chương 4 chứ không từ đặc điểm kiến trúc trình bày ở đây.

---

## 2.4. Học đo lường và độ tương đồng cosine

### 2.4.1. Chuẩn hoá L2 và độ tương đồng cosine

Hai phép đo khoảng cách thông dụng trong không gian đặc trưng là **khoảng cách Euclid** — độ dài đoạn
thẳng nối hai điểm — và **độ tương đồng cosin** — cosin của góc giữa hai vectơ, nhận giá trị trong
đoạn `[-1, 1]`, bằng 1 khi hai vectơ cùng hướng.

Hai phép đo này không độc lập với nhau. Sau khi **chuẩn hoá L2** — chia mỗi vectơ cho độ dài của chính
nó để đưa về độ dài đơn vị — quan hệ giữa chúng là:

```
‖a − b‖² = ‖a‖² + ‖b‖² − 2·a·b = 2 − 2·cos(a, b)
```

Vế phải giảm đơn điệu theo `cos(a, b)`. Nghĩa là trên các vectơ đã chuẩn hoá, **sắp xếp theo khoảng
cách Euclid và sắp xếp theo độ tương đồng cosin cho cùng một thứ tự**, và một ngưỡng đặt trên phép đo
này luôn quy đổi được sang ngưỡng tương ứng trên phép đo kia.

Độ tương đồng cosin vẫn được ưa dùng vì ba lý do thực tế. Thứ nhất, giá trị bị chặn trong `[-1, 1]` nên
ngưỡng dễ diễn giải và dễ so sánh giữa các mô hình khác nhau. Thứ hai, phép đo bỏ qua độ dài vectơ,
vốn có thể dao động theo chất lượng ảnh mà không mang thông tin về danh tính. Thứ ba, như §2.3.3 đã
nêu, mô hình huấn luyện bằng ArcFace được tối ưu trực tiếp trong không gian góc, nên so khớp bằng phép
đo góc là nhất quán với cách mô hình được xây dựng.

### 2.4.2. Ngưỡng quyết định

Hệ thống so vectơ đặc trưng của khuôn mặt đang đứng trước camera với các vectơ đã đăng ký, lấy mục có
độ tương đồng cao nhất, rồi đối chiếu giá trị đó với một **ngưỡng quyết định**. Vượt ngưỡng thì kết
luận là người đã đăng ký; không vượt thì kết luận là người lạ.

Ngưỡng này là tham số quan trọng nhất của toàn khối nhận diện, và nó **không có giá trị đúng phổ quát**:
mỗi mô hình có phân bố độ tương đồng riêng, và mỗi điều kiện triển khai lại dịch chuyển phân bố đó.
Vì vậy ngưỡng phải được chốt từ số đo trên chính hệ thống đang xây dựng, theo quy trình quét ngưỡng ở
§2.4.4, chứ không lấy từ tài liệu của mô hình.

### 2.4.3. Tập đóng và tập mở

Đây là phân biệt quyết định cách đánh giá toàn bộ hệ thống.

**Bài toán tập đóng** (closed-set) giả định khuôn mặt đưa vào **chắc chắn** thuộc một trong những người
đã đăng ký. Nhiệm vụ chỉ là chọn đúng người trong danh sách. Chỉ số phù hợp là độ chính xác phân loại.

**Bài toán tập mở** (open-set) không có giả định đó. Khuôn mặt đưa vào có thể là người hoàn toàn xa lạ,
và hệ thống bắt buộc phải có khả năng trả lời **"không phải ai trong danh sách"**.

Hệ thống kiểm soát ra vào là bài toán tập mở. Người lạ đứng trước camera là tình huống thường xuyên
chứ không phải ngoại lệ, và nhận nhầm người lạ thành chủ nhà là **thất bại nghiêm trọng nhất** mà hệ
thống có thể mắc phải.

Hệ quả về mặt đánh giá: **độ chính xác trên tập người đã đăng ký không phản ánh được năng lực an ninh
của hệ thống.** Một hệ thống chấp nhận mọi khuôn mặt vẫn đạt độ chính xác tuyệt đối trên tập đóng,
trong khi hoàn toàn vô dụng về mặt an ninh. Đánh giá tập mở đòi hỏi một tập dữ liệu riêng gồm những
người **không** được đăng ký, và các chỉ số ở mục tiếp theo.

### 2.4.4. FAR, FRR, EER và đường cong ROC/DET

Với một ngưỡng cho trước, hệ thống có thể mắc hai loại lỗi:

| Chỉ số | Tên đầy đủ | Định nghĩa | Hậu quả |
|---|---|---|---|
| **FAR** | False Acceptance Rate | Tỉ lệ người **lạ** bị chấp nhận nhầm | Người ngoài vào được nhà |
| **FRR** | False Rejection Rate | Tỉ lệ người **đã đăng ký** bị từ chối nhầm | Chủ nhà không mở được cửa |

Hai loại lỗi này đánh đổi trực tiếp với nhau qua ngưỡng. Nâng ngưỡng lên làm hệ thống khắt khe hơn:
FAR giảm nhưng FRR tăng. Hạ ngưỡng xuống cho tác dụng ngược lại. Không tồn tại ngưỡng làm cả hai cùng
bằng không, trừ trường hợp hai phân bố tách biệt hoàn toàn.

Quét ngưỡng qua toàn dải giá trị và ghi lại cặp `(FAR, FRR)` tại mỗi điểm cho ta một đường cong. Vẽ
theo quy ước ROC hoặc DET, đường cong này mô tả **năng lực của mô hình một cách độc lập với ngưỡng** —
nhờ vậy có thể so sánh hai mô hình mà không bị lẫn với ảnh hưởng của việc chọn ngưỡng.

**EER** (Equal Error Rate) là giá trị chung của FAR và FRR tại điểm hai đường cắt nhau. Đây là một con
số tóm tắt tiện dụng để đối chiếu nhanh giữa các mô hình.

Tuy nhiên, **EER không phải điểm làm việc phù hợp cho hệ thống an ninh**. Nó coi hai loại lỗi có mức
thiệt hại ngang nhau, trong khi thực tế thì không: người lạ vào được nhà nghiêm trọng hơn hẳn việc chủ
nhà phải thử lại lần thứ hai. Cách chọn ngưỡng đúng với bài toán này là **ấn định một mức FAR chấp nhận
được rồi đọc FRR tương ứng**, thay vì lấy điểm cân bằng.

Cuối cùng, độ tin cậy của con số FAR phụ thuộc trực tiếp vào **số lượng phép thử** trên tập người lạ.
Một tập người lạ quá nhỏ chỉ cho phép kết luận về FAR ở mức thô, bất kể kết quả đo có đẹp đến đâu.
Thiết kế tập dữ liệu người lạ và cỡ mẫu cần thiết được trình bày ở Chương 4 cùng với kết quả đo.

---

## 2.5. Phát hiện giả mạo (liveness detection)

### 2.5.1. Bài toán và phân loại tấn công trình diện

Hệ thống nhận diện khuôn mặt chỉ so khớp đặc trưng sinh trắc học mà không tự phân biệt được nguồn gốc
của khuôn mặt trong khung hình. Một bức ảnh in hoặc màn hình điện thoại hiển thị ảnh người đã đăng ký
vẫn tạo ra vectơ đặc trưng gần như trùng khớp với người thật. Khối phát hiện giả mạo (anti-spoofing,
hay liveness detection) có nhiệm vụ trả lời câu hỏi độc lập: khuôn mặt đang xuất hiện là **người thật
hiện diện trước camera** hay là một bản sao.

Tiêu chuẩn ISO/IEC 30107-3 gọi các hình thức này là **tấn công trình diện** (presentation attack) và
phân loại theo phương tiện tấn công `[n]`:

| Nhóm | Phương tiện | Trong phạm vi nghiên cứu này |
|---|---|---|
| Tấn công 2D — in | Ảnh in trên giấy, có thể cắt lỗ mắt | **Có** |
| Tấn công 2D — phát lại | Ảnh hoặc video hiển thị trên màn hình điện thoại, máy tính bảng | **Có** |
| Tấn công 3D | Mặt nạ silicon, mô hình đầu 3D | Không |
| Tấn công số | Video giả mạo tổng hợp (deepfake) đưa trực tiếp vào luồng dữ liệu | Không |

Nghiên cứu này giới hạn ở hai nhóm tấn công 2D. Đây là hai hình thức có chi phí thực hiện thấp nhất —
chỉ cần một bức ảnh của chủ nhà — nên cũng là mối đe doạ thực tế nhất đối với hệ thống trong hộ gia
đình. Hai nhóm còn lại đòi hỏi chi phí và điều kiện tiếp cận cao hơn nhiều, nằm ngoài mô hình đe doạ
được xét.

### 2.5.2. Hai hướng tiếp cận

**Hướng thứ nhất — phân loại nhị phân trên đặc trưng kết cấu.** Mô hình nhận ảnh khuôn mặt đã cắt và
đưa ra một điểm số thật/giả. Cơ sở nhận biết nằm ở dấu vết mà quá trình tái tạo để lại: mạng lưới điểm
mực của ảnh in, vân lưới điểm ảnh và hiện tượng moiré của màn hình, phản xạ ánh sáng bất thường trên
bề mặt phẳng, mất chi tiết tần số cao do đã qua một vòng chụp lại. Ưu điểm là kiến trúc gọn và chi phí
suy luận thấp; hạn chế là mô hình dễ học vào đặc thù của thiết bị và điều kiện chụp trong tập huấn
luyện, nên khả năng khái quát hoá sang miền dữ liệu mới thường giảm.

**MiniFASNet**, thuộc dự án Silent Face Anti-Spoofing, là đại diện của hướng này `[n]`. Mô hình dùng
kiến trúc nhẹ kiểu MobileNet với ảnh đầu vào kích thước nhỏ, xử lý toàn bộ trên một khung hình đơn
mà không cần chuỗi thời gian hay tương tác từ người dùng.

**Hướng thứ hai — giám sát theo điểm ảnh.** Thay vì huấn luyện mô hình đưa ra một nhãn nhị phân, hướng
này buộc mạng dự đoán một bản đồ có ý nghĩa vật lý — thường là **bản đồ độ sâu** của khuôn mặt. Trực
giác đứng sau: khuôn mặt thật là một bề mặt ba chiều nên bản đồ độ sâu có cấu trúc lồi lõm, còn ảnh in
hay màn hình là mặt phẳng nên bản đồ độ sâu gần như phẳng đều. Tín hiệu giám sát dày đặc theo từng
điểm ảnh cung cấp nhiều thông tin hơn một nhãn nhị phân, giúp mô hình khái quát hoá tốt hơn.

**CDCN** (Central Difference Convolutional Network) là công trình tiêu biểu của hướng này `[n]`. Đóng
góp cốt lõi là **tích chập sai phân trung tâm**: bên cạnh tổng có trọng số như tích chập thông thường,
phép toán cộng thêm thành phần chênh lệch giữa các điểm lân cận và điểm trung tâm, với tham số `θ`
điều tiết mức đóng góp của thành phần gradient. Cơ sở của thiết kế này là dấu vết giả mạo thể hiện ở
**biến thiên cục bộ của cường độ** rõ hơn ở giá trị cường độ tuyệt đối. Mạng nhận ảnh 3 × 256 × 256 và
dự đoán bản đồ độ sâu mức xám 32 × 32, huấn luyện bằng tổ hợp sai số bình phương trung bình và hàm mất
mát độ sâu tương phản. Phiên bản mở rộng CDCN++ bổ sung backbone tìm bằng tìm kiếm kiến trúc tự động
và khối hợp nhất chú ý đa tỉ lệ, đạt thứ hạng cao tại các cuộc thi phát hiện tấn công trình diện.

### 2.5.3. Lựa chọn của nghiên cứu này

**Bảng 2.x.** Đối chiếu hai hướng tiếp cận theo ràng buộc triển khai của nghiên cứu

| Tiêu chí | MiniFASNet | CDCN |
|---|---|---|
| Hướng tiếp cận | Phân loại nhị phân trên kết cấu | Giám sát theo điểm ảnh, bản đồ độ sâu |
| Kích thước ảnh đầu vào | 80 × 80 | **256 × 256** — gấp khoảng 10 lần số điểm ảnh |
| Đầu ra | Điểm số phân lớp | Bản đồ độ sâu 32 × 32, cần hậu xử lý |
| Trọng số huấn luyện sẵn | **Có, do nhóm tác giả phát hành** | **Không công bố trong công trình gốc** |
| Định dạng triển khai | Có bản ONNX sẵn | Mã nguồn nghiên cứu, PyTorch |
| Độ chính xác trên bộ chuẩn | Thấp hơn | **Cao hơn** |
| Khái quát hoá chéo bộ dữ liệu | Yếu hơn | **Tốt hơn** |

*Nguồn: tổng hợp từ tài liệu `[n]`, `[n]`. Các đánh giá về độ chính xác là kết quả công bố của các
công trình tương ứng, không phải kết quả đo của nghiên cứu này.*

Nghiên cứu này lựa chọn **MiniFASNet**. Lý do xếp theo mức quyết định:

1. **Ràng buộc về trọng số huấn luyện sẵn.** Phạm vi nghiên cứu loại trừ việc huấn luyện lại mô hình,
   do đó chỉ những mô hình có trọng số được phát hành mới sử dụng được. Công trình CDCN gốc không công
   bố trọng số; các bản cài đặt lại của bên thứ ba không được nhóm tác giả xác nhận và không có số liệu
   chuẩn để đối chiếu.
2. **Ràng buộc tài nguyên tính toán.** Hệ thống đặt chỉ tiêu tốc độ xử lý toàn luồng, trong đó khối
   phát hiện giả mạo chỉ chiếm một phần nhỏ ngân sách mỗi khung hình. Chênh lệch khoảng mười lần về số
   điểm ảnh đầu vào, cộng với chi phí cao hơn của phép tích chập sai phân, khiến CDCN khó khả thi trên
   nền tảng đã chọn.
3. **Phạm vi tấn công được xét.** Ưu thế của hướng giám sát theo độ sâu thể hiện rõ nhất khi cần khái
   quát hoá sang nhiều loại tấn công và nhiều miền dữ liệu. Nghiên cứu này giới hạn ở hai hình thức
   tấn công 2D trong một môi trường sử dụng cố định, nên phần năng lực vượt trội đó không được khai
   thác tương xứng với chi phí phải trả.

Đây là lựa chọn có đánh đổi được nêu rõ, không phải khẳng định MiniFASNet tốt hơn CDCN. Trong điều kiện
không bị ràng buộc về tài nguyên và có sẵn trọng số, hướng giám sát theo điểm ảnh là lựa chọn mạnh hơn.

### 2.5.4. Chỉ số đánh giá theo ISO/IEC 30107-3

Đánh giá hệ thống phát hiện tấn công trình diện dùng ba chỉ số chuẩn hoá `[n]`:

| Chỉ số | Định nghĩa | Ý nghĩa |
|---|---|---|
| **APCER** | Tỉ lệ mẫu tấn công bị phân loại nhầm thành mẫu thật | Tấn công lọt qua hệ thống |
| **BPCER** | Tỉ lệ mẫu thật bị phân loại nhầm thành tấn công | Người dùng hợp lệ bị từ chối |
| **ACER** | Trung bình cộng của APCER và BPCER | Chỉ số tổng hợp |

APCER phải được **báo cáo tách riêng cho từng loại tấn công** rồi lấy giá trị lớn nhất, vì một hệ thống
có thể chặn tốt ảnh in nhưng yếu trước màn hình. Chỉ tiêu "phát hiện tối thiểu 90 % tấn công" của nghiên
cứu này tương đương APCER ≤ 10 %.

Đối với hệ thống điều khiển thiết bị trong hộ gia đình, **APCER được ưu tiên hơn BPCER**: một lần tấn
công lọt qua cấp quyền điều khiển thiết bị điện cho người lạ, trong khi một lần từ chối nhầm chỉ gây
bất tiện và người dùng có thể thử lại.

---

## 2.6. Suy luận trên thiết bị biên

### 2.6.1. Vì sao không dùng khung học sâu đầy đủ trên thiết bị đích

Các khung học sâu như PyTorch hay TensorFlow được thiết kế cho cả **huấn luyện** lẫn **suy luận**. Để
phục vụ huấn luyện, chúng phải mang theo cơ chế tự động tính đạo hàm, bộ tối ưu, khả năng xây đồ thị
động thay đổi theo từng lượt chạy, cùng hệ thống thư viện toán học đi kèm. Trên máy phát triển, chi phí
này không đáng kể. Trên thiết bị biên, nó trở thành gánh nặng ở ba khía cạnh.

**Dung lượng cài đặt.** Một bản PyTorch đầy đủ chiếm hàng trăm megabyte đến vài gigabyte tuỳ cấu hình,
trong khi thẻ nhớ của thiết bị nhúng còn phải chứa hệ điều hành, cơ sở dữ liệu và dữ liệu vận hành.

**Bộ nhớ khi chạy.** Raspberry Pi 5 có 8 GB RAM dùng chung cho toàn bộ hệ thống, bao gồm cả khối web
giám sát, cơ sở dữ liệu và các mô hình khác trong chuỗi xử lý. Phần bộ nhớ mà một khung đầy đủ chiếm
giữ chỉ để phục vụ suy luận là phần bị lãng phí.

**Tính sẵn sàng trên kiến trúc ARM.** Nhiều gói phụ thuộc không có bản dựng sẵn cho ARM64, buộc phải
biên dịch từ mã nguồn — quá trình tốn thời gian và dễ hỏng khi nâng cấp.

Vì suy luận không cần tính đạo hàm và cũng không cần đồ thị động, cách làm hợp lý là **tách rời hai
giai đoạn**: huấn luyện và xuất mô hình thực hiện trên máy phát triển, còn thiết bị đích chỉ cài một
bộ chạy suy luận gọn nhẹ.

### 2.6.2. Đồ thị tính toán và định dạng ONNX

Một mạng nơ-ron sau khi huấn luyện xong có thể biểu diễn dưới dạng **đồ thị tính toán** (computation
graph): các nút là phép toán (tích chập, chuẩn hoá, hàm kích hoạt), các cạnh là luồng dữ liệu, còn
trọng số đã học là hằng số gắn kèm.

**ONNX** (Open Neural Network Exchange) là định dạng mở để lưu đồ thị này cùng trọng số `[n]`. Vai trò
của nó là tách **nơi huấn luyện** khỏi **nơi chạy**: mô hình huấn luyện bằng PyTorch xuất ra ONNX rồi
chạy bằng bất kỳ bộ suy luận nào hỗ trợ định dạng, không cần PyTorch hiện diện trên thiết bị đích.

Quá trình xuất mô hình thực hiện hai việc. Thứ nhất là **đóng băng đồ thị**: mọi nhánh điều kiện phụ
thuộc dữ liệu được giải quyết, đồ thị trở thành cố định. Thứ hai là **hợp nhất phép toán** (operator
fusion): các phép liên tiếp có thể gộp được — chẳng hạn tích chập, chuẩn hoá theo lô và hàm kích hoạt —
được nhập thành một nút duy nhất, giảm số lần đọc ghi bộ nhớ trung gian.

Việc đóng băng đồ thị kéo theo một hệ quả thiết kế cần lưu ý: **kích thước ảnh đầu vào bị cố định ngay
tại thời điểm xuất**. Muốn chạy mô hình ở nhiều độ phân giải khác nhau thì phải xuất sẵn nhiều tệp
tương ứng, không thể đổi kích thước lúc chạy.

Phiên bản tập toán tử (opset) cũng cần cân nhắc. Opset mới hỗ trợ nhiều phép toán hơn nhưng đòi hỏi bộ
suy luận đủ mới; chọn opset thấp hơn đổi lấy khả năng tương thích rộng hơn với các runtime cũ có sẵn
trên thiết bị nhúng.

### 2.6.3. ONNX Runtime

**ONNX Runtime** là bộ suy luận đa nền tảng do Microsoft phát triển, nhận trực tiếp tệp ONNX `[n]`.
Kiến trúc của nó dựa trên khái niệm **execution provider** — lớp trừu tượng ánh xạ các nút của đồ thị
xuống phần cứng cụ thể. Trên Raspberry Pi 5 không có GPU đa dụng nên toàn bộ đồ thị chạy qua execution
provider dành cho CPU, vốn được tối ưu bằng tập lệnh vectơ NEON của kiến trúc ARM.

Đây là bộ suy luận duy nhất được cài trên thiết bị đích trong nghiên cứu này. Việc giới hạn số lượng
thư viện phía thiết bị là lựa chọn có chủ đích: mỗi thư viện bổ sung đều kéo theo dung lượng, bộ nhớ
và rủi ro tương thích khi nâng cấp hệ điều hành.

> `[CHƯA VIẾT — CHẶN VÌ CHƯA ĐO]` — đối chiếu với bộ suy luận thứ hai (NCNN).
>
> Đề cương đặt ra việc so sánh ONNX Runtime với một bộ suy luận khác chuyên cho thiết bị nhúng.
> Phần này **chưa viết** vì nghiên cứu chưa chạy bộ suy luận đó lần nào. Mọi mô tả về ưu thế tốc độ
> hay dung lượng của nó lúc này sẽ chỉ là chép lại tài liệu quảng bá của nhà phát triển, không phải
> điều đã kiểm chứng — trong khi chính điểm cần trả lời là **hơn kém bao nhiêu trên phần cứng cụ
> thể của đồ án**.
>
> **Điều kiện gỡ chặn**: có Raspberry Pi 5, xuất được mô hình sang định dạng thứ hai, và đo xong
> trên cùng kịch bản với ONNX Runtime. Khi đó mục này viết cùng lượt với bảng đối chiếu ở Chương 4.

### 2.6.4. Lượng tử hoá và cấu hình số luồng

**Lượng tử hoá** (quantization) hạ độ chính xác biểu diễn của trọng số và giá trị trung gian, phổ biến
nhất là từ số thực 32 bit xuống số nguyên 8 bit. Mô hình thu nhỏ khoảng bốn lần, và phép toán số nguyên
chạy nhanh hơn trên CPU không có đơn vị dấu phẩy động mạnh. Cái giá phải trả là sai số biểu diễn, làm
độ chính xác giảm ở mức độ phụ thuộc vào từng mô hình. Với hệ thống an ninh, mức suy giảm này phải được
đo trước khi chấp nhận chứ không thể giả định là không đáng kể.

**Số luồng** là tham số điều chỉnh trực tiếp ở phía bộ suy luận. Raspberry Pi 5 có bộ xử lý bốn nhân,
nên về lý thuyết tăng số luồng sẽ rút ngắn thời gian mỗi khung hình. Trên thực tế, hiệu quả không tăng
tuyến tính: chi phí đồng bộ giữa các luồng và giới hạn băng thông bộ nhớ khiến mức cải thiện giảm dần,
và khi các khối khác của hệ thống cũng cần CPU thì việc chiếm hết số nhân cho một khối có thể làm giảm
hiệu năng tổng thể. Đây là lý do số luồng được đưa vào ma trận đo ở Chương 4 thay vì ấn định sẵn.

> Cấu hình xuất mô hình và thiết kế khối suy luận thuộc Chương 3. Số liệu đo trên phần cứng thật,
> gồm đối chiếu giữa các độ phân giải và số luồng, thuộc Chương 4.

---

## 2.7. Điều khiển thiết bị — GPIO và hồng ngoại

`[CHƯA VIẾT — CHẶN VÌ CHƯA CÓ PHẦN CỨNG]`

Dàn ý: chân GPIO trên Raspberry Pi 5 · module relay và cách ly quang · giao thức điều khiển hồng
ngoại, mã hoá NEC · nguyên tắc an toàn khi thao tác điện.

> ⛔ **Không viết mục này cho tới khi có Raspberry Pi 5 trong tay.** Lý do không phải là thiếu tài
> liệu, mà là tài liệu phổ biến **sai với phần cứng của đồ án**.
>
> Pi 5 dùng chip vào-ra mới **RP1**, khiến thư viện `RPi.GPIO` — thư viện xuất hiện trong hầu hết
> hướng dẫn GPIO trên mạng — **không hoạt động**, do nó truy cập thanh ghi qua `/dev/mem` trong khi
> thanh ghi GPIO nay nằm ở RP1 chứ không ở bộ xử lý chính `[n]`. Các lựa chọn thay thế
> (`rpi-lgpio`, `gpiozero`, `libgpiod`, `lgpio`) đều dùng được nhưng có ràng buộc riêng; đã có
> trường hợp `gpiozero` hỏng trên Pi 5 vì gán cứng số hiệu `gpiochip` không khớp với bản nhân
> Linux đang chạy `[n]`.
>
> Nghĩa là lựa chọn đúng **phụ thuộc phiên bản hệ điều hành và nhân Linux cụ thể trên thiết bị**.
> Viết mục này từ tài liệu trên mạng gần như chắc chắn sẽ mô tả một thư viện mà hệ thống không dùng
> — lỗi không chống đỡ được khi bảo vệ.
>
> Tương tự với phần hồng ngoại: giao thức NEC là kiến thức chuẩn có thể trích dẫn, nhưng mã lệnh
> thực tế của remote tivi phải ghi lại từ thiết bị thật (bước 5.3), và cách phát mã phụ thuộc thư
> viện chạy được trên Pi 5.
>
> **Điều kiện gỡ chặn**: có Pi 5, cài xong hệ điều hành, xác định được thư viện GPIO thực sự chạy
> trên bản nhân đang dùng. Ghi nhận vào `docs/dieu-chinh-pham-vi.md` nếu tới hạn vẫn chưa có.

---

## Checklist hoàn thành Chương 2

- [ ] Mọi mục không còn `[CHƯA VIẾT]`
- [ ] Chương trình bày **phương pháp**, không lẫn kết quả đo của nghiên cứu này
- [ ] Số liệu của công trình khác đều kèm trích dẫn và nói rõ là kết quả của họ
- [ ] Thuật ngữ tiếng Anh lần đầu ghi kèm tiếng Việt, các lần sau dùng nhất quán
- [ ] §2.2 nối lại được với khoảng trống đã nêu ở §1.3
- [ ] §2.3 trình bày **cả hai** phương án nhận diện, không thiên vị bên nào trước khi có số đo
- [ ] Mọi `[n]` đã thay bằng số trích dẫn thật, có mục trong `refs.bib`
- [ ] Không dùng ngôi thứ nhất
- [ ] Độ dài ~11 trang
