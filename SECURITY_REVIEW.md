# 🔍 보안 및 버그 검토 보고서

## 🚨 발견된 크리티컬 이슈

### 1. **날짜 형식 검증 부재** (HIGH)

**위치**: `trinity_engine_v2.py:238`, `acp_agent.py:72-74`

**문제**:
```python
# 사용자 입력을 검증 없이 strptime 사용
target_year = datetime.strptime(target_date, "%Y-%m-%d").year
```

**위험**:
- 잘못된 날짜 형식 입력 시 `ValueError` 발생
- 서비스 중단 가능

**해결책**:
```python
def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False
```

---

### 2. **Division by Zero 위험** (MEDIUM)

**위치**: `trinity_engine_v2.py:349`

**문제**:
```python
strong = elements[yongsin_hanja] > total_elements / 5
```

**위험**:
- `total_elements`가 0일 경우 `ZeroDivisionError`
- 빈 사주 데이터 입력 시 발생 가능

**해결책**:
```python
strong = elements[yongsin_hanja] > (total_elements / 5) if total_elements > 0 else False
```

---

### 3. **오행 매핑 중복 키** (CRITICAL)

**위치**: `trinity_engine_v2.py:109`

**문제**:
```python
ELEMENT_MAP_KO = {
    "경": "금", "신": "금",  # Line 104
    ...
    "신": "금", "유": "금",  # Line 109 - 중복!
}
```

**위험**:
- "신"이 천간(辛)과 지지(申) 모두에 사용됨
- 마지막 값만 유효 → 천간 "신"이 무시됨
- **잘못된 오행 계산**

**해결책**:
- 천간/지지 분리 매핑 사용
- 또는 한자 사용

---

### 4. **파일 경로 보안** (MEDIUM)

**위치**: `backtest_engine.py:77`

**문제**:
```python
with open(self.data_path, 'w', encoding='utf-8') as f:
```

**위험**:
- `data_path`가 사용자 입력일 경우 Path Traversal 공격 가능
- 예: `../../etc/passwd`

**해결책**:
```python
import os
# 경로 정규화 및 검증
safe_path = os.path.abspath(self.data_path)
if not safe_path.startswith(os.path.abspath("./data")):
    raise ValueError("Invalid data path")
```

---

### 5. **입력 검증 부재** (HIGH)

**위치**: `acp_agent.py:72-74`

**문제**:
```python
parts = user_birth_data.split()
birth_date = parts[0]
birth_time = parts[1] if len(parts) > 1 else "12:00"
```

**위험**:
- `user_birth_data`가 빈 문자열일 경우 `IndexError`
- 악의적 입력: `"" ` → `parts[0]` 실패

**해결책**:
```python
if not user_birth_data or not user_birth_data.strip():
    raise ValueError("user_birth_data cannot be empty")
parts = user_birth_data.split()
if len(parts) < 1:
    raise ValueError("Invalid birth data format")
```

---

### 6. **에러 핸들링 미흡** (MEDIUM)

**위치**: `trinity_engine_v2.py:264`

**문제**:
```python
hour = int(birth_time.split(":")[0])
```

**위험**:
- `birth_time`이 "14:30:00" 형식일 경우 정상 작동
- `birth_time`이 "1430" 형식일 경우 `IndexError`
- `birth_time`이 "abc:def"일 경우 `ValueError`

**해결책**:
```python
try:
    hour = int(birth_time.split(":")[0])
except (ValueError, IndexError):
    raise ValueError(f"Invalid time format: {birth_time}")
```

---

## ⚠️ 잠재적 이슈

### 7. **만세력 계산 정확도** (LOW)

**위치**: `trinity_engine_v2.py:255-266`

**문제**:
```python
year_gan_idx = (birth_dt.year - 4) % 10
```

**위험**:
- 간단한 modulo 연산으로 정확도 제한
- 절입일(節入日) 미고려
- 음력 변환 미고려

**해결책**:
- Phase 3에서 `korean-lunar-calendar` 통합 예정
- 현재는 MVP로 허용 가능

---

### 8. **대운 시작 나이 고정** (LOW)

**위치**: `trinity_engine_v2.py:404`

**문제**:
```python
start_offset = 3  # 기본 3세부터 시작
```

**위험**:
- 실제 대운 시작 나이는 성별/출생년도에 따라 다름
- 남자 양년생/여자 음년생: 순행
- 남자 음년생/여자 양년생: 역행

**해결책**:
- 성별과 출생년도 기반 계산 필요
- 현재는 단순화 버전으로 허용

---

## 🔒 보안 체크리스트

| 항목 | 상태 | 위험도 |
|------|------|--------|
| SQL Injection | ✅ N/A | - |
| XSS | ✅ N/A | - |
| CSRF | ✅ N/A | - |
| Path Traversal | ⚠️ 발견 | MEDIUM |
| Input Validation | ⚠️ 발견 | HIGH |
| Error Handling | ⚠️ 발견 | MEDIUM |
| Hardcoded Secrets | ✅ 없음 | - |
| eval/exec 사용 | ✅ 없음 | - |

---

## 📋 수정 우선순위

### 🔴 HIGH (즉시 수정 필요)
1. ✅ 오행 매핑 중복 키 수정
2. ✅ 날짜 형식 검증 추가
3. ✅ 입력 검증 강화

### 🟡 MEDIUM (Phase 3 전 수정)
4. ✅ Division by Zero 방지
5. ✅ 파일 경로 보안 강화
6. ✅ 에러 핸들링 개선

### 🟢 LOW (추후 개선)
7. ⏳ 만세력 계산 정확도 (Phase 3)
8. ⏳ 대운 시작 나이 계산 (Phase 3)

---

## 🛠️ 수정 계획

### 1단계: 크리티컬 이슈 수정
- 오행 매핑 분리
- 입력 검증 함수 추가
- 에러 핸들링 강화

### 2단계: 보안 강화
- 파일 경로 검증
- Division by Zero 방지

### 3단계: 테스트
- 악의적 입력 테스트
- 경계값 테스트
- 에러 케이스 테스트
