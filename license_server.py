import json
import uuid
import hashlib
import os
from datetime import datetime, timedelta

LICENSE_FILE = "licenses.json"
SECRET_KEY = "MY_SUPER_SECRET_KEY"


# -------------------------------
# 유틸
# -------------------------------
def now():
    return datetime.utcnow()


def hash_key(key: str) -> str:
    return hashlib.sha256((key + SECRET_KEY).encode()).hexdigest()


def load_licenses():
    if not os.path.exists(LICENSE_FILE):
        return {}
    with open(LICENSE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_licenses(data):
    with open(LICENSE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# -------------------------------
# 라이센스 생성
# -------------------------------
def create_license(days: int):
    licenses = load_licenses()

    raw_key = str(uuid.uuid4()).upper()
    hashed = hash_key(raw_key)

    licenses[hashed] = {
        "created_at": now().isoformat(),
        "expires_at": (now() + timedelta(days=days)).isoformat(),
        "active": False,
        "disabled": False
    }

    save_licenses(licenses)
    return raw_key


# -------------------------------
# 활성화
# -------------------------------
def activate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    if licenses[hashed]["disabled"]:
        return False, "비활성화된 라이센스"

    licenses[hashed]["active"] = True
    save_licenses(licenses)
    return True, "활성화 완료"


# -------------------------------
# 비활성화
# -------------------------------
def deactivate_license(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    licenses[hashed]["disabled"] = True
    licenses[hashed]["active"] = False
    save_licenses(licenses)
    return True, "비활성화 완료"


# -------------------------------
# 기간 연장
# -------------------------------
def extend_license(key: str, days: int):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "라이센스 없음"

    expires = datetime.fromisoformat(licenses[hashed]["expires_at"])
    licenses[hashed]["expires_at"] = (expires + timedelta(days=days)).isoformat()

    save_licenses(licenses)
    return True, f"{days}일 연장 완료"


# -------------------------------
# DRM 체크 (프로그램 실행 시)
# -------------------------------
def check_drm(key: str):
    licenses = load_licenses()
    hashed = hash_key(key)

    if hashed not in licenses:
        return False, "❌ 유효하지 않은 라이센스"

    lic = licenses[hashed]

    if lic["disabled"]:
        return False, "🚫 비활성화된 라이센스"

    if not lic["active"]:
        return False, "⚠ 활성화되지 않은 라이센스"

    if now() > datetime.fromisoformat(lic["expires_at"]):
        return False, "⌛ 라이센스 만료"

    return True, "✅ 라이센스 정상"


# -------------------------------
# 예제 CLI
# -------------------------------
def main():
    while True:
        print("\n1. 라이센스 생성")
        print("2. 라이센스 활성화")
        print("3. 라이센스 비활성화")
        print("4. 라이센스 기간 연장")
        print("5. DRM 체크")
        print("0. 종료")

        cmd = input("선택: ")

        if cmd == "1":
            days = int(input("기간(일): "))
            key = create_license(days)
            print("생성된 라이센스 키:", key)

        elif cmd == "2":
            key = input("라이센스 키: ")
            print(activate_license(key)[1])

        elif cmd == "3":
            key = input("라이센스 키: ")
            print(deactivate_license(key)[1])

        elif cmd == "4":
            key = input("라이센스 키: ")
            days = int(input("연장 일수: "))
            print(extend_license(key, days)[1])

        elif cmd == "5":
            key = input("라이센스 키: ")
            print(check_drm(key)[1])

        elif cmd == "0":
            break

        else:
            print("잘못된 입력")


if __name__ == "__main__":
    main()
