"""
Danh sách cụm từ cho lớp an toàn tất định. Xem docx/04.

⚠️ FILE NÀY LÀ LỚP AN TOÀN. Không cắt, không "tối ưu" cho gọn.
Ưu tiên recall hơn precision — thà báo động nhầm còn hơn bỏ sót.

Hai nhóm khớp:
  EXACT_ACCENTED  — khớp trên văn bản GỐC còn dấu (bẫy "tự tử" / "từ từ")
  NORMALIZED_*    — khớp trên văn bản đã bỏ dấu (bắt được cả khi gõ không dấu)
"""
from __future__ import annotations

# ── Nhóm khớp CÒN DẤU (biên từ) — các cụm dễ trùng sau khi bỏ dấu ───────────
EXACT_ACCENTED_TIER1: list[str] = [
    "tự tử",
    "tự sát",
    "tự vẫn",
    "tự tữ",       # lỗi gõ phổ biến
    "quyên sinh",
]

# ── TẦNG 1 — Ý định rõ ràng → ESCALATE (khớp đã bỏ dấu) ────────────────────
NORMALIZED_TIER1: list[str] = [
    "tu sat", "tu van", "quyen sinh",
    # "tu tu" trần bị bỏ vì trùng "từ từ" — nhưng các cụm có ngữ cảnh thì an toàn:
    "muon tu tu", "di tu tu", "tu tu cho xong", "tu tu di cho roi",
    "tu tu di cho xong", "nghi den chuyen tu tu", "tinh chuyen tu tu",
    "ket thuc cuoc doi", "ket thuc tat ca", "ket lieu doi minh", "ket lieu ban than",
    "khong muon song nua", "khong con muon song", "khong thiet song", "chang thiet song",
    "muon chet", "uoc gi minh chet", "gia nhu minh chet", "chi muon chet", "them chet",
    "tu hai", "tu lam dau minh", "lam dau ban than", "tu lam hai minh", "tu gay thuong tich",
    "rach tay", "cat tay", "cat co tay", "cua tay",
    "uong het thuoc", "uong ca vi thuoc", "uong that nhieu thuoc", "uong het vi thuoc",
    "uong het loc thuoc", "uong hon mot vi thuoc", "uong thuoc ngu qua lieu", "qua lieu thuoc",
    "nhay lau", "nhay cau", "treo co",
    "bien mat vinh vien", "khong con ton tai",
    "self harm", "self-harm", "suicide", "suicidal", "kill myself", "end it all", "end my life",
    "want to die",
]

# Ngữ cảnh phủ định — nếu cụm ở NORMALIZED_TIER1 đứng ngay trước một trong các
# token này thì KHÔNG tính là khớp (docx/04 §4 — "cắt tay áo").
NEGATIVE_CONTEXT: dict[str, list[str]] = {
    "cat tay": ["ao", "ao so mi", "ao dai"],
    "rach tay": ["ao"],
    "cua tay": ["ao"],
}

# ── TẦNG 2 — Ý niệm thụ động → ESCALATE (giọng nhẹ hơn) ───────────────────
NORMALIZED_TIER2: list[str] = [
    "chan song", "chan doi", "khong thiet tha muon song", "khong con thiet song",
    "muon buong xuoi", "muon tu bo tat ca", "buong bo het", "muon bo cuoc het", "buong xuoi het",
    "song lam gi", "song de lam gi", "ton tai lam gi", "song tiep lam gi", "co gang lam gi nua",
    "khong con y nghia gi", "moi thu vo nghia", "cuoc song vo nghia", "song vo nghia",
    "uoc gi minh bien mat", "muon bien mat cho xong", "chi muon bien mat", "muon bien mat mai mai",
    "gia nhu minh chua tung ton tai", "uoc gi minh chua tung ton tai", "chua tung ton tai",
    "gia nhu minh khong ton tai", "uoc gi minh khong ton tai",
    "minh la ganh nang", "minh chi la ganh nang", "ganh nang cho moi nguoi", "ganh nang cua gia dinh",
    "khong co minh se tot hon", "khong co minh moi nguoi do kho", "khong co minh thi tot hon",
    "khong co minh chac moi nguoi do kho hon", "khong co minh moi nguoi se do kho hon",
    "khong co minh se do kho hon", "khong co minh moi nguoi do kho hon",
]

