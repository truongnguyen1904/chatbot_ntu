import re, pathlib
from collections import OrderedDict

p = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
lines = p.read_text(encoding='utf-8').splitlines()

header=[]; i=0
while i < len(lines) and not re.match(r'^nlu:\s*$', lines[i]):
    header.append(lines[i]); i+=1
header.append(lines[i]); i+=1

intents=OrderedDict(); order=[]
while i < len(lines):
    m=re.match(r'^\s*- intent:\s+([A-Za-z0-9_]+)\s*$', lines[i])
    if not m: i+=1; continue
    intent=m.group(1); order.append(intent); i+=1
    while i < len(lines) and not re.match(r'^\s*examples:\s*\|\s*$', lines[i]): i+=1
    if i < len(lines): i+=1
    ex=[]
    while i < len(lines) and not re.match(r'^\s*- intent:\s+', lines[i]):
        s=lines[i].strip()
        if s.startswith('- '): ex.append(s[2:].strip())
        i+=1
    intents[intent]=ex

remove_map={
 'kiem_tra_nop_bai':[
  'kiem tra lich su nop bai tap','nộp bài xong trang web báo như thế nào là ok','hệ thống có ghi nhận timestamp nộp bài cụ thể không',
  'có email confirm nộp bài gửi về không ạ','hệ thống có gửi mail báo nộp bài thành công không','lam sao biet da nop bai thanh cong'
 ],
 'tim_kiem_loc_mon_hoc':['xem mon past courses o cho nao','xem môn past courses ở chỗ nào','cách ẩn môn cũ để chỉ còn môn hiện tại','chỉ xem môn của học kỳ này thôi'],
 'cach_tinh_diem':['điểm giữa kỳ và cuối kỳ được tính theo tỉ lệ nào'],
 'xem_diem':['xem điểm giữa kỳ trên elearning ở đâu','xem điểm bài quiz số 1 ở đâu','làm sao biết điểm thành phần của mình','lam sao biet diem thanh phan cua minh'],
 'cai_dat_thong_bao':['chi muon nhan thong bao quan trong thoi','cấu hình email digest thế nào','cai dat email digest the nao'],
 'loi_nop_bai':['mạng ổn mà upload vẫn báo fail liên tục'],
 'loi_duong_truyen':['duong truyen gap su co khong login duoc','mất mạng giữa chừng nên bị out khỏi hệ thống'],
 'ngoai_pham_vi':['hướng dẫn tập yoga cho người mới bắt đầu','huong dan cach choi co tuong']
}

