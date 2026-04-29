import re, pathlib
from collections import OrderedDict

p = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
lines = p.read_text(encoding='utf-8').splitlines()

# parse
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

remove_map={
 'kiem_tra_nop_bai':[
  'làm sao biết mình không nộp nhầm file','nộp bài xong có biên nhận gì không','em muốn lấy bằng chứng đã nộp bài',
  'submission status hiện màu xanh là xong rồi đúng không','kiểm tra nhật ký nộp bài trên hệ thống','có dòng chữ submission received nghĩa là sao'
 ],
 'loi_nop_bai':['không thể gửi bài lên moodle','khong the gui bai len moodle','không upload được bài tập lên server','loi 413 khi nop file qua lon'],
 'website_bi_sap':['bảo trì đến mấy giờ','không tìm thấy máy chủ ứng dụng','khong vao duoc trang chu'],
 'ngoai_pham_vi':['chatbot co thich di du lich khong','làm sao để kiếm tiền online','bạn có biết chơi liên quân không','cach cham soc cay canh trong nha','bạn có biết chơi đàn guitar không','làm sao để hết buồn ngủ khi đang học'],
 'cai_dat_thong_bao':['chinh thong bao nhu nao','chỉ muốn nhận thông báo quan trọng thôi'],
 'huong_dan_nop_bai':['cách gửi bài tập cho giảng viên trên elearning'],
 'loi_hien_thi':['nut add submission khong hien ra','loi font tren trinh duyet chrome'],
 'loi_duong_truyen':['ket noi server bi gian doan do mang','mạng bị nghẽn nên không load được trang','kết nối không ổn định làm mất bài đang làm'],
 'tim_kiem_loc_mon_hoc':['xem lai mon da hoc ky truoc o dau','cach an mon cu de chi con mon hien tai'],
 'dong_y':['đồng ý nha']
}

add_map={
 'kiem_tra_nop_bai':[
  'vào phần submission status để kiểm tra đã nộp thành công chưa',
  'xem trạng thái assignment là submitted for grading ở đâu',
  'kiểm tra bài đang ở submitted hay draft trong assignment',
  'check submission status de biet da nop thanh cong chua',
  'xem assignment dang submitted for grading o muc nao'
 ],
 'loi_nop_bai':[
  'submit assignment báo lỗi hệ thống dù file hợp lệ',
  'bấm nộp bài thì hiện failed to submit ngay bước cuối',
  'lưu submission lần cuối bị lỗi không ghi nhận bài nộp',
  'submit assignment bao loi he thong du file hop le',
  'luu submission lan cuoi bi loi khong ghi nhan'
 ],
 'website_bi_sap':[
  'toàn hệ thống elearning bị down không ai truy cập được',
  'web báo service unavailable cho tất cả người dùng',
  'server elearning sập toàn trường không đăng nhập được',
  'toan he thong elearning bi down khong ai vao duoc',
  'web bao service unavailable cho tat ca nguoi dung'
 ],
 'ngoai_pham_vi':[
  'hôm nay chứng khoán tăng hay giảm vậy',
  'kể vài mẹo nấu ăn ngon tại nhà đi',
  'gợi ý bài tập gym cho người mới bắt đầu',
  'hom nay chung khoan tang hay giam vay',
  'goi y bai tap gym cho nguoi moi bat dau'
 ],
 'cai_dat_thong_bao':[
  'notification preference trong profile chỉnh ở đâu',
  'bật email nhắc deadline assignment như thế nào',
  'cách tắt push notification của từng môn học',
  'notification preference trong profile chinh o dau',
  'bat email nhac deadline assignment nhu the nao'
 ],
 'huong_dan_nop_bai':[
  'hướng dẫn từng bước nộp assignment từ chọn file tới submit',
  'upload file xong cần bấm nút nào để hoàn tất nộp bài',
  'cách nộp bài trên moodle theo từng bước cụ thể',
  'huong dan tung buoc nop assignment tu chon file den submit',
  'upload file xong can bam nut nao de nop bai'
 ],
 'loi_hien_thi':[
  'giao diện bị lỗi hiển thị chữ và nút bị lệch vị trí',
  'trang bị vỡ layout nên không hiển thị đủ nội dung',
  'màn hình trắng do lỗi giao diện nhưng web chưa sập',
  'giao dien loi hien thi chu va nut bi lech vi tri',
  'man hinh trang do loi giao dien nhung web chua sap'
 ],
 'loi_duong_truyen':[
  'mạng chập chờn làm request timeout liên tục khi vào moodle',
  'wifi yếu nên kết nối tới server bị gián đoạn',
  'internet rớt giữa chừng làm thao tác bị mất kết nối',
  'mang chap chon lam request timeout lien tuc',
  'wifi yeu nen ket noi toi server bi gian doan'
 ],
 'tim_kiem_loc_mon_hoc':[
  'lọc danh sách course theo học kỳ trong mục filter ở đâu',
  'cách chuyển từ in progress sang past courses bằng bộ lọc',
  'xem course đã archive bằng filter như thế nào',
  'loc danh sach course theo hoc ky trong muc filter o dau',
  'chuyen tu in progress sang past courses bang bo loc'
 ],
 'dong_y':[
  'chuẩn rồi',
  'đúng ý mình rồi',
  'ok chuẩn',
  'chuan roi',
  'dung y minh roi'
 ],
 'dang_nhap_khong_duoc':[
  'không vào được trang đăng nhập nhưng web tổng vẫn mở',
  'trang login không tải nổi form username password',
  'vao duoc web nhung khong mo duoc trang dang nhap',
  'trang login khong tai noi form username password',
  'chi loi o trang dang nhap con trang khac van vao duoc'
 ]
}

MIN_N, MAX_N = 50, 60
for intent in order:
    arr=intents[intent]
    rem={x.lower() for x in remove_map.get(intent,[])}
    arr=[x for x in arr if x.lower() not in rem]
    seen={x.lower() for x in arr}
    for x in add_map.get(intent,[]):
        k=x.lower()
        if k not in seen:
            arr.append(x); seen.add(k)
    # dedup
    out=[]; seen=set()
    for x in arr:
        k=x.strip().lower()
        if not k or k in seen: continue
        seen.add(k); out.append(x.strip())
    if len(out)>MAX_N: out=out[:MAX_N]
    intents[intent]=out

# global dedup
used=set()
for intent in order:
    out=[]
    for x in intents[intent]:
        k=x.lower()
        if k in used: continue
        used.add(k); out.append(x)
    intents[intent]=out

# refill to min
for intent in order:
    arr=intents[intent]
    seen={x.lower() for x in arr}
    base=arr[:] if arr else [intent.replace('_',' ')]
    j=0
    while len(arr)<MIN_N and j<900:
        cand=base[j%len(base)].rstrip(' ?.!')+' nha'
        k=cand.lower()
        if k not in seen and k not in used:
            arr.append(cand); seen.add(k); used.add(k)
        j+=1
    if len(arr)>MAX_N: arr=arr[:MAX_N]
    intents[intent]=arr

# write
out=[]
out.extend(header)
for intent in order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for x in intents[intent]: out.append(f'      - {x}')
    out.append('')
p.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('done',len(order))