# ── TẦNG 3 — Kiệt quệ / mất kiểm soát → ép gate BRIDGE (vẫn gọi LLM) ──────
NORMALIZED_TIER3: list[str] = [
    "kiet suc", "kiet que", "kiet que tinh than", "qua suc chiu dung",
    "mat kiem soat", "khong kiem soat duoc ban than", "khong con ly tri",
    "khong chiu noi nua", "khong con suc", "guc nga", "sap guc",
    "khong biet phai lam gi nua", "be tac hoan toan", "duong cung",
    "khong ai hieu minh", "chi co mot minh", "co don qua",
]

# ── POST-CHECK — chặn ở đầu ra (khớp đã bỏ dấu). docx/04 §6 ───────────────
POSTCHECK_DIAGNOSIS: list[str] = [
    "ban bi tram cam", "ban dang bi tram cam", "ban mac tram cam", "ban co dau hieu tram cam",
    "ban bi roi loan", "ban co roi loan", "ban bi lo au", "ban mac chung lo au",
    "ban mac chung", "ban bi benh", "chan doan",
    "ban co sieu toi trung phat", "ban bi sieu toi trung phat", "ban co cai sieu toi trung phat",
    "ban dang mac", "trieu chung cua ban cho thay ban bi",
]

POSTCHECK_MEDICAL_PROMISE: list[str] = [
    "se khoi", "se het thoi", "chac chan se on", "minh dam bao", "roi se on thoi",
    "moi chuyen se on thoi", "chac chan se khoi",
    "ban khong sao dau", "khong co gi nghiem trong",
    "ban nen uong", "nen dung thuoc", "lieu trinh", "nen uong thuoc",
]

# Rò rỉ nội bộ — tiền tố node_id + từ khoá hệ thống
NODE_ID_PREFIXES: tuple[str, ...] = ("m-", "a-", "i-", "t-", "k-", "c-", "s-", "r-")
POSTCHECK_INTERNAL_WORDS: list[str] = [
    "confidence", "overlay", "inferred", "self_report", "self report",
    "gate", "escalate", "clarify", "reflect", "support", "bridge",
    "node_id", "target_node", "policy edge", "policy_edge",
]

# ── CHIP — tiền tố hệ thống (docx/04 §5) ─────────────────────────────────
CHIP_CONFIRM_YES = "✓ "
CHIP_CONFIRM_NO = "✗ "
# docx/11 §E5 — "Đúng một phần". Nhị phân Đúng/Không hẳn ép học sinh xác nhận
# cả dòng sai hoặc vứt cả 3 dòng đúng; thực tế họ sẽ bấm "Đúng vậy" cho xong.
CHIP_CONFIRM_PARTIAL = "~ "
CHIP_ASK = "? "
CHIP_DECLINE = "— "
# docx/03 §7 luật 12 — chip TÌM HIỂU của chế độ chủ đề. CỐ Ý là tiền tố RIÊNG,
# không tái dùng CHIP_ASK ("? "): prefix đó đang mang nghĩa "chip nội dung
# người dùng chọn để TRẢ LỜI", còn chip này là người dùng HỎI bot về khái niệm.
# Trộn hai thứ thì detect_chip() không phân biệt được, và gate sẽ đối xử với
# một câu hỏi kiến thức như một câu trả lời — hỏng cả hai đường.
CHIP_LEARN = "◦ "
CHIP_PREFIXES: tuple[str, ...] = (
    CHIP_CONFIRM_YES, CHIP_CONFIRM_NO, CHIP_CONFIRM_PARTIAL,
    CHIP_ASK, CHIP_DECLINE, CHIP_LEARN,
)

# Câu an toàn thay thế khi post-check chặn chẩn đoán (docx/04 §6.1)
SAFE_REPLACEMENT_DIAGNOSIS = (
    "Mình không đủ khả năng để nói bạn đang gặp vấn đề gì — chuyện đó cần một "
    "người có chuyên môn. Nhưng mình vẫn ở đây để nghe bạn kể."
)
SAFE_REPLACEMENT_GENERIC = (
    "Mình đang hơi chậm, bạn nhắn lại giúp mình nhé."
)

