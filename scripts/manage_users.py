#!/usr/bin/env python3
"""웹 서비스 계정 관리 CLI (관리자 전용, 셀프 회원가입 없음).

사용법:
    python scripts/manage_users.py add <username>
    python scripts/manage_users.py passwd <username>
    python scripts/manage_users.py list
    python scripts/manage_users.py remove <username>
"""
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, users


def _prompt_password():
    while True:
        pw1 = getpass.getpass("비밀번호: ")
        pw2 = getpass.getpass("비밀번호 확인: ")
        if pw1 != pw2:
            print("비밀번호가 일치하지 않습니다. 다시 입력해 주세요.")
            continue
        if len(pw1) < 4:
            print("비밀번호는 4자 이상이어야 합니다.")
            continue
        return pw1


def cmd_add(username):
    if users.get_by_username(username):
        print(f"이미 존재하는 계정입니다: {username}")
        return
    password = _prompt_password()
    users.create_user(username, password)
    print(f"계정을 생성했습니다: {username}")


def cmd_passwd(username):
    if not users.get_by_username(username):
        print(f"존재하지 않는 계정입니다: {username}")
        return
    password = _prompt_password()
    users.set_password(username, password)
    print(f"비밀번호를 변경했습니다: {username}")


def cmd_list():
    rows = users.list_users()
    if not rows:
        print("등록된 계정이 없습니다.")
        return
    for row in rows:
        print(f"{row['username']}\t(생성일: {row['created_at']})")


def cmd_remove(username):
    if not users.get_by_username(username):
        print(f"존재하지 않는 계정입니다: {username}")
        return
    users.delete_user(username)
    print(f"계정을 삭제했습니다: {username}")


def main():
    db.init_db()
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    command, rest = args[0], args[1:]
    if command == "add" and len(rest) == 1:
        cmd_add(rest[0])
    elif command == "passwd" and len(rest) == 1:
        cmd_passwd(rest[0])
    elif command == "list" and not rest:
        cmd_list()
    elif command == "remove" and len(rest) == 1:
        cmd_remove(rest[0])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
