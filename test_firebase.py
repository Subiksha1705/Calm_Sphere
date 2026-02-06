from firebase_db import save_message, get_messages

save_message("test_user", "Hello Firebase", emotion="happy")

msgs = get_messages("test_user")
print(msgs)
