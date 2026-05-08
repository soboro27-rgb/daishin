"""
최초 실행 시 기본 계정 데이터를 생성합니다.
사용법: python init_data.py
"""
from database import SessionLocal, engine
import models
from auth import hash_password


def init():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(models.User).count() > 0:
        print("이미 초기화되어 있습니다.")
        db.close()
        return

    # 지점 계정 (지점코드 + 비밀번호)
    branches = [
        ("DS001", "Ds001!2024", "서울강남지점", "서울"),
        ("DS002", "Ds002!2024", "서울여의도지점", "서울"),
        ("DS003", "Ds003!2024", "부산해운대지점", "부산"),
        ("DS004", "Ds004!2024", "대구수성지점", "대구"),
        ("DS005", "Ds005!2024", "인천남동지점", "인천"),
        ("DS006", "Ds006!2024", "광주북구지점", "광주"),
        ("DS007", "Ds007!2024", "대전유성지점", "대전"),
        ("DS008", "Ds008!2024", "수원영통지점", "경기"),
        ("DS009", "Ds009!2024", "성남분당지점", "경기"),
        ("DS010", "Ds010!2024", "울산남구지점", "울산"),
    ]

    for code, pw, name, region in branches:
        db.add(models.User(
            branch_code=code,
            password_hash=hash_password(pw),
            branch_name=name,
            region=region,
            role="branch",
        ))

    # 주관사 관리자
    db.add(models.User(
        branch_code="DS_WELFARE01",
        password_hash=hash_password("Welfare!2024"),
        branch_name="주관사",
        region="전국",
        role="welfare",
    ))

    # 코어테일 관리자
    db.add(models.User(
        branch_code="DS_CORETAIL01",
        password_hash=hash_password("Coretail!2024"),
        branch_name="코어테일",
        region="전국",
        role="coretail",
    ))

    db.commit()
    db.close()

    print("=" * 50)
    print("  데이터베이스 초기화 완료 (대신증권)")
    print("=" * 50)
    print()
    print("[지점 담당자 계정]")
    for code, pw, name, _ in branches:
        print(f"  {code} / {pw}  ({name})")
    print()
    print("[주관사 관리자]")
    print("  DS_WELFARE01 / Welfare!2024")
    print()
    print("[코어테일 관리자]")
    print("  DS_CORETAIL01 / Coretail!2024")
    print("=" * 50)


if __name__ == "__main__":
    init()
