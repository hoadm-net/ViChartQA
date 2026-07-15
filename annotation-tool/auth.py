"""Simple session-based login. No external auth service — 10-15 accounts
created by hand via scripts/seed_users.py.
"""

from __future__ import annotations

import secrets

import bcrypt
import streamlit as st
from sqlalchemy import select

from db import get_session
from models import User


class UserExistsError(ValueError):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_account(name: str, pod: str, role: str) -> str:
    """Tạo 1 User mới với mật khẩu ngẫu nhiên, trả về mật khẩu (chỉ tồn tại ở đây
    một lần — chỉ password_hash được lưu vào DB). Dùng chung bởi
    scripts/seed_users.py và scripts/create_user.py."""
    with get_session() as session:
        if session.scalar(select(User).where(User.name == name)):
            raise UserExistsError(f"Tài khoản '{name}' đã tồn tại")
        password = secrets.token_urlsafe(9)
        session.add(User(name=name, pod=pod, role=role, password_hash=hash_password(password)))
        session.commit()
    return password


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def _authenticate(name: str, password: str) -> User | None:
    with get_session() as session:
        user = session.scalar(select(User).where(User.name == name))
        if user and verify_password(password, user.password_hash):
            session.expunge(user)
            return user
    return None


def current_user() -> User | None:
    return st.session_state.get("user")


def logout() -> None:
    st.session_state.pop("user", None)
    st.rerun()


def require_login() -> User:
    """Call at the top of every page. Blocks rendering until logged in."""
    if current_user() is not None:
        return current_user()

    st.title("Đăng nhập — ViChartQA Annotation Tool")
    with st.form("login_form"):
        name = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")

    if submitted:
        user = _authenticate(name.strip(), password)
        if user is None:
            st.error("Sai tên đăng nhập hoặc mật khẩu.")
        else:
            st.session_state["user"] = user
            st.rerun()

    st.stop()


def sidebar_user_info() -> None:
    user = current_user()
    if user is None:
        return
    with st.sidebar:
        st.caption(f"Đăng nhập: **{user.name}** · Pod {user.pod} · {user.role}")
        if st.button("Đăng xuất"):
            logout()
