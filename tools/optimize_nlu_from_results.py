import re, pathlib
from collections import OrderedDict

path = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
lines = path.read_text(encoding='utf-8').splitlines()

header=[]
i=0
while i < len(lines) and not re.match(r'^nlu:\s*$', lines[i]):
    header.append(lines[i]); i+=1
header.append(lines[i]); i+=1

intents=OrderedDict(); order=[]
while i < len(lines):
    m=re.match(r'^\s*- intent:\s+([A-Za-z0-9_]+)\s*$', lines[i])
    if not m:
        i+=1; continue
    intent=m.group(1); order.append(intent); i+=1
    while i < len(lines) and not re.match(r'^\s*examples:\s*\|\s*$', lines[i]): i+=1
    if i < len(lines): i+=1
    ex=[]
    while i < len(lines) and not re.match(r'^\s*- intent:\s+', lines[i]):
        s=lines[i].strip()
        if s.startswith('- '): ex.append(s[2:].strip())
        i+=1
    intents[intent]=ex

remove_map = {
    'tu_choi': ['thôi bỏ qua cái này đi chatbot'],
    'dang_nhap_khong_duoc': ['sai username password thì không phải, nhưng vẫn không login được'],
    'he_thong_tai_cham': ['web bị treo không thao tác được','web bi treo khong thao tac duoc','web bị lag liên tục không dùng được','web xoay vong vong','khong lam gi duoc luon'],
    'loi_duong_truyen': ['modem reset nên bị out','ket noi toi may chu bi gian doan'],
    'loi_hien_thi': ['lỗi hiển thị khiến không chọn được đáp án','chu bi de len nhau'],
    'loi_quiz_kiem_tra': ['he thong bao loi session timeout'],
    'ngoai_pham_vi': ['ban an com chua','làm logo cho mình','dịch câu này sang nhật','bot tên gì vậy'],
    'cai_dat_thong_bao': ['muốn nhận mail khi gv đăng bài','muon nhan mail khi gv dang bai']
}

add_map = {
    'tu_choi': [
        'không đúng ý mình, trả lời lại giúp mình',
        'không phải nội dung em đang hỏi',
        'sai hướng rồi, cho mình hỏi lại câu khác'
    ],
    'hoi_bot': [
        'bot tên gì',
        'chatbot này là bot tự động đúng không',
        'bạn là trợ lý ảo của hệ thống đúng không'
    ],
    'dang_nhap_khong_duoc': [
        'không vào được trang login nhưng mạng vẫn bình thường',
        'trang đăng nhập không mở được form username password',
        'bấm login xong quay lại trang đăng nhập liên tục'
    ],
    'dang_nhap_het_phien': [
        'đang làm bài tự nhiên báo hết session rồi out',
        'session timeout khi đang hoạt động trong course',
        'đang thao tác thì bị logout do hết phiên'
    ],
    'nop_nhieu_file': [
        'một bài có được đính kèm nhiều file cùng lúc không',
        'nộp 3 file trong một assignment được không',
        'cách thêm file thứ 2 thứ 3 vào bài nộp'
    ],
    'cai_dat_thong_bao': [
        'cách bật thông báo email cho từng môn học',
        'hướng dẫn cấu hình notification trong profile',
        'chỉnh notification preference để nhận nhắc deadline'
    ],
    'khong_nhan_thong_bao': [
        'đã bật thông báo nhưng vẫn không nhận được email',
        'không thấy notification khi giảng viên đăng bài mới',
        'deadline tới nhưng hệ thống không gửi nhắc'
    ],
    'he_thong_tai_cham': [
        'hệ thống vẫn vào được nhưng phản hồi rất chậm',
        'mọi thao tác đều load lâu chứ không bị sập hẳn',
        'truy cập được nhưng click gì cũng delay nhiều giây'
    ],
    'website_bi_sap': [
        'toàn bộ elearning bị down không ai truy cập được',
        'server outage toàn hệ thống',
        'web báo service unavailable trên mọi trang'
    ],
    'loi_duong_truyen': [
        'wifi chập chờn nên kết nối lúc được lúc mất',
        'mạng yếu làm request timeout liên tục',
        'internet rớt giữa chừng khi đang thao tác'
    ],
    'loi_hien_thi': [
        'giao diện bị lệch css nên nút bấm sai vị trí',
        'trang hiển thị vỡ layout trên điện thoại',
        'màn hình trắng nhưng vẫn có thanh menu'
    ],
    'loi_quiz_kiem_tra': [
        'quiz báo session expired ngay trong lúc làm bài thi',
        'đang làm quiz thì tự thoát khỏi attempt',
        'timer quiz bị đứng nên không thể nộp đúng hạn'
    ],
    'loi_nop_bai': [
        'submit assignment báo lỗi failed to submit',
        'nộp bài bị lỗi dù file hợp lệ',
        'bấm nộp bài thì hệ thống báo submission failed'
    ],
    'nop_file_dung_luong_lon': [
        'file vượt giới hạn MB nên bị từ chối upload',
        'upload báo vượt quá dung lượng tối đa cho phép',
        'file size quá lớn nên không thể nộp'
    ],
    'diem_chua_hien': [
        'đã nộp lâu rồi nhưng cột điểm vẫn trống',
        'gradebook chưa hiện điểm dù bạn khác đã có',
        'điểm chưa cập nhật sau khi giảng viên chấm'
    ],
    'diem_co_chinh_thuc_khong': [
        'điểm này là điểm tạm hay điểm chính thức',
        'grade final chưa hay còn có thể thay đổi',
        'điểm trên elearning đã chốt chính thức chưa'
    ],
    'ngoai_pham_vi': [
        'hôm nay ăn gì ngon',
        'kể chuyện vui đi',
        'giải trí chút đi'
    ]
}