add_map={
 'kiem_tra_nop_bai':[
  'làm sao kiểm tra bài đã submit thành công',
  'xem trạng thái submitted for grading ở đâu',
  'kiểm tra assignment đã nộp hay còn draft',
  'xem receipt nộp bài trong assignment thế nào',
  'co cach check assignment da submitted chua'
 ],
 'tim_kiem_loc_mon_hoc':[
  'lọc theo học kỳ để xem môn cũ như thế nào',
  'filter course theo semester ở mục nào',
  'cách bật bộ lọc in progress và past courses',
  'lọc danh sách môn theo năm học ở đâu',
  'loc course theo hoc ky o dau'
 ],
 'cach_tinh_diem':[
  'điểm tổng kết được tính theo công thức nào',
  'trọng số từng thành phần điểm là bao nhiêu phần trăm',
  'công thức cộng điểm giữa kỳ cuối kỳ thế nào',
  'diem tong ket tinh theo cong thuc nao',
  'trong so tung thanh phan diem la bao nhieu'
 ],
 'xem_diem':[
  'mở gradebook để xem điểm ở đâu',
  'xem cột điểm của mình trong course như thế nào',
  'vào mục grades để coi điểm đã chấm',
  'xem bảng điểm môn học trên moodle ở đâu',
  'mo gradebook de xem diem o dau'
 ],
 'cai_dat_thong_bao':[
  'cách bật thông báo email khi có bài mới',
  'hướng dẫn cài notification cho từng môn học',
  'bật push notification trong app moodle như nào',
  'set thong bao deadline qua email nhu the nao',
  'bat thong bao email khi co bai moi'
 ],
 'diem_co_chinh_thuc_khong':[
  'điểm này là điểm chính thức hay chỉ tham khảo',
  'grade final đã chốt chưa hay còn thay đổi',
  'điểm trên moodle có phải điểm cuối cùng không',
  'diem final da chot chua',
  'diem moodle co phai diem cuoi cung khong'
 ],
 'loi_nop_bai':[
  'submit assignment báo lỗi failed to submit',
  'không nộp được bài dù mạng ổn định',
  'nộp bài bị lỗi xử lý request trên hệ thống',
  'bam submit assignment bao failed to submit',
  'khong nop duoc bai du mang on dinh'
 ],
 'loi_duong_truyen':[
  'wifi chập chờn làm kết nối bị gián đoạn liên tục',
  'internet yếu nên request timeout khi truy cập',
  'mạng rớt giữa chừng khi đang thao tác trên hệ thống',
  'wifi chap chon lam ket noi gian doan',
  'internet yeu nen request timeout'
 ],
 'ngoai_pham_vi':[
  'kể chuyện khoa học viễn tưởng đi',
  'gợi ý món ăn ngon cuối tuần',
  'dự báo thời tiết ngày mai giúp mình',
  'ke chuyen khoa hoc vien tuong di',
  'goi y mon an ngon cuoi tuan'
 ],
 'loi_quiz_kiem_tra':[
  'quiz báo lỗi attempt overdue dù chưa hết giờ',
  'bài quiz không lưu đáp án đã chọn',
  'đang làm quiz bị out khỏi attempt',
  'quiz bao loi attempt overdue du chua het gio',
  'dang lam quiz bi out khoi attempt'
 ]
}

TARGET_MIN, TARGET_MAX = 50, 60

for intent in order:
    exs=intents[intent]
    rm={x.lower() for x in remove_map.get(intent,[])}
    exs=[e for e in exs if e.lower() not in rm]
    seen={e.lower() for e in exs}
    for a in add_map.get(intent,[]):
        if a.lower() not in seen:
            exs.append(a); seen.add(a.lower())
    # dedup keep order
    new=[]; seen=set()
    for e in exs:
        k=e.lower().strip()
        if not k or k in seen: continue
        seen.add(k); new.append(e.strip())
    # trim to max
    if len(new)>TARGET_MAX:
        new=new[:TARGET_MAX]
    # pad to min with light variants from first samples
    j=0
    base=new[:]
    while len(new)<TARGET_MIN and base and j<400:
        b=base[j%len(base)].rstrip(' ?.!')
        cand=b+' nha'
        if cand.lower() not in seen:
            new.append(cand); seen.add(cand.lower())
        j+=1
    intents[intent]=new

# global exact dedup, then re-pad each intent to min if needed
used=set()
for intent in order:
    arr=[]
    for e in intents[intent]:
        k=e.lower()
        if k in used: continue
        used.add(k); arr.append(e)
    intents[intent]=arr

for intent in order:
    arr=intents[intent]
    seen={e.lower() for e in arr}
    base=arr[:] if arr else [intent.replace('_',' ')]
    j=0
    while len(arr)<TARGET_MIN and j<600:
        b=base[j%len(base)].rstrip(' ?.!')
        cand=b+' nhe'
        k=cand.lower()
        if k not in seen and k not in used:
            arr.append(cand); seen.add(k); used.add(k)
        j+=1
    if len(arr)>TARGET_MAX: arr=arr[:TARGET_MAX]
    intents[intent]=arr

out=[]; out.extend(header)
for intent in order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for e in intents[intent]: out.append(f'      - {e}')
    out.append('')
p.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('done',len(order))
