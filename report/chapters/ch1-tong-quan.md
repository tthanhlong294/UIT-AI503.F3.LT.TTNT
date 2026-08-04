# Chương 1 — Tổng quan

> **Đây là khung làm việc, chưa phải bản thảo.** Mọi mục còn `[CHƯA VIẾT]` là chỗ cần điền.
> Ngân sách: **~7 trang**.
> §1.2 phân tích sâu **4 công trình: 2 nước ngoài + 2 trong nước** (bài báo hoặc đồ án/luận văn).
> Các trích dẫn nền (ArcFace, LFW, YOLO, tiêu chuẩn…) không tính vào 4 công trình này —
> chúng nằm ở §1.1 và Chương 2.
>
> Quy ước: không viết câu nào có số liệu mà chưa có nguồn. Chưa có → để `[CHƯA ĐO]` (`CLAUDE.md` R5).
>
> Thứ tự viết khuyến nghị: **§1.2 → §1.3 → §1.1 → §1.4 → §1.5**.
> Bắt đầu từ khảo sát vì mọi mục khác đều dựa vào kết quả đọc tài liệu.

---

## 1.1. Bối cảnh — nhà thông minh và trí tuệ nhân tạo biên

#### 1.1.1. Nhu cầu xác thực sinh trắc học trong nhà thông minh

Xu hướng phát triển của nhà thông minh (smart home) đang dịch chuyển từ điều khiển thủ công thông qua
ứng dụng di động sang hướng cá nhân hoá thụ động, trong đó hệ thống tự nhận biết người dùng và kích
hoạt kịch bản tương ứng — điều chỉnh chiếu sáng, nhiệt độ hay thiết bị giải trí — mà không cần thao
tác chủ động. Xác thực bằng đặc trưng sinh trắc học, đặc biệt là nhận diện khuôn mặt, đóng vai trò
then chốt cho hướng phát triển này. Khác với mật khẩu hoặc thẻ từ, đặc trưng sinh trắc học không cần
mang theo, không thể bị bỏ quên, và cho phép quá trình xác thực diễn ra liên tục trong nền thay vì
tại một thao tác rời rạc.

Hướng ứng dụng này đã xuất hiện trong các nghiên cứu gần đây. Zamir và cộng sự [1] xây dựng hệ thống
nhận diện khuôn mặt chi phí thấp trên máy tính nhúng với mục tiêu ứng dụng cho giám sát nhà thông minh
và các hệ thống dựa trên Internet vạn vật. Phan Nguyễn Quốc Bảo và Hoàng Công Minh [3] tích hợp nhận
diện khuôn mặt như một kênh xác thực trong hệ thống điều khiển thiết bị gia đình, bên cạnh các kênh
điều khiển bằng giao diện web và cử chỉ tay. Cả hai công trình được phân tích chi tiết ở mục 1.2.

#### 1.1.2. Hạn chế của mô hình xử lý trên đám mây

Phần lớn giải pháp nhận diện khuôn mặt thương mại hiện nay thực hiện xử lý trên máy chủ đám mây
(cloud). Mô hình này bộc lộ hai nhóm hạn chế.

Về mặt kỹ thuật, việc truyền ảnh lên máy chủ và chờ kết quả trả về làm tăng độ trễ của toàn bộ chu
trình xác thực, đồng thời khiến hệ thống phụ thuộc vào chất lượng kết nối Internet: khi đường truyền
gián đoạn, chức năng xác thực ngừng hoạt động. Đối với hệ thống điều khiển thiết bị trong nhà, cả hai
hạn chế đều ảnh hưởng trực tiếp tới khả năng sử dụng.

Về mặt pháp lý và quyền riêng tư, Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân xếp dữ liệu sinh
trắc học — trong đó có đặc điểm khuôn mặt — vào nhóm **dữ liệu cá nhân nhạy cảm**, đòi hỏi các điều
kiện chặt chẽ hơn về sự đồng ý của chủ thể, về lưu trữ và về chuyển giao cho bên thứ ba `[n]`. Việc
thiết bị thu hình đặt trong không gian sinh hoạt gia đình liên tục truyền hình ảnh tới hạ tầng của
bên thứ ba làm mở rộng đáng kể bề mặt rủi ro: dữ liệu nhạy cảm được lưu trữ ngoài tầm kiểm soát trực
tiếp của chủ thể, và mỗi khâu truyền tải hoặc lưu trữ trung gian đều là một điểm có khả năng lộ lọt.

#### 1.1.3. Trí tuệ nhân tạo biên

Trí tuệ nhân tạo biên (edge AI) là hướng tiếp cận đưa toàn bộ quá trình suy luận về thực hiện tại
thiết bị đầu cuối, thay vì gửi dữ liệu tới máy chủ tập trung. Đối với bài toán nhận diện khuôn mặt
trong hộ gia đình, hướng này mang lại hai lợi ích tương ứng với hai hạn chế nêu trên: độ trễ chỉ còn
phụ thuộc vào năng lực tính toán của thiết bị chứ không phụ thuộc đường truyền, và hệ thống vẫn vận
hành khi mất kết nối Internet. Quan trọng hơn, dữ liệu hình ảnh thô không rời khỏi thiết bị; hệ thống
chỉ lưu trữ vectơ đặc trưng (embedding) phục vụ đối sánh.

Cần nêu rõ rằng xử lý cục bộ **làm giảm rủi ro lộ lọt chứ không miễn trừ nghĩa vụ pháp lý**. Vectơ
đặc trưng sinh trắc học vẫn là dữ liệu cá nhân nhạy cảm, và việc thu thập ảnh khuôn mặt vẫn đòi hỏi
sự đồng ý của chủ thể theo Nghị định 13/2023/NĐ-CP. Nghiên cứu này tuân thủ yêu cầu đó: toàn bộ dữ
liệu khuôn mặt sử dụng trong thực nghiệm đều được thu thập từ những người đã được thông báo rõ mục
đích và đồng ý tham gia, như trình bày ở phần đạo đức nghiên cứu.

#### 1.1.4. Raspberry Pi 5 làm nền tảng triển khai

Raspberry Pi 5 là một trong những máy tính đơn bo mạch (single-board computer) phổ biến để xây dựng
các hệ thống trí tuệ nhân tạo biên chi phí thấp. Thiết bị sử dụng vi xử lý Broadcom BCM2712 với bốn
nhân ARM Cortex-A76 hoạt động ở tần số 2,4 GHz, và bổ sung cổng PCIe 2.0 x1 cho phép kết nối thiết bị
mở rộng — bao gồm cả các bộ tăng tốc suy luận chuyên dụng `[n]`.

Tuy nhiên, năng lực của nền tảng này cần được đánh giá đúng mức. Raspberry Pi 5 **không tích hợp bộ
xử lý thần kinh chuyên dụng** (Neural Processing Unit — NPU), nên toàn bộ khối lượng tính toán của mô
hình học sâu dồn lên CPU. Hệ quả là hiệu năng suy luận phụ thuộc mạnh vào độ phức tạp của mô hình và
độ phân giải ảnh đầu vào; khi tải tính toán kéo dài, thiết bị có thể đạt ngưỡng nhiệt và tự động giảm
xung nhịp (thermal throttling), làm sụt giảm hiệu năng. Việc trang bị tản nhiệt chủ động do đó là điều
kiện cần để duy trì hiệu năng ổn định trong vận hành liên tục.

Những ràng buộc này định hình các lựa chọn kỹ thuật của nghiên cứu: ưu tiên mô hình nhẹ, tối ưu định
dạng suy luận cho kiến trúc ARM, và đo đạc hiệu năng kèm điều kiện nhiệt độ thực tế thay vì dựa vào
thông số danh nghĩa. Kết quả đo cụ thể trên phần cứng triển khai được trình bày ở Chương 4.

