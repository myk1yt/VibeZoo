import keyring
import getpass

print("=== VibeZoo Exa API Key 암호화 저장 ===")
api_key = getpass.getpass("Enter EXA_API_KEY (입력 시 화면에 보이지 않습니다): ").strip()

if api_key:
    keyring.set_password("VibeZoo", "EXA_API_KEY", api_key)
    print("성공적으로 Windows 자격 증명 관리자에 암호화되어 저장되었습니다!")
else:
    print("오류: API 키가 입력되지 않았습니다.")
