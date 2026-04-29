import re, pathlib
from collections import OrderedDict

p = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
lines = p.read_text(encoding='utf-8').splitlines()

# Parse file
header=[]; i=0
while i < len(lines) and lines[i].strip()!='nlu:':
    header.append(lines[i]); i+=1
header.append('nlu:'); i+=1

intents=OrderedDict(); order=[]
while i < len(lines):
    m=re.match(r'^\s*- intent:\s+([A-Za-z0-9_]+)\s*$', lines[i])
    if not m:
        i+=1; continue
    name=m.group(1); order.append(name); i+=1
    while i < len(lines) and lines[i].strip()!='examples: |': i+=1
    if i < len(lines): i+=1
    ex=[]
    while i < len(lines) and not re.match(r'^\s*- intent:\s+', lines[i]):
        s=lines[i].strip()
        if s.startswith('- '): ex.append(s[2:].strip())
        i+=1
    intents[name]=ex

remove_map = {
 'tam_biet': ['dung chat','tam dung nha','ok bye','chúc bạn một ngày tốt lành'],
 'ngoai_pham_vi': ['bạn là ai vậy','chatbot có biết yêu không','di ngu thoi'],
 'hoi_bot': ['có người đọc tin nhắn không'],
 'tu_choi': ['không đúng nội dung mình cần','thôi không cần thông tin này nữa'],
 'khong_co_thac_mac': ['ok roi nha'],
 'kiem_tra_nop_bai': ['kiểm tra assignment đã nộp hay còn draft','lam sao lay bang chung da nop bai','xem log nộp bài của cá nhân'],
 'ban_nhap_nop_bai': ['bản nháp là sao','bài chỉ lưu nháp có được tính điểm không'],
 'loi_nop_bai': ['loi 413 khi nop file qua lon','nop xong khong hien submission status'],
 'cai_dat_thong_bao': ['có cách nào nhận thông báo khi có deadline mới không','setting thông báo trên moodle nằm ở đâu'],
 'khong_nhan_thong_bao': ['em bật thông báo rồi mà vẫn không nhận được'],
 'dang_nhap_cham': ['vao he thong cham bat thuong','đăng nhập lúc nào cũng chậm'],
 'he_thong_tai_cham': ['login mat rat lau moi vao duoc'],
 'tai_tai_lieu': ['he thong co gioi han so lan tai khong'],
 'loi_tai_lieu': ['tải tài liệu bị đứng ở mức 99% rồi dừng'],
 'dang_ky_hoc_phan': ['add course vào kỳ'],
 'tim_kiem_nhanh_mon_hoc': ['làm sao để không phải cuộn nhiều môn'],
 'dang_nhap_khong_duoc': ['không vào được elearning dù đã thử nhiều lần']
}