> 🖉 **Ghi chú soạn thảo — xoá trước khi nộp**
>
> 1. Còn **hai** vị trí `[n]` cần bổ sung trích dẫn: (a) Nghị định 13/2023/NĐ-CP — trích bản gốc trên
>    Cổng thông tin điện tử Chính phủ, (b) thông số Raspberry Pi 5 — trích tài liệu chính thức của
>    Raspberry Pi Ltd. Mẫu định dạng cho cả hai đã có sẵn trong `report/refs.bib`.
> 1b. **Đánh số trích dẫn**: bản nháp Markdown đang dùng số theo thứ tự khảo sát ở §1.2 ([1]–[4]).
>    Khi chuyển sang LaTeX, thay bằng `\cite{khoá}` và để BibTeX tự đánh số theo thứ tự xuất hiện —
>    không sửa số bằng tay, vì thứ tự sẽ còn đổi khi viết các chương sau.
> 2. **Đã lược bỏ có chủ ý** con số "10–15 FPS cho mô hình nhẹ trên Pi 5" trong bản viết tay.
>    Lý do: chưa có nguồn, và nếu Chương 1 khẳng định 10–15 FPS trong khi Chương 4 đo ra thấp hơn thì
>    báo cáo tự mâu thuẫn. Muốn giữ thì phải có trích dẫn cụ thể, hoặc dời sang Chương 4 dưới dạng
>    số đo thật.
> 3. Câu "giải quyết triệt để lo ngại về Nghị định 13" đã sửa thành "làm giảm rủi ro lộ lọt chứ không
>    miễn trừ nghĩa vụ pháp lý" — xem giải thích ở phần trao đổi.
> 4. Đề cập Google Coral Edge TPU / Hailo-8L đã chuyển khỏi mục này; thuộc **Chương 5 §Hướng phát
>    triển**, vì nằm ngoài phạm vi đề cương.

---

## 1.2. Khảo sát công trình liên quan ⭐

Nghiên cứu này khảo sát bốn công trình tiêu biểu về nhận diện khuôn mặt trên thiết bị nhúng, gồm
hai công trình quốc tế và hai công trình trong nước. Tiêu chí lựa chọn là các nghiên cứu có triển
khai và đo đạc trên phần cứng tài nguyên hạn chế thực tế, thay vì chỉ đánh giá trên máy tính hiệu
năng cao. Bảng 1.1 ở cuối mục tổng hợp đối chiếu phạm vi của bốn công trình này với nghiên cứu hiện tại.

#### 1.2.1. Các công trình quốc tế

Zamir và cộng sự [1] đề xuất một hệ thống phát hiện và nhận diện khuôn mặt chi phí thấp trên
Raspberry Pi, hướng tới các ứng dụng Internet vạn vật (Internet of Things — IoT) như giám sát nhà
thông minh. Nghiên cứu đối chiếu hai hướng trích xuất đặc trưng: biểu đồ gradient có hướng
(Histogram of Oriented Gradients — HOG) và mạng nơ-ron tích chập (Convolutional Neural Network — CNN)
kết hợp kiến trúc ResNet, cài đặt thông qua thư viện dlib và OpenCV. Kết quả cho thấy hướng tiếp cận
CNN đạt độ chính xác từ 89,5 % đến 98,6 % trên bốn bộ dữ liệu, trong đó có một bộ tự thu thập gồm
700 ảnh của 7 danh tính; với dữ liệu video, CNN đạt 98 % so với khoảng 59–84 % của HOG. Nghiên cứu
cũng kiểm chứng khả năng nhận diện trong trường hợp đối tượng đeo khẩu trang.

Công trình tập trung so sánh độ chính xác giữa hai hướng trích xuất đặc trưng và không công bố tốc độ
khung hình đạt được trên Raspberry Pi — thông số quyết định tính khả thi của một hệ thống thời gian
thực. Phạm vi nghiên cứu dừng ở nhận diện, chưa bao gồm cơ chế phát hiện giả mạo (anti-spoofing)
lẫn khối điều khiển thiết bị.

Mohammad và cộng sự [2] đề xuất khung công tác IoT-MFaceNet, triển khai trên Raspberry Pi 400 phục vụ
kiểm soát truy cập tại một khoa của Đại học Mustansiriyah. Khối phát hiện khuôn mặt kết hợp ba phương
pháp Haar Cascade, dlib CNN và MediaPipe; khối trích xuất đặc trưng sử dụng MobileNetV2 và FaceNet,
sau đó phân loại bằng máy vectơ hỗ trợ (Support Vector Machine — SVM) hoặc mạng perceptron nhiều lớp
(Multilayer Perceptron — MLP). Nghiên cứu áp dụng TensorFlow Lite cùng các kỹ thuật lượng tử hoá
(quantization) và rút gọn mô hình nhằm giảm thời gian suy luận trên thiết bị hạn chế tài nguyên.

Trên cơ sở dữ liệu nội bộ gồm 24.300 ảnh của 10 danh tính, cấu hình FaceNet VGG-19 kết hợp SVM đạt
độ chính xác cao nhất 99,976 %, còn các cấu hình MobileNetV2 kết hợp MLP đạt 99,1–99,4 %. Về hiệu
năng, hệ thống đạt khoảng 6 FPS trên Raspberry Pi 400 khi chạy đa luồng, so với 25 FPS trên máy tính
cá nhân dùng bộ xử lý Ryzen 5 3600, và hoạt động ổn định trong phạm vi dưới 80 cm tính từ camera.

Đây là công trình gần với nghiên cứu hiện tại nhất về phần cứng và mục tiêu ứng dụng. Cần lưu ý các
con số độ chính xác nêu trên được đo trong bài toán tập đóng (closed-set) với 10 danh tính, tức mọi
đối tượng kiểm thử đều đã có trong cơ sở dữ liệu đăng ký; nghiên cứu không báo cáo tỉ lệ chấp nhận
sai đối với người chưa đăng ký. Hệ thống cũng chưa tích hợp phát hiện giả mạo và chưa mở rộng sang
điều khiển thiết bị.

Hai công trình quốc tế nêu trên cho thấy nhận diện khuôn mặt bằng học sâu đã khả thi trên máy tính
nhúng phổ thông, với độ chính xác cao trên cơ sở dữ liệu quy mô nhỏ. Tuy nhiên, cả hai đều đánh giá
hệ thống theo tiêu chí độ chính xác của bài toán tập đóng, trong khi một hệ thống kiểm soát truy cập
thực tế phải đối mặt với người chưa đăng ký và với các hình thức tấn công giả mạo.

#### 1.2.2. Các công trình trong nước

Phan Nguyễn Quốc Bảo và Hoàng Công Minh [3] xây dựng hệ thống nhà thông minh đa hệ sinh thái, tích hợp
thiết bị của nhiều hãng khác nhau vào một nền tảng điều khiển thống nhất. Kiến trúc phân tách thành
hai tầng: vi điều khiển ESP32 trên bo mạch NodeMCU-32S đóng vai trò thiết bị biên, trực tiếp thu thập
dữ liệu cảm biến và chấp hành lệnh điều khiển; Raspberry Pi đóng vai trò máy chủ, chạy Home Assistant
cùng ứng dụng Flask và đảm nhiệm khối nhận diện khuôn mặt. Khối này sử dụng mạng tích chập đa nhiệm
xếp tầng (Multi-task Cascaded Convolutional Networks — MTCNN) để phát hiện khuôn mặt và FaceNet để
sinh vectơ đặc trưng 128 chiều. Hệ thống hỗ trợ điều khiển thiết bị qua bốn kênh: giao diện web, cử
chỉ tay nhận dạng bằng MediaPipe, nhận diện khuôn mặt và tự động theo ngưỡng cảm biến.

Cách phân tách này khác với nghiên cứu hiện tại, nơi Raspberry Pi 5 vừa là thiết bị thu nhận vừa thực
hiện toàn bộ quá trình suy luận tại chỗ, không phụ thuộc vào một máy chủ tách rời.

Đây là công trình duy nhất trong bốn công trình khảo sát có triển khai trọn vẹn từ nhận diện đến điều
khiển thiết bị thực tế. Điểm hạn chế nằm ở phần đánh giá: nghiên cứu báo cáo kết quả theo hướng định
tính — hệ thống "hoạt động ổn định", "độ trễ thấp" — mà không công bố số liệu định lượng cho khối nhận
diện, cũng không mô tả điều kiện đo của khối này. Các thông số kỹ thuật được nêu chi tiết chỉ thuộc về
cảm biến môi trường. Nhóm tác giả cũng ghi nhận hệ thống chưa hỗ trợ nhiều người dùng và chưa có cơ chế
phân quyền truy cập theo danh tính, đồng thời chưa tích hợp phát hiện giả mạo.

Trương Văn Trương và Huỳnh Việt Thắng [4] triển khai hệ thống nhận dạng khuôn mặt trên máy tính nhúng
Raspberry Pi lõi ARM11 hoạt động ở tần số 700 MHz, sử dụng đặc trưng Haar-like kết hợp bộ phân lớp
xếp tầng để phát hiện khuôn mặt, và phân tích thành phần chính (Principal Component Analysis — PCA)
theo hướng Eigenface để trích xuất đặc trưng, sau đó đối sánh bằng khoảng cách Euclid với một ngưỡng
cho trước. Trên bộ dữ liệu chuẩn AT&T, hệ thống đạt hiệu suất nhận dạng 93 %.

