# Facility Layout 리더보드 (GitHub 버전)

참가자가 GitHub 이슈로 배치 CSV를 제출하면 GitHub Actions가 채점하고,
GitHub Pages 페이지의 Case 1~5 리더보드에 1등과 순위가 표시됩니다.

## 관리자 설정 (처음 1번, 약 10분)
1. GitHub에서 **공개(Public)** 저장소를 만듭니다. (예: `layout-leaderboard`)
   - 비공개 저장소는 Pages가 유료 플랜에서만 되므로 공개를 권장합니다.
2. 이 폴더의 모든 파일(숨김 폴더 `.github` 포함)을 저장소 `main` 브랜치에 올립니다.
   ```
   git init && git add -A && git commit -m "init"
   git branch -M main
   git remote add origin https://github.com/<아이디>/<저장소>.git
   git push -u origin main
   ```
3. **Settings → Pages**: Source = *Deploy from a branch*, Branch = `main`, 폴더 = `/docs` → Save.
4. **Settings → Actions → General → Workflow permissions**: *Read and write permissions* 선택 → Save.
5. Pages 주소 `https://<아이디>.github.io/<저장소>/` 를 팀원에게 공유합니다.

## 참가자 사용법
1. 위 주소에서 **제출하기** 클릭 (GitHub 로그인 필요).
2. Case를 고르고 CSV 내용(`dept,x,y,rot`, 헤더 포함)을 붙여넣어 제출합니다.
   Case 3, 5는 `VOID,0,0,0` 행이 필요합니다.
3. 1분 내외로 이슈에 채점 결과 댓글이 달리고, 페이지 순위가 갱신됩니다.
4. 순위표의 **내려받기/복사**로 1등을 포함한 누구의 배치 CSV든 받을 수 있습니다.

## 규칙
- 제약조건을 통과한 해만 등록되며, 목적함수는 낮을수록 우수합니다.
- 같은 참가자는 더 좋은 값일 때만 갱신됩니다. 이름은 GitHub 아이디입니다.
- 문제 JSON은 `cases/case1~5.json` 입니다. 교체하려면 같은 이름으로 덮어쓰세요
  (대회 중 교체하면 기존 기록과 기준이 달라지니 주의).

## 기록 삭제 (관리자)
**Actions → Admin - delete records → Run workflow**
- `delete_entry`: Case와 GitHub 아이디를 지정해 한 명의 기록 삭제
- `reset_case`: 해당 Case 전체 삭제

## 문제 해결
- 제출 후 댓글이 안 달리면 **Actions** 탭에서 실행 로그와 4번 설정을 확인하세요.
- 순위가 바로 안 바뀌면 Pages 배포에 1~2분이 걸릴 수 있습니다.
