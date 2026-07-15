"""Tạo 1 tài khoản qua command line — dùng khi cần thêm người sau lần seed ban đầu
(xem scripts/seed_users.py để tạo hàng loạt lúc khởi tạo).

Dùng:
    python scripts/create_user.py <name> <pod> <role>
    python scripts/create_user.py                      # hỏi từng giá trị, có validate

Pod: A/B/C/D/E. Role: annotator/pm/data_intake.
"""

import sys
from argparse import ArgumentParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from auth import UserExistsError, create_account
from constants import PODS, ROLES
from db import init_db


def _prompt_choice(label: str, choices: list[str]) -> str:
    while True:
        value = input(f"{label} ({'/'.join(choices)}): ").strip()
        if value in choices:
            return value
        print(f"Giá trị không hợp lệ, chọn 1 trong: {', '.join(choices)}")


def main() -> None:
    parser = ArgumentParser(description="Tạo 1 tài khoản cho annotation tool.")
    parser.add_argument("name", nargs="?", help="Tên đăng nhập, vd. pod_b_4")
    parser.add_argument("pod", nargs="?", choices=PODS, help=f"Pod: {'/'.join(PODS)}")
    parser.add_argument("role", nargs="?", choices=ROLES, help=f"Role: {'/'.join(ROLES)}")
    args = parser.parse_args()

    name = args.name or input("Tên đăng nhập: ").strip()
    if not name:
        raise SystemExit("Tên đăng nhập không được để trống.")
    pod = args.pod or _prompt_choice("Pod", PODS)
    role = args.role or _prompt_choice("Role", ROLES)

    init_db()
    try:
        password = create_account(name, pod, role)
    except UserExistsError as exc:
        raise SystemExit(str(exc)) from exc

    print(f"\nĐã tạo tài khoản '{name}' (pod {pod}, role {role}).")
    print(f"Mật khẩu (chỉ hiện 1 lần, lưu ngay — password manager): {password}")


if __name__ == "__main__":
    main()