Công trình này được công bố năm 2016, trước giai đoạn học sâu trở nên phổ biến trên thiết bị nhúng,
nên con số 93 % không đặt cùng thang so sánh với các kết quả của [1] và [2]. Giá trị tham chiếu của
nó nằm ở chỗ khác: nghiên cứu cho thấy ngay cả với phần cứng và phương pháp thế hệ trước, bài toán
nhận dạng khuôn mặt trên Raspberry Pi đã khả thi, và nút thắt được nhóm tác giả xác định là tốc độ
xử lý do giới hạn phần cứng. Hệ thống dừng ở xác định danh tính, không bao gồm chống giả mạo và
không triển khai điều khiển thiết bị, dù nhóm tác giả có nêu định hướng ứng dụng cho bảo mật gia đình.

Hai công trình trong nước phản ánh hai hướng khác nhau: [3] ưu tiên tính tích hợp hệ thống và trải
nghiệm điều khiển, [4] ưu tiên đánh giá thuật toán trên phần cứng hạn chế. Điểm chung là cả hai đều
không đánh giá hệ thống ở khía cạnh an ninh — không đo tỉ lệ chấp nhận sai và không kiểm thử với
các hình thức tấn công giả mạo.

#### 1.2.3. Tổng hợp

Đặt bốn công trình theo trục thời gian có thể thấy rõ hướng phát triển của **khối phát hiện khuôn
mặt**: từ đặc trưng Haar-like kết hợp bộ phân lớp xếp tầng [4], sang biểu đồ gradient có hướng và
mạng tích chập [1], rồi tới việc kết hợp nhiều bộ phát hiện chạy nối tiếp — Haar Cascade, dlib CNN
và MediaPipe — nhằm tăng độ tin cậy [2], và mạng đa nhiệm xếp tầng MTCNN [3]. Xu hướng chung là
chuyển từ đặc trưng thiết kế thủ công sang mạng học sâu, đồng thời chấp nhận chi phí tính toán cao
hơn để đổi lấy độ tin cậy của khâu phát hiện.

Đáng chú ý là **không công trình nào trong nhóm khảo sát sử dụng họ mô hình phát hiện một giai đoạn**
(one-stage detector) như YOLO, vốn được thiết kế hướng tới suy luận thời gian thực bằng cách dự đoán
đồng thời vị trí và độ tin cậy trong một lần duyệt ảnh. Các phương pháp xếp tầng và đa giai đoạn được
sử dụng ở [2], [3], [4] phải duyệt ảnh nhiều lần hoặc qua nhiều bộ phân lớp nối tiếp, khiến thời gian
xử lý phụ thuộc vào số khuôn mặt và độ phức tạp của khung hình. Đây là điểm khác biệt về phương pháp
mà nghiên cứu hiện tại lựa chọn khai thác.

Khối **trích xuất đặc trưng** cũng cho thấy một chuyển dịch tương tự: từ phân tích thành phần chính
theo hướng Eigenface [4] — một phương pháp thống kê tuyến tính — sang các vectơ đặc trưng sinh bởi
mạng học sâu như ResNet [1], MobileNetV2 và FaceNet [2], [3]. Tuy nhiên, không công trình nào áp dụng
các hàm mất mát dựa trên biên góc (angular margin loss) như ArcFace, hướng tiếp cận hiện được xem là
chuẩn cho nhận diện khuôn mặt độ chính xác cao.

Về mặt đo đạc, chỉ [2] công bố tốc độ khung hình đạt được trên thiết bị nhúng. Hai công trình [1] và
[4] chỉ báo cáo độ chính xác, còn [3] đánh giá theo hướng định tính. Do đó, mặc dù các thuật toán được
sử dụng rất khác nhau về chi phí tính toán, nhóm công trình khảo sát **chưa cung cấp cơ sở để đối chiếu
đánh đổi giữa độ chính xác và tốc độ** giữa các phương án trên cùng một nền tảng phần cứng.

Bảng 1.1 tổng hợp đối chiếu phạm vi chức năng và kết quả công bố của bốn công trình với nghiên cứu hiện tại.

**Bảng 1.1.** Đối chiếu phạm vi của các công trình liên quan với nghiên cứu này

| Công trình | Phần cứng | Mô hình (phát hiện → nhận diện) | Kết quả công bố | Báo cáo FAR | Chống giả mạo | Điều khiển thiết bị |
|---|---|---|---|---|---|---|
| Zamir và cộng sự (2022) [1] | Raspberry Pi *(không nêu phiên bản)* | HOG / CNN → ResNet (dlib, OpenCV) | Accuracy 89,5–98,6 % trên bốn bộ dữ liệu, trong đó có một bộ tự thu 700 ảnh / **7 danh tính**; **không công bố FPS** | Không | Không | Không |
| Mohammad và cộng sự (2024) [2] | Raspberry Pi 400 | Haar Cascade + dlib CNN + MediaPipe → MobileNetV2 + FaceNet, phân loại SVM/MLP | Accuracy **99,976 %** (FaceNet VGG-19 + SVM) và 99,1–99,4 % (MobileNetV2 + MLP), đo closed-set trên CSDL nội bộ 24.300 ảnh / **10 danh tính**; **6 FPS** trên Pi 400 (25 FPS trên PC Ryzen 5 3600); hiệu quả ở khoảng cách < 80 cm | Không | Không | Không |
| Phan Nguyễn Quốc Bảo và Hoàng Công Minh (2025) [3] *(đồ án tốt nghiệp, ĐH Bách khoa – ĐH Đà Nẵng)* | ESP32 (NodeMCU-32S) tại biên + **Raspberry Pi làm máy chủ** (Flask / Home Assistant) | MTCNN → FaceNet (embedding 128 chiều) | **Không công bố số liệu định lượng** cho khối nhận diện; đánh giá định tính "ổn định, độ trễ thấp" | Không | Không | **Có** — đèn, quạt, cửa; qua web, cử chỉ tay, khuôn mặt, cảm biến |
| Trương Văn Trương và Huỳnh Việt Thắng (2016) [4] *(Tạp chí KH&CN ĐH Đà Nẵng)* | Raspberry Pi lõi ARM11 @ 700 MHz + Picamera / USB webcam | Haar-like + Cascade → PCA (Eigenface) + khoảng cách Euclid | Hiệu suất nhận dạng 93 % trên bộ AT&T; **không công bố FPS** | Không | Không | Không |
| **Nghiên cứu này** | **Raspberry Pi 5 8 GB** + camera *(suy luận hoàn toàn tại chỗ)* | **YOLOv8n-face → dlib / MobileFaceNet-ArcFace** *(so sánh hai phương án)* **+ MiniFASNet** | `[CHƯA ĐO]` | **Có** — `FAR_lfw`, `FAR_adapt`, `FAR_indomain` | **Có** (MiniFASNet) | **Có** (GPIO + IR) |

*Nguồn: tổng hợp từ tài liệu tham khảo [1]–[4]. Số trích dẫn là tạm, chốt lại sau khi hoàn thành §1.1.*

Cần lưu ý Bảng 1.1 không phải bảng xếp hạng. Mỗi công trình đánh giá trên bộ dữ liệu khác nhau, số
danh tính khác nhau và điều kiện đo khác nhau, do đó các giá trị ở cột "Kết quả công bố" không so sánh
trực tiếp được với nhau. Bảng đối chiếu phạm vi chức năng và hướng tiếp cận nhằm xác định vị trí của
nghiên cứu hiện tại, không nhằm xếp hạng hiệu năng.

---

> 🖉 *Hết phần đưa vào báo cáo. Phần dưới đây là tài liệu làm việc, **không đưa vào báo cáo**.*

| Nhãn | Loại | Yêu cầu |
|---|---|---|
| **NN-1** | Nước ngoài | Bài báo bình duyệt, 2020–2026, **có số liệu đo trên thiết bị nhúng thật** |
| **NN-2** | Nước ngoài | Như trên, nên khác hướng tiếp cận với NN-1 |
| **TN-1** | Trong nước | Bài báo hoặc đồ án/luận văn |
| **TN-2** | Trong nước | Như trên |

### Tìm công trình nước ngoài

Nguồn: Google Scholar · IEEE Xplore · arXiv. Từ khoá:

```
face recognition raspberry pi
lightweight face recognition embedded ARM
edge AI face recognition smart home
face anti-spoofing embedded device
real-time face recognition access control edge
```

Ưu tiên bài **đo trên thiết bị nhúng thật** (Pi, Jetson Nano, điện thoại) — đó là công trình bạn
so sánh được. Bài đo trên GPU máy bàn chỉ dùng để nêu bối cảnh, không dùng để đối chiếu hiệu năng.