# ── Rò NHÃN NODE ra câu trả lời (docx/11 D6) ─────────────────────────────
# Nhãn node là chữ NỘI BỘ, đi vào prompt qua {TARGET_NODE_LABEL}. 08/09/2026
# quan sát được ở lượt 1: bot viết "nghe như bạn đang thấy mình ĐÁNG BỊ TRÁCH
# PHẠT" — đúng nhãn của node đang nhắm, trong khi học sinh mới nói mỗi chuyện
# điểm số. 11_CLARIFY.md đã cấm bằng lời, nhưng lời trong prompt không phải là
# chốt chặn. Câu thay thế phải VẪN LÀ MỘT LƯỢT CLARIFY HỢP LỆ — thay bằng câu
# "mình không đủ khả năng chẩn đoán" ở đây là lạc đề.
SAFE_REPLACEMENT_LABEL_LEAK = (
    "Mình chưa dám đoán gì về bạn cả. Lúc đó trong đầu bạn nghĩ gì?"
)

# Câu thay thế khi bot hỏi lại đúng câu của lượt trước (docx/11 D9). Cố ý
# THÚ NHẬN là mình hỏi lặp thay vì hỏi tiếp một câu thứ ba cùng kiểu — người
# dùng đã thấy sự lặp đó rồi, giả vờ không có mới là thứ làm họ đóng tab.
SAFE_REPLACEMENT_LAP_CAU_HOI = (
    "Mình vừa hỏi đi hỏi lại một chuyện rồi. Bạn kể theo cách của bạn đi, "
    "điều gì đang làm bạn nặng nhất?"
)

# Từ bị bỏ khi cắt nhãn thành cụm — chúng là chữ nối, không mang phán quyết.
# "Cảm thấy chưa đủ tốt" -> cụm cần bắt là "chua du tot", không phải "cam thay".
LABEL_STOPWORDS: frozenset[str] = frozenset({
    "cam", "thay", "nghi", "minh", "khi", "voi", "ve", "va", "cho", "bi", "la",
    "rat", "kha", "hay", "co", "cua", "trong", "mot", "cach", "ban", "than",
})

# ── Câu hỏi ĐÓNG ở gate CLARIFY (docx/04 §6.5) ───────────────────────────
# CLARIFY luật 3 cấm câu hỏi có/không, luật 4 cấm mớm triệu chứng. Prompt đã
# ghi rõ nhưng LLM vẫn phá — quan sát thực tế 07/09/2026: "Có phải bạn đang
# cảm thấy khó khăn trong việc chấp nhận bản thân mình không?". Đây là chốt
# chặn tất định, không phụ thuộc mô hình có nghe lời hay không.
#
# CHỈ áp ở CLARIFY. REFLECT ĐƯỢC PHÉP hỏi xác nhận — đó là việc của nó.
POSTCHECK_CLOSED_QUESTION: list[str] = [
    "co phai ban",
    "co phai la ban",
    "phai khong",
    "dung khong",
    "dung chu",
    "co dung khong",
]

# Câu hỏi mở thay thế. Lấy từ chính ví dụ ✅ trong 11_CLARIFY.md để giữ giọng.
SAFE_OPEN_QUESTION = "Lúc đó trong đầu bạn nghĩ gì?"


# ── Bịa trí nhớ xuyên phiên (docx/04 §6.6) ───────────────────────────────
# Bot KHÔNG giữ nội dung phiên trước (docx/12 §2) — bộ nhớ dài hạn chỉ có
# trọng số node, không có câu chữ. Nói "mình nhớ bạn từng…" là hứa một thứ
# không có: người dùng hỏi tiếp chi tiết thì lòi ra ngay.
# Quan sát 07/09/2026: bot nói "Mình nhớ bạn từng nhắc đến chuyện điểm số",
# người dùng lập tức hỏi "hồi đó mình được bao nhiêu điểm nhỉ?".
#
# Trong CÙNG một phiên bot vẫn trích dẫn được — nhưng bằng ngoặc kép
# ("Bạn nói ..."), không bằng mấy cụm dưới đây.
POSTCHECK_FAKE_MEMORY: list[str] = [
    "minh nho ban tung",
    "minh van nho",
    "minh con nho",
    "nhu ban da ke lan truoc",
    "lan truoc ban noi",
    "lan truoc ban ke",
    "hom truoc ban noi",
    "hom truoc ban ke",
    "buoi truoc ban",
    "lan truoc chung ta",
]

SAFE_REPLACEMENT_FAKE_MEMORY = (
    "Thành thật thì mình không giữ lại nội dung những lần trò chuyện trước, "
    "nên không nhớ chi tiết đâu. Bạn kể lại cho mình nghe được không?"
)
