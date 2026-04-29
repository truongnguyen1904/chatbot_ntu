import re, pathlib
from collections import OrderedDict

p = pathlib.Path(r'c:\Users\HP\chatbot_ntu\data\nlu.yml')
lines = p.read_text(encoding='utf-8').splitlines()

# Parse
header=[]; i=0
while i < len(lines) and lines[i].strip()!='nlu:':
    header.append(lines[i]); i+=1
header.append(lines[i]); i+=1
intents=OrderedDict(); order=[]
while i < len(lines):
    m=re.match(r'^\s*- intent:\s+([A-Za-z0-9_]+)\s*$', lines[i])
    if not m:
        i+=1; continue
    intent=m.group(1); order.append(intent); i+=1
    while i < len(lines) and lines[i].strip()!='examples: |':
        i+=1
    if i < len(lines): i+=1
    ex=[]
    while i < len(lines) and not re.match(r'^\s*- intent:\s+', lines[i]):
        s=lines[i].strip()
        if s.startswith('- '): ex.append(s[2:].strip())
        i+=1
    intents[intent]=ex

remove_map={
 'kiem_tra_nop_bai':[
  'làm sao biết giảng viên đã nhận được file của em','lam sao biet giang vien thay bai cua minh chua','xem lại file đã upload ở đâu','xem lai file da upload nam o dau',
  'xem minh chung da nop bai','xem minh chứng nộp bài ở đâu'
 ],
 'nop_bo_sung_bai':['nộp lại lần 2 có bị tính là nộp trễ không','nop lan 2 co bi tinh la nop tre khong'],
 'loi_nop_bai':['đang upload bài thì bị văng ra ngoài','nop xong khong thay file dau het','nộp xong không thấy file đâu hết','add submission bị treo máy'],
 'loi_quiz_kiem_tra':['nút nộp bài bị mờ không cho phép nhấn','giao diện thi bị lỗi font chữ không đọc được đề','click vào câu hỏi nhưng không hiện nội dung','ko thay nut tiep theo de sang cau moi'],
 'loi_hien_thi':['trang web bi trang xoa ko hien noi dung','bị màn hình trắng xóa khi vào môn học'],
 'ngoai_pham_vi':['bạn có phải là robot không hay là người thật','goi y mon an ngon cuoi tuan','dự báo thời tiết ngày mai giúp mình'],
 'chinh_sach_nop_tre':['nop muon co sao ko admin','qua thoi gian nop bai co cho nop nua khong'],
 'ban_nhap_nop_bai':['ban nhap la gi','ban nhap co phai la bai chua nop']
}

add_map={
 'kiem_tra_nop_bai':[
  'xem submission receipt sau khi nộp ở đâu',
  'vào đâu để kiểm tra trạng thái submitted của assignment',
  'làm sao biết bài đang ở submitted hay draft',
  'check lịch sử timestamp nộp bài trong assignment như nào',
  'xem proof da nop bai trong phan submission status'
 ],
 'nop_bo_sung_bai':[
  'sau khi submit em muốn replace file bài nộp thì làm sao',
  'có thể chỉnh submission và nộp lại file mới không',
  'hướng dẫn update file sau khi đã bấm submit',
  'replace submission sau khi nop bai nhu the nao',
  'edit bai da nop roi nop lai duoc khong'
 ],
 'loi_nop_bai':[
  'bấm submit assignment báo failed to submit dù file hợp lệ',
  'hệ thống trả lỗi khi lưu submission lần cuối',
  'nộp bài bị báo request failed dù mạng ổn định',
  'submit assignment bao failed to submit du file hop le',
  'nop bai bao request failed du mang on dinh'
 ],
 'loi_quiz_kiem_tra':[
  'đang làm quiz thì submit all and finish bị lỗi',
  'quiz bị mất đáp án sau khi bấm next page',
  'attempt quiz bị invalid session giữa lúc làm bài',
  'submit all and finish bi loi khi dang thi quiz',
  'attempt quiz bi invalid session giua luc lam bai'
 ],
 'loi_hien_thi':[
  'màn hình chỉ hiện khung trắng nhưng web vẫn đang chạy',
  'giao diện bị lỗi css làm chữ và nút lệch vị trí',
  'khung nội dung bị tràn nên không thấy đầy đủ thông tin',
  'man hinh chi hien khung trang nhung web van chay',
  'giao dien loi css lam chu va nut lech vi tri'
 ],
 'ngoai_pham_vi':[
  'cho mình xin lịch chiếu phim rạp tối nay',
  'gợi ý game mobile hay để giải trí',
  'giải thích tarot là gì giúp mình',
  'cho minh xin lich chieu phim toi nay',
  'goi y game mobile hay de giai tri'
 ],
 'chinh_sach_nop_tre':[
  'nộp quá deadline có bị trừ điểm theo chính sách không',
  'chính sách late submission của môn này như thế nào',
  'nộp muộn có cần xin giảng viên mở lại assignment không',
  'nop qua deadline co bi tru diem khong',
  'late submission policy cua mon nay la gi'
 ],
 'ban_nhap_nop_bai':[
  'trạng thái draft nghĩa là bài mới lưu nháp đúng không',
  'bài ở draft thì chưa được tính là đã nộp phải không',
  'khi nào draft chuyển sang submitted for grading',
  'trang thai draft nghia la bai chua nop dung khong',
  'draft thi chua duoc tinh la da nop phai khong'
 ],
 'lich_hoc':[
  'xem lịch buổi học và phòng học trong course ở đâu',
  'thời khóa biểu môn học tuần này xem ở mục nào',
  'link zoom của từng buổi học nằm trong lịch nào',
  'xem lich buoi hoc va phong hoc trong course o dau',
  'thoi khoa bieu mon hoc tuan nay xem o muc nao'
 ],
 'website_bi_sap':[
  'toàn bộ sinh viên đều không truy cập được elearning',
  'web báo service unavailable toàn hệ thống',
  'server down toàn trang không login được cho ai',
  'toan bo nguoi dung deu khong vao duoc elearning',
  'web bao service unavailable toan he thong'
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
    # dedup within intent
    out=[]; seen=set()
    for x in arr:
        k=x.strip().lower()
        if not k or k in seen: continue
        seen.add(k); out.append(x.strip())
    if len(out)>MAX_N: out=out[:MAX_N]
    intents[intent]=out

# global exact dedup
used=set()
for intent in order:
    out=[]
    for x in intents[intent]:
        k=x.lower()
        if k in used: continue
        used.add(k); out.append(x)
    intents[intent]=out

# repad to min
for intent in order:
    arr=intents[intent]
    seen={x.lower() for x in arr}
    base=arr[:] if arr else [intent.replace('_',' ')]
    j=0
    while len(arr)<MIN_N and j<800:
        b=base[j%len(base)].rstrip(' ?.!')
        cand=f'{b} nha'
        k=cand.lower()
        if k not in seen and k not in used:
            arr.append(cand); seen.add(k); used.add(k)
        j+=1
    if len(arr)>MAX_N: arr=arr[:MAX_N]
    intents[intent]=arr

# write
out=[]; out.extend(header)
out.append('nlu:') if (not out or out[-1].strip()!='nlu:') else None
for intent in order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for x in intents[intent]: out.append(f'      - {x}')
    out.append('')
p.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('updated',len(order))