### Tìm công trình trong nước

Nguồn:
- **Thư viện số các trường** — UIT, ĐHQG-HCM, BKHN, ĐH Đà Nẵng… (nơi có khoá luận, luận văn)
- **Tạp chí**: Chuyên san *Các công trình nghiên cứu, phát triển và ứng dụng CNTT&TT* (JRD) ·
  *Tạp chí Tin học và Điều khiển học* · tạp chí khoa học của các trường
- **Kỷ yếu hội nghị**: FAIR, NICS, hội nghị khoa học công nghệ cấp trường
- Google Scholar với từ khoá tiếng Việt:

```
nhận dạng khuôn mặt Raspberry Pi
hệ thống điểm danh bằng khuôn mặt
nhận diện khuôn mặt thời gian thực trên thiết bị nhúng
phát hiện giả mạo khuôn mặt
```

**Tiêu chí tối thiểu** cho công trình trong nước — thiếu thì tìm bài khác:
- Có mô tả phương pháp đủ để hiểu (không chỉ liệt kê công cụ đã dùng)
- Có ít nhất một bảng kết quả thực nghiệm
- Nêu được phần cứng và điều kiện đo

> ⚠️ Nếu chọn **đồ án/khoá luận**, ghi rõ loại tài liệu khi trích dẫn (*khoá luận tốt nghiệp*,
> *luận văn thạc sĩ*) và tên trường. Không trình bày như bài báo bình duyệt.

### Bảng làm việc — điền khi đọc (không đưa vào báo cáo)