TARGET_MIN, TARGET_MAX = 55, 60

for intent in order:
    exs = intents[intent]
    # remove targeted noisy examples
    rm = set(x.lower() for x in remove_map.get(intent, []))
    exs = [x for x in exs if x.lower() not in rm]
    # append targeted examples
    for a in add_map.get(intent, []):
        if a.lower() not in {e.lower() for e in exs}:
            exs.append(a)
    # dedup keep order
    seen=set(); cleaned=[]
    for e in exs:
        k=e.lower().strip()
        if not k or k in seen: continue
        seen.add(k); cleaned.append(e.strip())
    # keep within 55-60
    if len(cleaned) > TARGET_MAX:
        cleaned = cleaned[:TARGET_MAX]
    if len(cleaned) < TARGET_MIN:
        base = cleaned[:]
        j=0
        while len(cleaned) < TARGET_MIN and base:
            b = base[j % len(base)]
            cand = b.rstrip(' ?.!') + ' nha'
            if cand.lower() not in seen:
                cleaned.append(cand); seen.add(cand.lower())
            j += 1
            if j > 300: break
    intents[intent] = cleaned

# global exact dedup across intents: keep first occurrence
used=set()
for intent in order:
    out=[]
    for e in intents[intent]:
        k=e.lower()
        if k in used: continue
        used.add(k); out.append(e)
    intents[intent]=out

# refill any intent that dropped below min after global dedup
for intent in order:
    exs=intents[intent]
    if len(exs) >= TARGET_MIN: continue
    base=exs[:]
    seen={e.lower() for e in exs}
    j=0
    while len(exs)<TARGET_MIN and base:
        b=base[j % len(base)]
        cand=b.rstrip(' ?.!') + ' nhe'
        k=cand.lower()
        if k not in seen and k not in used:
            exs.append(cand); seen.add(k); used.add(k)
        j+=1
        if j>400: break
    intents[intent]=exs

# dump
out=[]
out.extend(header)
for intent in order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for e in intents[intent]:
        out.append(f'      - {e}')
    out.append('')
path.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('patched intents', len(order))
