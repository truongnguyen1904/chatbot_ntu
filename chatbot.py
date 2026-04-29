import sys

from chatbot_core import process_user_message

print("Chatbot starting...")

DEFAULT_SENDER = "cli_user"


def _print_bot(prefix: str, text: str) -> None:
    if not text.strip():
        print(f"{prefix}Xin lỗi, tôi chưa hiểu.")
        return
    print(f"{prefix}{text}")


while True:
    try:
        user_input = input("Bạn: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nTạm biệt!")
        sys.exit(0)

    if not user_input:
        continue

    result = process_user_message(user_input, DEFAULT_SENDER)
    d = result.get("debug") or {}

    if result.get("error") == "parse_failed":
        print(result.get("text", ""))
        continue

    if d.get("multi_question"):
        print(f"[Rasa] nhiều ý: {d.get('parts')} phần")
        for s in d.get("sub_intents") or []:
            ii = s.get("intent")
            cc = s.get("confidence")
            if ii is not None and cc is not None:
                print(f"  · {ii} ({float(cc):.2f})")
    else:
        intent = d.get("intent")
        conf = d.get("confidence")
        if intent is not None and conf is not None:
            print(f"[Rasa] {intent} ({float(conf):.2f})")

    if d.get("phobert_intent") is not None:
        pi = d.get("phobert_intent")
        ps = d.get("phobert_score")
        if ps is not None:
            print(f"[PhoBERT] → {pi} ({float(ps):.2f})")

    via = d.get("via")
    prefix = "Bot: "
    if via == "phobert":
        prefix = "Bot (PhoBERT): "

    _print_bot(prefix, result.get("text") or "")