| Nhãn | Tác giả, năm, nơi công bố | Bài toán | Mô hình detect | Mô hình nhận diện | Phần cứng | Kết quả báo cáo | Có anti-spoofing? | Có điều khiển thiết bị? | Điều kiện đo | Hạn chế |
|---|---|---|---|---|---|---|---|---|---|---|
| [Face Detection & Recognition from Images & Videos Based on CNN & Raspberry Pi](https://www.mdpi.com/2079-3197/10/9/148) |Muhammad Zamir, Nouman Ali,Amad Naseem, Areeb Ahmed Frasteen, Bushra Zafar, Muhammad Assam, Mahmoud Othman and El-Awady Attia/2022/ Computation | Sử dụng Raspberry Pi cho ứng dụng nhà thông minh: Sử dụng Raspberry Pi, một thiết bị dựa trên IoT phổ biến, cho các ứng dụng như giám sát nhà thông minh và có thể kết nối với Internet dễ dàng.Hệ thống chi phí thấp, đáng tin cậy cho ứng dụng IoT: Mục tiêu là trình bày một hệ thống nhận diện và phát hiện khuôn mặt thời gian thực, chi phí thấp và độ tin cậy cao, có thể sử dụng trong bất kỳ ứng dụng dựa trên IoT nào.| HOG và CNN detector | CNN kết hợp ResNet, Dlib và OpenCV chạy trên Raspberry Pi| Raspberry Pi|Kết quả báo cáo trong bài nghiên cứu này cho thấy hệ thống nhận diện khuôn mặt dựa trên CNN chạy trên Raspberry Pi đạt độ chính xác rất cao khi so sánh với phương pháp HOG và các nghiên cứu trước đó:<br> Dataset VMU (Virtual Makeup): đạt 98% độ chính xác với tỷ lệ huấn luyện 80:20, và 89.5% với tỷ lệ 70:30.<br> Face Recognition dataset: đạt 97.39% (70:30) và 98.24% (80:20). Precision, Recall và F1-score đều trên 98%.<br>14 Celebrity dataset: đạt 98.39% (70:30) và 98.63% (80:20). Precision, Recall và F1-score dao động quanh 90–93%. <br>Dataset tự tạo (700 ảnh, 7 người): đạt 95.23% (70:30) và 97.71% (80:20). Precision, Recall và F1-score đều trên 96%.<br>Video testing: CNN cho kết quả vượt trội (98% khi huấn luyện và kiểm thử bằng CNN) so với HOG (chỉ khoảng 59–84%).<br>Nhận diện khuôn mặt có khẩu trang: CNN vẫn duy trì độ chính xác cao hơn HOG, chứng minh khả năng thích ứng với điều kiện thực tế. |không có nội dung về liveness detection hay anti-spoofing (ví dụ: phân biệt ảnh in, video giả, hay mặt nạ). Điều này nghĩa là hệ thống có thể nhận diện chính xác khuôn mặt thật trong dữ liệu, nhưng chưa có cơ chế bảo vệ chống lại việc kẻ gian dùng ảnh hoặc video để đánh lừa. | Trong bài báo trên MDPI về Face Detection & Recognition từ Images & Videos dựa trên CNN & Raspberry Pi, hệ thống chỉ tập trung vào phát hiện và nhận diện khuôn mặt. Nó không có phần điều khiển thiết bị.| 👉 Tóm lại, điều kiện đo bao gồm thiết bị Raspberry Pi + camera, dữ liệu đa dạng (chuẩn và tự tạo), tỷ lệ train/test khác nhau, và môi trường ánh sáng + khẩu trang để kiểm chứng tính ứng dụng thực tế.|giới hạn phần cứng, thiếu cơ chế chống giả mạo, và dữ liệu chưa đủ phong phú.|
| [IoT-MFaceNet: Internet-of-Things-Based Face Recognition Using MobileNetV2 and FaceNet Deep-Learning Implementations on a Raspberry Pi-400](https://www.mdpi.com/2079-9268/14/3/46) |Ahmad Saeed Mohammad,Thoalfeqar G. Jarullah 1ORCID,Musab T. S. Al-Kaltakchi,Jabir Alshehabi Al-Ani and Somdip Dey<br> Published: 5 September 2024|Đề xuất một khung công tác gọi là IoT-MFaceNet, một hệ thống nhận diện khuôn mặt dựa trên Internet Vạn Vật (IoT) sử dụng học sâu MobileNetV2 và FaceNet.<br>Triển khai trên Raspberry Pi: Trình diễn hệ thống nhận dạng khuôn mặt trên các thiết bị tài nguyên hạn chế như Raspberry Pi 400, cho thấy độ chính xác cao và khả năng hoạt động hiệu quả.<br>Ứng dụng Kiểm soát Truy cập: Mô tả việc hệ thống hoạt động như một công cụ xác định tập hợp kín để kiểm soát quyền truy cập vào một phòng ban cụ thể trong một trường đại học, chỉ cho phép nhân viên được ủy quyền. |Mô hình detect trong nghiên cứu này không chỉ dùng một thuật toán duy nhất mà là tổ hợp Haar Cascade + Dlib CNN + Mediapipe, nhằm tăng độ chính xác và độ tin cậy khi phát hiện khuôn mặt trước khi nhận dạng. |mô hình nhận diện trong nghiên cứu này là MobileNetV2 và FaceNet (cho trích xuất đặc trưng), kết hợp với SVM/MLP (cho phân loại). |phần cứng của hệ thống chủ yếu là Raspberry Pi 400 + camera module, kết hợp với các thiết bị ngoại vi cơ bản để phục vụ cho việc phát hiện và nhận diện khuôn mặt trong môi trường IoT | hệ thống nhận diện khuôn mặt được đề xuất (IoT-MFaceNet) đã hoạt động thành công trên thiết bị có cấu hình thấp (Raspberry Pi 400) trong thời gian thực, phục vụ cho việc kiểm soát quyền truy cập vào phòng ban của trường Đại học Mustansiriyah (Iraq) với độ chính xác tối đa lên tới 99.976%. Hệ thống này đã vượt trội hơn so với nhiều phương pháp hiện có khi so sánh (State-of-the-Art).<br>Kết quả chi tiết theo từng mô hình thử nghiệm<br>1. Thử nghiệm với MobileNetV2 và bộ phân loại MLP:<br>Nhóm nghiên cứu đã tạo ra các mạng nơ-ron tùy chỉnh với các kích thước khác nhau (Custom Top) và áp dụng các kỹ thuật tối ưu hóa (TensorFlow Lite và giảm độ phức tạp của mô hình - "squeezing") để giảm thời gian xử lý và dung lượng lưu trữ nhưng vẫn giữ được độ chính xác cao.<br>Mô hình nhỏ nhất (Custom Top 128-128-128): Đạt độ chính xác 99.4% (cả trước và sau khi tối ưu hóa).>br>Mô hình trung bình (Custom Top 192-256-128): Đạt độ chính xác 99.1% (cả trước và sau khi tối ưu hóa).<br>Mô hình lớn nhất (Custom Top 384-384-384): Độ chính xác tăng nhẹ từ 98.7% (trước tối ưu) lên 99.3% (sau tối ưu).<br>2. Thử nghiệm với FaceNet và bộ phân loại SVM:<br>Mô hình FaceNet được đào tạo trên bộ dữ liệu nội bộ gồm 24.300 bức ảnh chụp từ điện thoại thông minh của 10 đối tượng khác nhau. Kết quả cho thấy độ phân loại xuất sắc:<br>Mô hình FaceNet VGG-16 + SVM: Đạt độ chính xác 99.88%.<br>Mô hình FaceNet VGG-19 + SVM: Đạt độ chính xác cao nhất của toàn bộ nghiên cứu là 99.976%.<br>So sánh với các phương pháp khác: hệ thống vượt trội hơn các nghiên cứu hiện tại, nhờ kết hợp MobileNetV2 + FaceNet cùng các bộ phân loại SVM/MLP và tối ưu hóa bằng TensorFlow Lite (quantization, model squeezing).<br>Ứng dụng thực tế: được triển khai như một hệ thống nhận dạng kín trong Khoa Kỹ thuật Máy tính, Đại học Mustansiriyah (Iraq), để kiểm soát truy cập phòng báo cáo của khoa |IoT-MFaceNet không tích hợp anti-spoofing, nên nếu triển khai thực tế trong môi trường an ninh cao (ví dụ kiểm soát ra vào), cần bổ sung thêm các kỹ thuật như:<br>Phát hiện chuyển động mắt/môi (liveness detection).<br>Sử dụng cảm biến hồng ngoại hoặc chiều sâu (depth camera).<br>Áp dụng mô hình học sâu chuyên biệt cho phát hiện giả mạo. |IoT-MFaceNet chỉ tập trung vào nhận diện khuôn mặt, chưa tích hợp điều khiển thiết bị IoT | Điều kiện đo (measurement conditions) khi thử nghiệm hệ thống:<br>Khoảng cách: hệ thống nhận diện hoạt động tốt nhất khi khuôn mặt ở trong phạm vi dưới 80 cm từ camera. Nếu vượt quá khoảng này, độ chính xác giảm và giao diện sẽ cảnh báo.<br>Thiết bị: thử nghiệm trên Raspberry Pi 400 với camera module, đồng thời so sánh với PC (CPU Ryzen 5 3600).<br>Tốc độ xử lý:<br>Trên PC: trung bình 25 FPS.<br>Trên Raspberry Pi 400: khoảng 6 FPS khi chạy đa luồng.<br>Nguồn dữ liệu: ảnh và video thu từ webcam, smartphone, và camera gắn với Raspberry Pi.<br>Môi trường: thử nghiệm trong phòng học/laboratory của Khoa Kỹ thuật Máy tính, Đại học Mustansiriyah (Iraq).<br>Điều kiện ánh sáng: không có mô tả chi tiết, nhưng hệ thống được kiểm tra trong môi trường ánh sáng bình thường (indoor lighting).|Tốc độ xử lý thấp trên Raspberry Pi 400: chỉ đạt khoảng 6 FPS, chưa đủ mượt cho các ứng dụng thời gian thực phức tạp.<br>📏 Giới hạn khoảng cách nhận diện: hệ thống chỉ hoạt động ổn định trong phạm vi dưới 80 cm. Nếu xa hơn, độ chính xác giảm đáng kể.<br>🔒 Không có anti-spoofing: chưa có cơ chế chống giả mạo (ví dụ: phân biệt ảnh in, video, mặt nạ với khuôn mặt thật).<br>🔌 Chưa tích hợp điều khiển thiết bị IoT: hệ thống mới dừng ở mức nhận diện, chưa kết nối để mở cửa, bật đèn, hay điều khiển thiết bị thông minh.<br>🌐 Phạm vi thử nghiệm hạn chế: chủ yếu trong môi trường phòng học/lab, chưa kiểm chứng trong điều kiện ánh sáng phức tạp hoặc môi trường ngoài trời.<br>🧩 Phụ thuộc vào camera 2D: chưa tận dụng cảm biến chiều sâu hoặc hồng ngoại, nên dễ bị ảnh hưởng bởi ánh sáng và góc chụp. |
| [Giám sát và Điều khiển hệ thống điện trong nhà thông minh](http://thuvienso.dut.udn.vn/handle/DUT/20276) |Phan Nguyễn Quốc Bảo, Hoàng Công Minh<br>	Publisher: Trường Đại học Bách Khoa, Đại học Đà Nẵng<br>Issue Date: 2025 |Đồ án này tập trung nghiên cứu, thiết kế và triển khai một hệ thống nhà thông minh đa hệ sinh thái, có khả năng tích hợp các thiết bị từ nhiều hãng khác nhau như Xiaomi, Yeelight, Tuya... vào một nền tảng điều khiển thống nhất dựa trên Home Assistant và Flask Server. Hệ thống bao gồm các tính năng nổi bật như:<br>- Điều khiển thiết bị thông minh từ nhiều hệ sinh thái thông qua giao diện web than thiện.<br>- Giám sát môi trường sống với cảm biến khí gas, nhiệt độ, độ ẩm<br>- Hệ thống bảo mật thông minh bằng cách nhận diện khuôn mặt (Sử dụng mô hình MTCNN và FaceNet)<br>- Tương tác bằng cử chỉ tay (sử dụng thư viện MeadiaPipe)<br>- Lưu trữ lịch sử và hiển thị dữ liệu thời gian thực<br>Đồ án không chỉ giải quyết bài toán phân mảng giữa các hệ sinh thái thiết bị mà còn hướng đến giải pháp mở, chi phí hợp lý, phù hợp với người dùng phổ thông tại Việt Nam | 1. Phát hiện và nhận diện khuôn mặt (Face Detection & Verification)<br>Mô hình MTCNN (Multi-task Cascaded Convolutional Networks): Được sử dụng để phát hiện khuôn mặt (Face Detection). Mô hình này làm nhiệm vụ quét hình ảnh đầu vào, xác định vị trí khuôn mặt (tạo các bounding boxes) và các điểm đặc trưng (landmarks) như mắt, mũi, miệng.<br>Mô hình FaceNet: Sau khi MTCNN phát hiện và cắt được khuôn mặt, FaceNet được sử dụng để xác minh/nhận diện (Face Verification). Nó chuyển đổi khuôn mặt thành một vector đặc trưng (embedding vector) gồm 128 chiều để so sánh và phân biệt xem đó là người quen hay người lạ.<br>2. Phát hiện và nhận diện cử chỉ tay (Hand Gesture Detection)<br>Mô hình MediaPipe: Sử dụng giải pháp Hands của thư viện MediaPipe (do Google phát triển) để phát hiện bàn tay (Hand Detection) và trích xuất 21 điểm đặc trưng (landmarks) trên bàn tay theo thời gian thực. Từ đó, hệ thống phân tích số ngón tay giơ lên để phát hiện các cử chỉ điều khiển thiết bị (ví dụ: giơ 1 ngón để bật đèn, giơ 2 ngón để tắt đèn).| 1. Nhận diện khuôn mặt (Face Verification) bằng mô hình FaceNet<br>2. Nhận diện cử chỉ tay bằng thuật toán phân tích điểm đặc trưng của MediaPipe| Bộ vi điều khiển trung tâm:<br>Bo mạch NodeMCU-32S (sử dụng chip ESP32): Đóng vai trò là bộ não xử lý tín hiệu tại phần cứng, thu thập dữ liệu từ cảm biến và giao tiếp với Server thông qua Wi-Fi/Bluetooth. và các cảm biến như khí gas, thiết bị đo nhiệt độ, đọ ẩm xiaomi, thiết bị thu nhận hình ảnh( camera/camera an ninh)|Hoạt động ổn định và nhận diện chính xác: Hệ thống nhận diện khuôn mặt (sử dụng MTCNN + FaceNet) và nhận diện cử chỉ tay (sử dụng MediaPipe) hoạt động trơn tru trong thời gian thực với độ trễ thấp. Các cảm biến và thiết bị đầu ra (đèn, quạt, cửa tự động) tương tác mượt mà với bộ điều khiển trung tâm.<br>Giao diện thân thiện, cập nhật thời gian thực (Real-time): Giao diện web được thiết kế trực quan, dễ sử dụng. Nhờ sử dụng giao thức WebSocket, mọi trạng thái của thiết bị và hình ảnh camera đều được đồng bộ và phản hồi ngay lập tức khi có thao tác điều khiển mà không cần tải lại trang.<br>Tích hợp thành công nhiều công nghệ hiện đại: Nhóm đã kết hợp hiệu quả giữa phần cứng và phần mềm, bao gồm Trí tuệ nhân tạo (Machine Learning), Internet vạn vật (IoT), vi điều khiển ESP32 và nền tảng quản lý nhà thông minh mã nguồn mở Home Assistant.<br>Điều khiển đa kênh đồng bộ: Hệ thống cho phép người dùng điều khiển thiết bị qua nhiều phương thức khác nhau như: nhận diện khuôn mặt, ra dấu bằng cử chỉ tay, nút bấm vật lý hoặc qua giao diện web. Mọi tín hiệu đều được xử lý tập trung qua Server để đảm bảo tính đồng bộ, không xảy ra xung đột.<br>Tính ứng dụng thực tiễn cao: Mô hình có chi phí triển khai hợp lý và khả năng mở rộng linh hoạt, rất phù hợp để áp dụng cho các hộ gia đình, văn phòng, hoặc cơ sở y tế tại Việt Nam. Đặc biệt, tính năng điều khiển không chạm (qua cử chỉ) mang lại sự an toàn và tiện lợi, rất hữu ích cho người già, trẻ nhỏ hoặc trong bối cảnh cần hạn chế tiếp xúc vật lý. |không có tính năng anti-spoofing (chống giả mạo / nhận diện thực thể sống - liveness detection). | Điều khiển qua giao diện web, điều khiển bằng cử chỉ tay, điều kiển tự động nhận diện khuôn mặt, điều khiển tự động dựa trên cảm biến|rong báo cáo đồ án, mặc dù không có một mục riêng biệt định nghĩa về "điều kiện đo" chung cho toàn hệ thống, nhưng tác giả có nêu rõ điều kiện hoạt động và phạm vi đo (measurement conditions/ranges) của từng loại cảm biến được sử dụng để thu thập dữ liệu. Cụ thể như sau:1. Đối với thiết bị đo nhiệt độ, độ ẩm Xiaomi (LYWSD03MMC):Phạm vi đo nhiệt độ: Từ $0^{\circ}C$ đến $60^{\circ}C$.Độ chính xác nhiệt độ: $0.1^{\circ}C$.Phạm vi đo độ ẩm: Từ $0\%$ đến $99\%$ RH (Relative Humidity - Độ ẩm tương đối).Độ chính xác độ ẩm: $1\%$.2. Đối với cảm biến siêu âm HC-SR04 (Dùng để đo khoảng cách/phát hiện người):Phạm vi đo: Có thể đo khoảng cách trong khoảng từ 2 cm đến 300 cm.Điều kiện phát sóng: Cảm biến phát ra sóng siêu âm với tần số $40kHz$ để đo thời gian phản xạ lại.Điều kiện kích hoạt thực tế trong hệ thống: Tác giả thiết lập vùng xác định là 10 cm. Khi có vật thể/người tiến vào khoảng cách này, cảm biến sẽ báo về vi điều khiển để kích hoạt camera nhận diện khuôn mặt.3. Đối với cảm biến khí gas MQ2:Điều kiện hoạt động: Hoạt động tốt trong môi trường có khí hóa lỏng LPG, H2 và các khí gây cháy khác.Cơ chế đo: Độ nhạy của cảm biến thấp với không khí sạch, nhưng khi môi trường có chất dễ cháy, điện áp đầu ra sẽ thay đổi và tỷ lệ thuận với nồng độ khí gas có trong môi trường đó. |Chưa hỗ trợ nhiều người dùng và phân quyền truy cập: Hệ thống hiện chỉ lưu trữ dữ liệu (embedding) khuôn mặt của một số ít người dùng và chưa có cơ chế phân quyền tài khoản (ví dụ: phân biệt giữa quản trị viên và khách). Điều này làm hạn chế khả năng triển khai ở môi trường nhiều thành viên như gia đình đông người hay văn phòng.<br>Điều khiển bằng giọng nói chưa được triển khai hoàn chỉnh: Mặc dù kiến trúc hệ thống hỗ trợ mở rộng, nhưng phiên bản hiện tại chưa tích hợp công nghệ xử lý ngôn ngữ tự nhiên (NLP) hoặc nhận diện giọng nói bằng tiếng Việt.<br>Phụ thuộc vào mạng (nội bộ/Internet): Để duy trì giao tiếp thời gian thực giữa các thành phần (Server, vi điều khiển ESP32, Home Assistant và Dashboard web), hệ thống bắt buộc phải có kết nối mạng liên tục và ổn định.<br>Chưa triển khai mô hình Machine Learning tùy chỉnh: Dự án hiện tại vẫn đang sử dụng các mô hình học máy và AI có sẵn (như MTCNN, FaceNet, MediaPipe) thay vì tự xây dựng và huấn luyện một mô hình tùy chỉnh chuyên biệt.<br>Hạn chế khi xử lý nhiều thiết bị cùng lúc: Năng lực xử lý dữ liệu và điều khiển đồng thời một số lượng lớn thiết bị trong cùng một thời điểm vẫn còn gặp giới hạn. |
| [Nhận dạng khuôn mặt trên máy tính nhúng Raspberry Pi](https://jst-ud.vn/jst-ud/article/view/3611) |Trương Văn Trương, Huỳnh Việt Thắng, đăng trên Tạp chí Khoa học và Công nghệ Đà Nẵng năm 2016 |Nhận dạng khuôn mặt người là một trong những lĩnh vực mang tính thách thức trong thị giác máy tính và học máy. Hầu hết các hệ thống nhận dạng khuôn mặt hiện có đều sử dụng tài nguyên tính toán mạnh mẽ dựa trên DSP hoặc các máy tính đa mục đích, rất khó ứng dụng vào các dự án vừa và nhỏ như nhận dạng nhân trắc học cho hệ thống bảo mật gia đình, hệ thống chấm công và quản lý nhân viên trong các công ty. Chúng tôi giới thiệu một nền tảng phần cứng nhúng mới dùng trong xử lý ảnh, đó là máy tính nhúng Raspberry Pi lõi ARM11, sử dụng thư viện xử lý ảnh mã nguồn mở OpenCV của Intel. Chúng tôi sử dụng đặc trưng Haar-like cho phát hiện khuôn mặt và thuật toán phân tích thành phần chính cho nhận dạng khuôn mặt, tất cả được thực thi trên board mạch Raspberry Pi. Hệ thống được thiết kế với nguồn tài nguyên phần cứng giới hạn, giá thành thấp, tiêu tán năng lượng thấp, đảm bảo hiệu suất nhận dạng 93% và tốc độ nhận dạng tốt. | Đặc trưng Haar-like kết hợp với kỹ thuật phân lớp Cascade of Classifiers (hay còn gọi là phân lớp Haar Cascade).<br>Thuật toán này được hỗ trợ thông qua thư viện mã nguồn mở OpenCV, hoạt động dựa trên việc dùng các bộ phân lớp từ đơn giản đến phức tạp (Cascade tree) để quét và loại bỏ nhanh các vùng nền không chứa khuôn mặt, giúp tăng tốc độ xử lý.<br>* **Thuật toán Phân tích thành phần chính (PCA - Principal Component Analysis)**: Phương pháp này được sử dụng để trích xuất các đặc trưng của khuôn mặt và tìm ra các "mặt riêng" (Eigenface). Thuật toán sẽ giúp giảm chiều dữ liệu nhưng vẫn giữ lại các hướng biến thiên quan trọng nhất của khuôn mặt.<br>* **Kỹ thuật đối sánh mẫu (Template matching) bằng khoảng cách Euclidian**: Sau khi dùng PCA để trích xuất ra vector đặc trưng, hệ thống sẽ tính khoảng cách Euclidian giữa khuôn mặt cần nhận dạng và các khuôn mặt đã có trong tập cơ sở dữ liệu huấn luyện. Nếu khoảng cách nhỏ nhất thu được bé hơn một ngưỡng cho trước, hệ thống sẽ kết luận đó là khuôn mặt của người tương ứng trong cơ sở dữ liệu. | Máy tính nhúng Raspberry Pi: Đây là nền tảng phần cứng chính của hệ thống. Nhóm tác giả sử dụng phiên bản bo mạch Raspberry Pi có lõi ARM11, hoạt động ở tần số xung đồng hồ 700MHz. Ưu điểm của thiết bị này là nhỏ gọn, giá thành thấp và tiêu thụ ít năng lượng nhưng vẫn đáp ứng được quá trình xử lý ảnh.<br>Module Camera: Hệ thống sử dụng Picamera hoặc USB webcam kết nối với bo mạch Raspberry Pi để thu thập dữ liệu hình ảnh đầu vào (dùng cho cả việc xây dựng cơ sở dữ liệu huấn luyện và nhận dạng trực tiếp).|Hiệu suất nhận dạng: Hệ thống đạt tỷ lệ nhận dạng đúng khá cao, lên đến 93%.<br>Tốc độ xử lý: Đảm bảo tốc độ nhận dạng tốt dù phải hoạt động trên nền tảng phần cứng có tài nguyên giới hạn (bo mạch Raspberry Pi lõi ARM11, xung nhịp 700MHz).<br>Tối ưu hóa tài nguyên: Kết quả cho thấy hệ thống hoạt động ổn định với mức tiêu tán năng lượng thấp và giá thành rẻ so với các hệ thống DSP chuyên dụng truyền thống.<br>Phương pháp đo lường: Các thông số về hiệu suất và thời gian nhận dạng này được nhóm tác giả thử nghiệm và đánh giá một cách khách quan trên bộ cơ sở dữ liệu khuôn mặt chuẩn AT&T. | Không có cơ chế chống giả mạo|Bài nghiên cứu này chủ yếu tập trung vào việc xây dựng, tối ưu và đánh giá thuật toán nhận dạng trên nền tảng máy tính nhúng Raspberry Pi. Đầu ra của hệ thống dừng lại ở việc xác định danh tính khuôn mặt và đo lường các thông số như hiệu suất nhận dạng (93%) hay thời gian xử lý.<br>Tuy nhiên, vì nền tảng phần cứng là Raspberry Pi có hỗ trợ các chân giao tiếp phần cứng (GPIO), và nhóm tác giả có định hướng ứng dụng cho "hệ thống bảo mật gia đình" hay "hệ thống chấm công", nên việc lập trình xuất tín hiệu để điều khiển các thiết bị điện tử sau khi nhận dạng thành công là hoàn toàn khả thi trong thực tế, dù nó không nằm trong phạm vi thử nghiệm của bài báo này. | Điều kiện phần cứng: Hệ thống được thực thi và đo lường trực tiếp trên bo mạch máy tính nhúng Raspberry Pi (lõi ARM11), hoạt động ở tần số xung đồng hồ là 700MHz.<br>Dữ liệu thử nghiệm (Dataset): Nhóm tác giả sử dụng bộ cơ sở dữ liệu khuôn mặt AT&T để tiến hành đánh giá. Dữ liệu này được chia ra thành các tập huấn luyện (training) và tập kiểm tra (testing).<br>Điều kiện hình ảnh đầu vào: Các ảnh đưa vào thử nghiệm có cường độ ánh sáng và biểu cảm khuôn mặt khác nhau. Hình ảnh phải ở định dạng PGM hoặc JPEG. Kích thước các ảnh có thể chênh lệch nhau nhưng hệ thống sẽ tự động chuẩn hóa lại ở bước dò tìm khuôn mặt.<br>Tiêu chí đo lường: Quá trình đo lường tập trung vào hai thông số chính để đánh giá hiệu năng của hệ thống, bao gồm hiệu suất nhận dạng (tỉ lệ nhận dạng đúng) và thời gian nhận dạng.| tốc độ nhận dạng chậm hơn vì những giới hạn về phần cứng của RaspberryPi (tốc độ vi xử lý,bộ nhớ)|

Hai cột quan trọng nhất:
- **Điều kiện đo** — độ phân giải, khoảng cách, ánh sáng, cỡ tập dữ liệu, số danh tính.
  Thiếu thông tin này thì con số kết quả **không so sánh được**, và bản thân việc thiếu đó
  là một hạn chế đáng nêu.
- **Hạn chế** — nuôi thẳng §1.3. Ghi cụ thể: *"chỉ báo accuracy, không có FAR"*,
  *"không chống giả mạo"*, *"đo trên tập tự thu, không công bố số danh tính"*.

### Bảng 1.1

**Đã chuyển lên mục 1.2.3** (phần đưa vào báo cáo). Sửa trực tiếp ở đó, không giữ bản sao ở đây
để tránh hai phiên bản lệch nhau.

### Nhận xét rút ra từ Bảng 1.1 — nguyên liệu cho §1.3

Ba mẫu hình lặp lại trên **cả bốn** công trình:

1. **Không công trình nào báo cáo tỉ lệ chấp nhận sai (FAR).** Cả bốn chỉ công bố accuracy —
   chỉ số của bài toán closed-set. Với hệ thống mở khoá thiết bị, người đứng trước camera có thể
   là **bất kỳ ai**, nên FAR mới là chỉ số phản ánh năng lực an ninh. Đây là khoảng trống rõ nhất.
2. **Không công trình nào tích hợp chống giả mạo.** Cả bốn đều nhận diện được khuôn mặt thật,
   nhưng không phân biệt được người thật với ảnh in hay màn hình điện thoại.
3. **Nhận diện và điều khiển thiết bị bị tách rời.** Ba công trình dừng ở nhận diện; công trình
   duy nhất có điều khiển thiết bị [3] lại không công bố số liệu định lượng cho khối nhận diện.
   Chưa có công trình nào đo **đồng thời** độ chính xác, FAR, tỉ lệ chặn tấn công giả mạo và
   độ trễ điều khiển trên cùng một hệ thống.

4. **Các con số accuracy đều đo trên cơ sở dữ liệu quy mô nhỏ.** Bộ tự thu của [1] gồm 7 danh tính,
   của [2] gồm 10 danh tính; [3] chỉ nêu "một số ít người dùng", không công bố số lượng.
   Điều này cho thấy accuracy cao trên thiết bị nhúng thường gắn với bài toán closed-set quy mô
   nhỏ — bối cảnh cần nêu khi diễn giải mọi con số ở cột "Kết quả công bố", **kể cả của nghiên
   cứu này**.

Hai mốc đối chiếu cần dẫn lại ở Chương 4:

- **Hiệu năng**: [2] đạt **6 FPS** trên Raspberry Pi 400 với pipeline **chưa có** anti-spoofing.
  Nghiên cứu này đặt mục tiêu ≥ 5 FPS trên Raspberry Pi 5 với pipeline **có thêm** khối chống
  giả mạo — Pi 5 mạnh hơn đáng kể nên mục tiêu là hợp lý, nhưng con số 6 FPS là mốc so sánh trực tiếp.
- **Quy mô đánh giá**: [2] đạt 99,976 % trên 10 danh tính. Nghiên cứu này có gallery 2–3 người,
  tức bài toán phân biệt còn đơn giản hơn; đó chính là lý do phải bổ sung ba tập impostor và
  báo cáo FAR thay vì dựa vào accuracy.

### Cách viết thành văn xuôi

Với 4 công trình, viết theo **cặp**: hai công trình nước ngoài trước, hai công trình trong nước sau,
mỗi cặp kết bằng một đoạn nhận xét chung.

Mỗi công trình trình bày theo đúng thứ tự: **bài toán → phương pháp → kết quả → hạn chế**.
Đoạn "hạn chế" là đoạn có giá trị nhất, không được bỏ.

❌ Không viết kiểu: *"Tác giả A làm X. Tác giả B làm Y."* — phải có đối chiếu và nhận xét.
❌ Không chê công trình khác để nâng đồ án. Nêu hạn chế **về mặt phạm vi**, ví dụ:
*"nghiên cứu này tập trung vào độ chính xác nhận diện và chưa đánh giá khả năng chống giả mạo"* —
đó là mô tả trung lập, không phải phê phán.

---

## 1.3. Xác định vấn đề

Từ kết quả khảo sát ở mục 1.2, có thể nhận thấy ba khoảng trống chung của các công trình đã xét.

**Thứ nhất, chưa có cơ sở đối chiếu định lượng giữa các phương án thuật toán trên cùng một điều kiện
đo.** Bốn công trình sử dụng bốn tổ hợp thuật toán khác nhau ở cả khâu phát hiện lẫn khâu trích xuất
đặc trưng, nhưng mỗi nghiên cứu chỉ triển khai và đánh giá một phương án đã chọn sẵn. Ngoại lệ duy
nhất là [1] có so sánh HOG với CNN, song phép so sánh này chỉ dừng ở độ chính xác mà không kèm số
liệu tốc độ — trong khi chi phí tính toán mới là ràng buộc quyết định trên thiết bị biên. Hệ quả là
khi cần lựa chọn thuật toán cho một hệ thống nhúng cụ thể, các kết quả đã công bố không cung cấp đủ
căn cứ: chúng được đo trên phần cứng khác nhau, bộ dữ liệu khác nhau và điều kiện khác nhau, nên
không thể quy về cùng một thang để đánh giá đánh đổi giữa độ chính xác và tốc độ.

Riêng ở khâu **phát hiện khuôn mặt**, khoảng trống này còn rõ hơn. Các công trình khảo sát đều dùng
phương pháp xếp tầng hoặc đa giai đoạn — Haar Cascade [2], [4], MTCNN [3], HOG và CNN [1] — vốn phải
duyệt ảnh nhiều lần hoặc qua nhiều bộ phân lớp nối tiếp, khiến thời gian xử lý biến thiên theo nội
dung khung hình. Họ mô hình phát hiện một giai đoạn, dự đoán đồng thời vị trí và độ tin cậy trong một
lần duyệt ảnh, chưa được khảo sát trong nhóm công trình này dù được thiết kế hướng tới suy luận thời
gian thực. Tương tự, ở khâu trích xuất đặc trưng, các hàm mất mát dựa trên biên góc — hiện là chuẩn
cho nhận diện khuôn mặt độ chính xác cao — cũng chưa xuất hiện trong nhóm khảo sát.

**Thứ hai, không công trình nào tích hợp cơ chế phát hiện giả mạo.** Cả bốn hệ thống đều nhận diện
chính xác khuôn mặt thật, nhưng không phân biệt được người thật với ảnh in hoặc màn hình điện thoại
hiển thị ảnh của người đã đăng ký. Đối với hệ thống chỉ hiển thị hoặc ghi nhận danh tính, hạn chế này
ít ảnh hưởng. Đối với hệ thống điều khiển thiết bị trong nhà, nó tạo ra một đường tấn công đơn giản
và chi phí thấp: chỉ cần một bức ảnh của chủ nhà. Việc bổ sung khối này cũng đặt ra một bài toán kỹ
thuật riêng, vì nó tiêu tốn thêm tài nguyên trên một pipeline vốn đã sát giới hạn của thiết bị.

**Thứ ba, các nghiên cứu đánh giá hệ thống theo bài toán tập đóng (closed-set) mà không báo cáo tỉ lệ
chấp nhận sai (False Acceptance Rate — FAR).** Cả bốn công trình đều công bố độ chính xác trên tập
kiểm thử chỉ gồm những người đã đăng ký. Trong khi đó, một hệ thống mở khoá thiết bị vận hành trong
điều kiện tập mở (open-set): người xuất hiện trước camera có thể là bất kỳ ai, phần lớn là người chưa
từng được đăng ký. Với bài toán này, độ chính xác trên người đã đăng ký phản ánh mức độ thuận tiện,
còn tỉ lệ chấp nhận sai mới phản ánh năng lực an ninh. Một hệ thống đạt độ chính xác cao vẫn có thể
cấp quyền điều khiển thiết bị cho người lạ nếu ngưỡng quyết định được đặt quá rộng, và hiện tượng này
không thể phát hiện được nếu chỉ đo độ chính xác.

Ba khoảng trống trên gắn liền với nhau khi triển khai thực tế. Ba trong bốn công trình dừng ở xác định
danh tính [1], [2], [4]; công trình duy nhất có điều khiển thiết bị [3] lại đánh giá khối nhận diện
theo hướng định tính. Do đó chưa có nghiên cứu nào trong nhóm khảo sát đo đồng thời độ chính xác,
tốc độ xử lý, khả năng chặn tấn công giả mạo và độ trễ điều khiển trên cùng một hệ thống hoàn chỉnh —
trong khi chính các phép đo đồng thời đó mới bộc lộ được đánh đổi giữa an ninh, độ trễ và tài nguyên
tính toán, vấn đề trung tâm của triển khai trên thiết bị biên.

Bối cảnh hộ gia đình làm những khoảng trống này đáng quan tâm hơn. Khác với hệ thống chấm công hay
kiểm soát ra vào doanh nghiệp, hệ thống nhà thông minh hoạt động không có người giám sát, số người
dùng đăng ký ít nhưng số người lạ có thể tiếp cận lại không giới hạn, và hậu quả của một lần chấp
nhận sai là quyền điều khiển thiết bị điện trong nhà.

Từ đó, nghiên cứu này đặt bài toán như sau: xây dựng hệ thống nhận diện khuôn mặt chạy hoàn toàn cục
bộ trên Raspberry Pi 5, trong đó khâu phát hiện khuôn mặt sử dụng mô hình một giai đoạn hướng thời
gian thực, khâu trích xuất đặc trưng được **triển khai theo hai phương án và so sánh định lượng trên
cùng phần cứng, cùng bộ dữ liệu và cùng kịch bản đo**. Hệ thống tích hợp thêm khối phát hiện giả mạo
và khối điều khiển thiết bị theo phân quyền danh tính, đồng thời được đánh giá theo tiêu chí tập mở
với tỉ lệ chấp nhận sai đo trên các tập người lạ độc lập, bên cạnh độ chính xác, tốc độ xử lý và độ
trễ điều khiển đo trực tiếp trên phần cứng triển khai.

---

## 1.4. Đóng góp của đồ án

`[CHƯA VIẾT]` — ~1 trang · ⏳ **viết ở Phase 8**, sau khi có kết quả Phase 3–7

Chưa viết được bây giờ vì mỗi đóng góp phải kèm bằng chứng định lượng từ `results/`.
Dự kiến gồm:

- So sánh định lượng hai phương án nhận diện trên cùng phần cứng, cùng bộ dữ liệu `[CHƯA ĐO]`
- Đánh giá open-set bằng **ba tập impostor** và quy trình kiểm chứng domain adaptation `[CHƯA ĐO]`
- Hệ thống hoàn chỉnh chạy hoàn toàn cục bộ trên Raspberry Pi 5 `[CHƯA ĐO]`

---

## 1.5. Cấu trúc báo cáo

`[CHƯA VIẾT]` — ~0,5 trang · ⏳ viết cuối cùng

Mỗi chương một câu. Viết sau khi các chương đã ổn định để khỏi phải sửa lại.

---

## Tài liệu cần tìm bản gốc

Bốn công trình sau **bắt buộc** phải trích bản gốc, không trích qua blog hay bài tổng hợp:

| Công trình | Loại |
|---|---|
| ArcFace — hàm mất mát margin góc cho nhận diện khuôn mặt | Hội nghị (CVPR) |
| MobileFaceNets — mạng nhẹ cho thiết bị di động | Hội nghị |
| FaceNet — embedding và triplet loss | Hội nghị (CVPR) |
| LFW — bộ dữ liệu đánh giá | Báo cáo kỹ thuật |

⚠️ **Bẫy trích dẫn**: **YOLOv8** (Ultralytics) và **Silent-Face-Anti-Spoofing / MiniFASNet**
(MiniVision) **không có bài báo bình duyệt**. Phải trích dạng *tài liệu kỹ thuật / kho mã nguồn*
kèm ngày truy cập, và nêu rõ trong bài rằng đây là dự án mã nguồn mở. Ghi chúng như paper
bình duyệt là lỗi hội đồng bắt được.

Chuẩn anti-spoofing **ISO/IEC 30107-3** (APCER/BPCER/ACER) trích dạng tiêu chuẩn.

Mọi mục điền vào `report/refs.bib`, đánh số IEEE theo **thứ tự xuất hiện** trong bài.

---

## Checklist hoàn thành Chương 1

- [ ] Đủ **2 công trình nước ngoài + 2 trong nước**, bảng làm việc §1.2 điền đủ cột cho cả 4
- [ ] Công trình trong nước là đồ án/luận văn thì đã **ghi rõ loại tài liệu và tên trường**
- [ ] Bảng 1.1 có đủ 4 công trình + dòng cuối là đồ án này
- [ ] Có câu nói rõ **bảng 1.1 không phải bảng xếp hạng** (điều kiện đo khác nhau)
- [ ] Mỗi công trình trình bày đủ 4 phần: bài toán → phương pháp → kết quả → hạn chế
- [ ] §1.3 rút ra trực tiếp từ cột "Hạn chế", không có kết luận nào thiếu dẫn chứng
- [ ] Mọi trích dẫn `[n]` có mục tương ứng trong `refs.bib`, không có tài liệu "mồ côi"
- [ ] YOLOv8 và MiniFASNet trích đúng dạng tài liệu kỹ thuật, có ghi chú
- [ ] Không dùng ngôi thứ nhất ("em", "tôi", "mình")
- [ ] Không còn `[CHƯA VIẾT]` hay `[CHƯA ĐO]` sót lại
- [ ] Số thập phân dùng **dấu phẩy**, đơn vị có khoảng trắng: `96,8 %` · `18,4 ms`
- [ ] Độ dài ~7 trang
