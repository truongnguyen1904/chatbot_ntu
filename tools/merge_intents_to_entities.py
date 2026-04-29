import re, pathlib
from collections import OrderedDict, defaultdict

p = pathlib.Path(r"c:\Users\HP\chatbot_ntu\data\nlu.yml")
text = p.read_text(encoding='utf-8').splitlines()

header=[]; i=0
while i < len(text) and text[i].strip()!='nlu:':
    header.append(text[i]); i+=1
header.append('nlu:')
if i < len(text) and text[i].strip()=='nlu:':
    i+=1

intents=OrderedDict(); order=[]
while i < len(text):
    m=re.match(r'^\s*- intent:\s+([A-Za-z0-9_]+)\s*$', text[i])
    if not m:
        i+=1; continue
    name=m.group(1); order.append(name); i+=1
    while i < len(text) and text[i].strip()!='examples: |':
        i+=1
    if i < len(text):
        i+=1
    ex=[]
    while i < len(text) and not re.match(r'^\s*- intent:\s+', text[i]):
        s=text[i].strip()
        if s.startswith('- '):
            ex.append(s[2:].strip())
        i+=1
    intents[name]=ex

merge_map = {
  'nop_bai': {
    'entity': 'nop_bai_issue',
    'items': [
      ('huong_dan_nop_bai','how_to_submit'),
      ('loi_nop_bai','submit_error'),
      ('kiem_tra_nop_bai','check_status'),
      ('ban_nhap_nop_bai','draft_status'),
      ('nop_bo_sung_bai','resubmit'),
      ('nop_nhieu_file','multi_file'),
      ('nop_file_dung_luong_lon','file_too_large'),
    ]
  },
  'thong_bao': {
    'entity': 'thong_bao_issue',
    'items': [
      ('cai_dat_thong_bao','settings'),
      ('khong_nhan_thong_bao','not_received'),
    ]
  },
  'tai_lieu': {
    'entity': 'tai_lieu_issue',
    'items': [
      ('tai_tai_lieu','download_howto'),
      ('loi_tai_lieu','download_error'),
    ]
  },
  'loi_he_thong': {
    'entity': 'loi_context',
    'items': [
      ('loi_quiz_kiem_tra','quiz'),
      ('loi_hien_thi','ui'),
    ]
  }
}

kw = {
 'nop_bai_issue': {
   'how_to_submit':[r'cách nộp',r'huong dan',r'hướng dẫn',r'submit',r'add submission',r'upload file',r'chọn file',r'nộp bài',r'nop bai'],
   'submit_error':[r'request failed',r'timeout',r'failed to submit',r'failed',r'fail',r'error',r'lỗi',r'502|500|504|413',r'không thể',r'khong the',r'không upload',r'khong upload',r'không gửi',r'khong gui'],
   'check_status':[r'submission status',r'submitted for grading',r'receipt',r'biên nhận',r'bằng chứng',r'minh chứng',r'timestamp',r'nhật ký',r'log',r'đã nộp',r'da nop'],
   'draft_status':[r'save draft',r'draft',r'lưu nháp',r'ban nhap',r'chưa submit',r'chua submit'],
   'resubmit':[r'nộp lại',r'nop lai',r'resubmit',r'replace',r'thay file',r'cập nhật',r'cap nhat',r'bổ sung',r'bo sung'],
   'multi_file':[r'nhiều file',r'nhieu file',r'multiple',r'multi-file',r'chon nhieu',r'chọn nhiều',r'drag and drop',r'2-3 file'],
   'file_too_large':[r'entity too large',r'size limit',r'dung lượng',r'dung luong',r'file lớn',r'file lon',r'quá nặng',r'qua nang',r'200mb|300mb|500mb',r'nén file',r'nen file',r'chía nhỏ',r'chia nho',r'link drive'],
 },
 'thong_bao_issue': {
   'settings':[r'notification preferences',r'preferences',r'cài',r'cai',r'bật',r'bat',r'tắt',r'tat',r'setting',r'push',r'email',r'spam'],
   'not_received':[r'không nhận',r'khong nhan',r'không thấy',r'khong thay',r'không có thông báo',r'ko nhận',r'ko thay',r'đến trễ',r'den tre',r'miss deadline',r'bell'],
 },
 'tai_lieu_issue': {
   'download_howto':[r'tải',r'tai',r'download',r'slide',r'pdf',r'ppt',r'video',r'offline',r'lưu ở đâu',r'section'],
   'download_error':[r'download failed',r'failed',r'fail',r'corrupt',r'0kb|0 byte',r'404',r'permission',r'không mở',r'khong mo',r'không tải',r'khong tai',r'không chạy',r'khong chay',r'lỗi',r'error'],
 },
 'loi_context': {
   'quiz':[r'submit all and finish',r'finish attempt',r'start attempt',r'next page',r'attempt',r'quiz',r'phòng thi',r'bài thi',r'đang thi',r'dang thi',r'đếm ngược',r'session timeout'],
   'ui':[r'giao diện',r'layout',r'màn hình',r'man hinh',r'vỡ',r'vo',r'css',r'font',r'không scroll',r'khong scroll',r'không thấy nút',r'khong thay nut',r'sidebar',r'dropdown'],
 }
}