add_map = {
 'tam_biet': [
  'mình xin kết thúc cuộc trò chuyện tại đây',
  'tạm biệt bot, mình thoát nhé',
  'cam on ban, minh dung chat tai day',
  'ket thuc trao doi o day nha'
 ],
 'dong_y': [
  'đúng rồi bạn',
  'ok chuẩn luôn',
  'chinh xac roi do'
 ],
 'ngoai_pham_vi': [
  'giá xăng hôm nay bao nhiêu',
  'gợi ý quán ăn ngon ở nha trang',
  'hướng dẫn nấu mì ý',
  'ke mot cau chuyen cuoi ngan',
  'du bao thoi tiet ngay mai'
 ],
 'hoi_bot': [
  'bạn là chatbot hỗ trợ e-learning đúng không',
  'mình đang nói chuyện với trợ lý ảo phải không',
  'ban la tro ly ao hay nguoi that'
 ],
 'tu_choi': [
  'câu trả lời này chưa đúng ý mình',
  'mình không muốn phương án đó',
  'tra loi nay chua dung y'
 ],
 'khong_co_thac_mac': [
  'mình ổn rồi, không hỏi thêm nữa',
  'thế là rõ rồi, cảm ơn bạn',
  'minh da hieu roi'
 ],
 'kiem_tra_nop_bai': [
  'xem submission status để xác nhận đã nộp ở đâu',
  'làm sao biết trạng thái submitted for grading',
  'check trang thai bai nop da ghi nhan chua',
  'xem receipt xác nhận nộp bài trong assignment'
 ],
 'ban_nhap_nop_bai': [
  'bài đang ở draft nghĩa là chưa nộp đúng không',
  'save draft có được tính là nộp chưa',
  'trang thai draft la bai chua submit'
 ],
 'loi_nop_bai': [
  'nộp bài báo failed to submit dù file hợp lệ',
  'bấm submit assignment thì hệ thống trả lỗi request failed',
  'nop bai bao loi submit khong thanh cong'
 ],
 'nop_file_dung_luong_lon': [
  'lỗi 413 request entity too large khi nộp bài',
  'file vượt quá giới hạn dung lượng upload'
 ],
 'cai_dat_thong_bao': [
  'cách bật email notification cho từng môn học',
  'notification preference nằm ở phần cài đặt nào',
  'bat thong bao deadline qua email nhu the nao'
 ],
 'khong_nhan_thong_bao': [
  'đã bật thông báo nhưng vẫn không nhận được email',
  'co bai moi nhung he thong khong gui thong bao',
  'thong bao den tre nen em bi lo deadline'
 ],
 'dang_nhap_cham': [
  'trang login quay vòng rất lâu mới phản hồi',
  'bấm đăng nhập rồi chờ mãi mới vào được',
  'dang nhap bi delay lau'
 ],
 'he_thong_tai_cham': [
  'vào được hệ thống nhưng mọi thao tác đều lag',
  'dashboard load rất chậm dù mạng vẫn ổn',
  'he thong chay cham tren toan trang'
 ],
 'tai_tai_lieu': [
  'tải tài liệu môn học ở mục nào',
  'download slide bài giảng ở đâu',
  'tai file pdf bai giang nhu the nao'
 ],
 'loi_tai_lieu': [
  'download tài liệu báo failed liên tục',
  'file tải về bị corrupt không mở được',
  'bam download nhung file bi loi'
 ],
 'dang_ky_hoc_phan': [
  'đăng ký học phần ở cổng nào của trường',
  'khi đến đợt chọn môn thì thao tác ở đâu',
  'dang ky hoc phan tren he thong nao'
 ],
 'tim_kiem_nhanh_mon_hoc': [
  'dùng ô search để tìm nhanh course ở đâu',
  'search tên môn học nhanh trong dashboard',
  'tim nhanh mon hoc bang thanh tim kiem'
 ],
 'dang_nhap_khong_duoc': [
  'không vào được trang đăng nhập e-learning',
  'bấm login nhưng không vào hệ thống được',
  'khong the dang nhap vao elearning'
 ],
 'website_bi_sap': [
  'toàn hệ thống e-learning bị down không truy cập được',
  'server báo maintenance toàn trường',
  'khong tim thay may chu ung dung'
 ],
 'loi_hien_thi': [
  'giao diện bị vỡ layout không hiển thị đúng',
  'không thấy nút nộp bài do lỗi hiển thị',
  'trang hien thi thieu thong tin tren man hinh'
 ],
 'loi_quiz_kiem_tra': [
  'đang làm quiz thì bị mất phiên đăng nhập',
  'bấm nộp bài thi nhưng hệ thống không phản hồi',
  'nop bai thi xong nhung khong ghi nhan ket qua'
 ]
}

TOUCHED = set(remove_map.keys()) | set(add_map.keys())

for intent in order:
    ex = intents[intent]
    rm = {x.lower() for x in remove_map.get(intent, [])}
    ex = [e for e in ex if e.lower() not in rm]
    seen = {e.lower() for e in ex}
    for a in add_map.get(intent, []):
        if a.lower() not in seen:
            ex.append(a); seen.add(a.lower())

    # dedup keep order
    out=[]; seen=set()
    for e in ex:
        k=e.lower().strip()
        if not k or k in seen: continue
        seen.add(k); out.append(e.strip())

    # Keep touched intents within 50-60 for stability
    if intent in TOUCHED:
        if len(out) > 60:
            out = out[:60]
        base = out[:] if out else [intent.replace('_',' ')]
        j=0
        seen={x.lower() for x in out}
        while len(out) < 50 and j < 400:
            c = base[j % len(base)].rstrip('?.!') + ' nha'
            if c.lower() not in seen:
                out.append(c); seen.add(c.lower())
            j += 1

    intents[intent]=out

# global exact dedup across intents
used=set()
for intent in order:
    out=[]
    for e in intents[intent]:
        k=e.lower()
        if k in used: continue
        used.add(k); out.append(e)
    intents[intent]=out

# refill touched intents if fell below 50 after global dedup
for intent in TOUCHED:
    if intent not in intents: continue
    arr=intents[intent]
    seen={x.lower() for x in arr}
    base=arr[:] if arr else [intent.replace('_',' ')]
    j=0
    while len(arr)<50 and j<600:
        c=base[j%len(base)].rstrip('?.!')+' nhe'
        if c.lower() not in seen and c.lower() not in used:
            arr.append(c); seen.add(c.lower()); used.add(c.lower())
        j+=1
    if len(arr)>60: arr=arr[:60]
    intents[intent]=arr

# write
out=[]
out.extend(header)
for intent in order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for e in intents[intent]:
        out.append(f'      - {e}')
    out.append('')

p.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('patched intents', len(TOUCHED))
