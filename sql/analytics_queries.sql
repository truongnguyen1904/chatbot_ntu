-- Truy vấn mẫu cho báo cáo đồ án (thống kê sử dụng chatbot)

-- 1) Top intent được nhận diện (một lượt chat = một dòng)
SELECT primary_intent AS intent, COUNT(*) AS so_luot
FROM chat_messages
WHERE primary_intent IS NOT NULL AND primary_intent != ''
GROUP BY primary_intent
ORDER BY so_luot DESC;

-- 2) Tỷ lệ câu hỏi gộp nhiều ý (multi-question)
SELECT
    SUM(CASE WHEN is_multi_question = 1 THEN 1 ELSE 0 END) AS so_multi,
    SUM(CASE WHEN is_multi_question = 0 THEN 1 ELSE 0 END) AS so_don,
    COUNT(*) AS tong
FROM chat_messages;

-- 3) Số phiên (sender) đã từng chat
SELECT COUNT(DISTINCT sender_id) AS so_phien FROM chat_sessions;

-- 4) 20 tin nhắn gần nhất (kiểm tra log)
SELECT id, sender_id, substr(user_text, 1, 80) AS tom_tat_cau_hoi,
       primary_intent, confidence, is_multi_question, created_at
FROM chat_messages
ORDER BY id DESC
LIMIT 20;

-- 5) Trung bình độ tin cậy intent (theo intent)
SELECT primary_intent, ROUND(AVG(confidence), 3) AS tb_conf, COUNT(*) AS n
FROM chat_messages
WHERE confidence IS NOT NULL
GROUP BY primary_intent
ORDER BY n DESC;