def annotate(example: str, entity: str, value: str):
    for pat in kw.get(entity, {}).get(value, []):
        m = re.search(pat, example, flags=re.I)
        if not m:
            continue
        span = example[m.start():m.end()]
        if len(span) < 3:
            continue
        return example[:m.start()] + f'[{span}]({entity})' + example[m.end():]
    return example

synonyms = defaultdict(set)
manual_syn = {
 'nop_bai_issue':{
  'how_to_submit':['cách nộp','hướng dẫn','submit','add submission','upload file'],
  'submit_error':['báo lỗi','error','failed','request failed','timeout'],
  'check_status':['submission status','submitted for grading','receipt','bằng chứng','timestamp'],
  'draft_status':['draft','save draft','lưu nháp','bản nháp'],
  'resubmit':['nộp lại','replace','thay file','cập nhật','bổ sung'],
  'multi_file':['nhiều file','multiple file','multi-file','drag and drop'],
  'file_too_large':['dung lượng','file lớn','entity too large','size limit','nén file','link drive'],
 },
 'thong_bao_issue':{
  'settings':['notification preferences','preferences','bật thông báo','tắt thông báo','push notification','email notification'],
  'not_received':['không nhận thông báo','không thấy thông báo','notification đến trễ','bell không hiện'],
 },
 'tai_lieu_issue':{
  'download_howto':['tải tài liệu','download tài liệu','tải slide','tải pdf','lưu ở đâu'],
  'download_error':['download failed','file corrupt','không tải được','không mở được','lỗi 404','0kb'],
 },
 'loi_context':{
  'quiz':['quiz','attempt','submit all and finish','finish attempt','next page','start attempt'],
  'ui':['giao diện','layout','màn hình trắng','lỗi css','lỗi font','không scroll'],
 }
}
for ent, mp in manual_syn.items():
    for canon, vals in mp.items():
        for v in vals:
            synonyms[(ent, canon)].add(v)

skip_old = {old for m in merge_map.values() for old,_ in m['items']}
inserted=set(); new_order=[]
for intent in order:
    if intent in skip_old:
        for merged, cfg in merge_map.items():
            if merged in inserted:
                continue
            olds=[o for o,_ in cfg['items']]
            if intent in olds:
                inserted.add(merged)
                new_order.append(merged)
        continue
    new_order.append(intent)

new_intents=OrderedDict()
for merged, cfg in merge_map.items():
    ent=cfg['entity']
    bucket=[]
    for old, val in cfg['items']:
        for e in intents.get(old, []):
            bucket.append(annotate(e, ent, val))
    seen=set(); out=[]
    for e in bucket:
        k=e.lower().strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(e)
    new_intents[merged]=out

for intent in order:
    if intent in skip_old:
        continue
    new_intents[intent]=intents[intent]

out=[]
out.extend(header)
for intent in new_order:
    out.append(f'  - intent: {intent}')
    out.append('    examples: |')
    for e in new_intents[intent]:
        out.append(f'      - {e}')
    out.append('')

# add synonyms
for (ent, canon), vals in sorted(synonyms.items(), key=lambda x:(x[0][0],x[0][1])):
    out.append(f'  - synonym: {canon}')
    out.append('    examples: |')
    for v in sorted(vals):
        out.append(f'      - {v}')
    out.append('')

p.write_text('\n'.join(out).rstrip()+'\n', encoding='utf-8')
print('ok merged', {k:len(new_intents[k]) for k in merge_map})
