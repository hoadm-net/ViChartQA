"""Create initial user accounts. Edit the USERS list below with real names/pods,
then run once: `python scripts/seed_users.py`.

Prints each generated password once — save them somewhere safe (e.g. a password
manager) and share individually with each annotator. Re-running is safe: existing
usernames are skipped, not overwritten.

Để thêm 1 tài khoản sau này, dùng `python scripts/create_user.py` thay vì sửa file này.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import UserExistsError, create_account
from db import init_db

# (name, pod, role) — role in {annotator, pm, data_intake}
USERS = [
    ("pm", "E", "pm"),
    # ("pod_a_1", "A", "data_intake"),
    # ("pod_a_2", "A", "data_intake"),
    # ("pod_b_1", "B", "annotator"),
    # ("pod_b_2", "B", "annotator"),
    # ("pod_b_3", "B", "annotator"),
    # ("pod_c_1", "C", "annotator"),
    # ("pod_c_2", "C", "annotator"),
    # ("pod_d_1", "D", "annotator"),
    # ("pod_d_2", "D", "annotator"),
]


def main() -> None:
    init_db()
    created = []
    for name, pod, role in USERS:
        try:
            password = create_account(name, pod, role)
        except UserExistsError:
            print(f"skip (exists): {name}")
            continue
        created.append((name, pod, role, password))

    if created:
        print("\nTài khoản mới tạo — lưu lại ngay, mật khẩu không hiển thị lại được:")
        print(f"{'name':<12} {'pod':<5} {'role':<12} password")
        for name, pod, role, password in created:
            print(f"{name:<12} {pod:<5} {role:<12} {password}")
    else:
        print("Không có tài khoản mới (tất cả đã tồn tại).")


if __name__ == "__main__":
    main()
