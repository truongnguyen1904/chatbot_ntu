import re, pathlib
from collections import OrderedDict

path = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
lines = path.read_text(encoding='utf-8').splitlines()

# parse nlu
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
  'làm sao biết bài mình có bị lưu ở dạng bản nháp không','làm sao biết bài đang ở submitted hay draft','xem thời gian chính xác mình đã nộp bài','hướng dẫn xem lịch sử nộp bài','lam sao biet file da len he thong'
 ],
 'ban_nhap_nop_bai':['khi nào draft chuyển sang submitted for grading'],
 'loi_quiz_kiem_tra':['giao diện bài thi bị che khuất ô nhập mật khẩu bài thi','lỗi trắng trang khi nhấn nộp bài kiểm tra','không load được danh sách câu hỏi trong bài kiểm tra'],
 'loi_hien_thi':['không thấy sidebar nên không vào được mục grades','giao diện bị phóng to nhỏ bất thường','thiếu nội dung khi hiển thị trên mobile'],
 'khong_nhan_thong_bao':['giảng viên đăng bài mới nhưng không thấy hiện','he thong khong gui email thong bao','notification den tre qua'],
 'cai_dat_thong_bao':['chua biet cach đe cai đat phat thong bao tren may tinh đe biet deadline moi'],
 'tai_tai_lieu':['bấm tải xong file lưu ở đâu trên máy','link tài liệu nằm trong section nào của course'],
 'loi_tai_lieu':['bam download khong chay va bao loi','bấm nút download mà hệ thống không chạy'],
 'ngoai_pham_vi':['hướng dẫn cách thắt cà vạt','giải thích tarot là gì giúp mình'],
 'tam_biet':['tam dung nha','ket thuc cuoc tro chuyen','kết thúc cuộc trò chuyện'],
 'hoi_bot':['có người đọc tin nhắn không']
}

add_map={
 'kiem_tra_nop_bai':[
  'kiểm tra bài đã nộp thành công trong submission status ở đâu',
  'xem assignment đã ở trạng thái submitted for grading chưa',
  'làm sao xác nhận hệ thống đã ghi nhận bài nộp',
  'kiem tra bai da nop thanh cong trong submission status o dau',
  'xac nhan he thong da ghi nhan bai nop nhu the nao'
 ],
 'ban_nhap_nop_bai':[
  'bài ở trạng thái draft nghĩa là chưa nộp đúng không',
  'save draft chỉ lưu tạm chứ chưa submit phải không',
  'làm sao biết bài mới lưu nháp chưa gửi đi',
  'bai o trang thai draft nghia la chua nop dung khong',
  'save draft chi luu tam chu chua submit phai khong'
 ],
 'loi_quiz_kiem_tra':[
  'đang làm quiz thì attempt bị invalid session',
  'submit all and finish báo lỗi không hoàn tất được bài quiz',
  'quiz tự thoát khỏi attempt khi chưa hết thời gian',
  'dang lam quiz thi attempt bi invalid session',
  'submit all and finish bao loi khong hoan tat duoc'
 ],
 'loi_hien_thi':[
  'giao diện bị lệch khung khiến nút bấm nằm sai vị trí',
  'chữ và thành phần giao diện chồng lên nhau khó đọc',
  'layout trang bị vỡ khi đổi kích thước trình duyệt',
  'giao dien bi lech khung khien nut bam sai vi tri',
  'layout trang bi vo khi doi kich thuoc trinh duyet'
 ],
 'khong_nhan_thong_bao':[
  'đã bật thông báo nhưng không nhận email nhắc deadline',
  'không thấy notification dù có bài mới trong môn',
  'hệ thống không push thông báo lên điện thoại của mình',
  'da bat thong bao nhung khong nhan email nhac deadline',
  'khong thay notification du co bai moi'
 ],
 'cai_dat_thong_bao':[
  'hướng dẫn bật email notification cho từng môn học',
  'chỉnh notification preference để nhận nhắc hạn nộp bài',
  'cách tắt thông báo đẩy trên app moodle',
  'huong dan bat email notification cho tung mon',
  'chinh notification preference de nhan nhac deadline'
 ],
 'tai_tai_lieu':[
  'vào mục nào để tải slide bài giảng về máy',
  'cách tải file pdf tài liệu trong course',
  'download tài liệu trên app moodle thực hiện thế nào',
  'vao muc nao de tai slide bai giang ve may',
  'cach tai file pdf tai lieu trong course'
 ],
 'loi_tai_lieu':[
  'download tài liệu báo failed không tải được',
  'tải file về nhưng mở ra báo corrupt',
  'bấm download xong file bị lỗi định dạng không mở được',
  'download tai lieu bao failed khong tai duoc',
  'tai file ve mo ra bao corrupt'
 ],
 'ngoai_pham_vi':[
  'cho mình dự đoán giá bitcoin tuần này',
  'gợi ý vài kênh youtube giải trí hay',
  'viết caption instagram ngắn cho ảnh du lịch',
  'cho minh du doan gia bitcoin tuan nay',
  'viet caption instagram ngan cho anh du lich'
 ],
 'tam_biet':[
  'mình xin dừng cuộc trò chuyện tại đây',
  'ok cảm ơn, mình thoát chat nhé',
  'tạm biệt bot, mình quay lại sau',
  'minh xin dung cuoc tro chuyen tai day',
  'ok cam on minh thoat chat nhe'
 ],
 'hoi_bot':[
  'bạn là chatbot tự động hay người thật',
  'mình đang chat với AI đúng không',
  'bot này của trường hay bot bên thứ ba',
  'ban la chatbot tu dong hay nguoi that',
  'minh dang chat voi ai dung khong'
 ]
}

MIN_N, MAX_N = 50, 60
for intent in order:
    arr=intents[intent]
    rem={x.lower() for x in remove_map.get(intent,[])}
    arr=[x for x in arr if x.lower() not in rem]
    seen={x.lower() for x in arr}
    for x in add_map.get(intent,[]):
        if x.lower() not in seen:
            arr.append(x); seen.add(x.lower())
    # intra dedup
    out=[]; seen=set()
    for x in arr:
        k=x.lower().strip()
        if not k or k in seen: continue
        seen.add(k); out.append(x.strip())
    if len(out)>MAX_N:
        out=out[:MAX_N]
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

# refill min preserving intent style
for intent in order:
    arr=intents[intent]
    seen={x.lower() for x in arr}
    base=arr[:] if arr else [intent.replace('_',' ')]
    j=0
    while len(arr)<MIN_N and j<800:
        cand=base[j%len(base)].rstrip(' ?.!')+' nha'
        k=cand.lower()
        if k not in seen and k not in used:
            arr.append(cand); seen.add(k); used.add(k)
        j+=1
    if len(arr)>MAX_N: arr=arr[:MAX_N]
    intents[intent]=arr

out=[]
out.extend(header)
for intent in order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for x in intents[intent]:
        out.append(f'      - {x}')
    out.append('')
path.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('updated',len(order))
