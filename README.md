# 🗂️ Memory Cards (Speaking Matrix 영어 회화 플래시카드)

Anki의 **Speaking Matrix (문장 말하기 900제)** 덱과 **기존 복습 이력(1,592건)**이 성공적으로 웹앱으로 이전되었습니다!  
FSRS 알고리즘을 통해 기존에 공부하던 복습 주기가 그대로 유지되며, **GitHub Pages**를 통해 모바일(아이폰/아이패드/갤럭시)에서 **앱(PWA)**처럼 어디서나 공부할 수 있습니다.

---

## 📊 현재 탑재된 덱 현황

- **카드 수:** 총 900장 (Day 01 ~ Day 30)
- **과목 분류 (Unit):**
  - Unit 01 (Day 01-05) : 150장 (Input 100 / Output 50)
  - Unit 02 (Day 06-10) : 150장 (Input 100 / Output 50)
  - Unit 03 (Day 11-15) : 150장 (Input 100 / Output 50)
  - Unit 04 (Day 16-20) : 150장 (Input 100 / Output 50)
  - Unit 05 (Day 21-25) : 150장 (Input 100 / Output 50)
  - Unit 06 (Day 26-30) : 150장 (Input 100 / Output 50)
- **복원된 복습 기록:** 총 1,592건 (지난주 533건 + 이번 주 1,059건의 채점 이력 복원)
- **카드 구성:**
  - **앞면:** 한국어 문장 (상단에 Day 및 Input/Output 표시)
  - **뒷면:** 영어 정답 문장
  - **보충 설명:** 청크 분할 및 상황 설명 표시

---

## 🚀 GitHub에 올리고 모바일에서 공부하기 (3단계)

### 1단계. 내 GitHub 저장소에 올리기

1. [GitHub](https://github.com/)에서 새 레포지토리(Public 권장)를 생성합니다. (예: `speaking-cards`)
2. 이 폴더에서 터미널(PowerShell)을 열고 푸시합니다:

```bash
git init
git add .
git commit -m "feat: Speaking Matrix 900제 및 복습 이력 이관"
git branch -M main
git remote add origin https://github.com/<내-GitHub-아이디>/<저장소이름>.git
git push -u origin main
```

---

### 2단계. GitHub Pages 켜기 (웹 호스팅)

1. GitHub 레포지토리 페이지에서 **Settings** → 좌측 **Pages** 메뉴 클릭
2. **Build and deployment**의 **Branch**를 `main` / `/(root)`로 선택하고 **Save** 클릭
3. 1~2분 뒤 상단에 표시되는 주소로 접속합니다:  
   👉 `https://<내-GitHub-아이디>.github.io/<저장소이름>/`

---

### 3단계. 스마트폰/태블릿에서 앱으로 설치하기 📱

모바일 브라우저로 위 주소에 접속합니다:

- **아이폰 / 아이패드 (Safari):**  
  하단 중앙 **공유 버튼(네모+화살표)** 클릭 → **[홈 화면에 추가]** 클릭
- **안드로이드 / 갤럭시 (Chrome / 삼성 인터넷):**  
  우측 상단 메뉴 **(점 3개)** 클릭 → **[홈 화면에 추가]** 또는 **[앱 설치]** 클릭

✨ 홈 화면의 아이콘을 누르면 주소창 없는 깔끔한 **전체화면 네이티브 앱(PWA)**으로 실행됩니다!

---

## 🔄 기기 간 학습 기록 동기화 (PC ↔ 모바일)

모바일에서 공부한 결과를 PC에서도 똑같이 이어가려면 GitHub 토큰을 한 번만 연결해 두면 됩니다:

1. [GitHub Personal Access Token](https://github.com/settings/tokens) 발급:
   - 권한(Scopes): `repo` (또는 `Contents: Read and write`)
2. 웹앱 우측 상단 **⚙️ 설정** → **GitHub 연결** 클릭
3. 저장소명(`아이디/저장소명`)과 발급받은 토큰 입력 후 **[연결]** 클릭
4. 이제 채점 결과가 자동으로 내 깃허브 저장소로 커밋·백업됩니다.

---

## 🛠️ 추가 덱 변환 도구 안내

- **Anki 패키지 변환:** `python import_anki.py <파일명.apkg>`
- **엑셀/CSV/텍스트 변환:** `python build_cards.py <파일명.csv>`
