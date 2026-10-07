## Runnable이라는 통일된 인터페이스

---

### Runnable

#### 핵심 개념

Runnable은 "입력을 받아 출력을 내보내는 부품"이 공통으로 따르는 규격

**모든 Runnable이 갖는 공통 메서드**

| 메서드 | 하는 일 | 비유 |
| --- | --- | --- |
| `invoke(입력)` | 입력 1개 → 결과 1개 | 자판기에 동전 한 번 넣기 |
| `batch([입력들])` | 여러 입력을 한꺼번에 처리 | 주문 여러 개를 한 번에 넣기 |
| `stream(입력)` | 결과를 조각조각 실시간으로 받음 | 챗봇 답변이 한 글자씩 나오는 것 |
| `ainvoke` / `abatch` / `astream` | 위 메서드의 비동기 버전 | 기다리는 동안 다른 일 하기 |

**용어 정리**

- **체인(Chain)**: 여러 Runnable을 순서대로 연결한 것. 체인 자체도 Runnable이다.
- **LCEL(LangChain Expression Language)**: `|` 기호로 부품을 연결하는 문법.
- **`|` (파이프)**: "앞 부품의 출력을 뒤 부품의 입력으로 넘겨라"는 뜻.

---

### 새로 배울 Runnable 3가지

#### 1. RunnableParallel — 병렬 실행

여러 체인을 **동시에 실행**해서 결과를 dict로 받는다.

```python
parallel = RunnableParallel(
    analysis=analysis_chain,
    reply=reply_chain
)

result = parallel.invoke({"review": "..."})
# result["analysis"], result["reply"]
```

#### 2. RunnablePassthrough — 입력을 그대로 흘려보냄

입력을 그대로 다음 단계에 전달한다. **데이터를 합칠 때** 유용하다.

```python
# 분석 + 원본 리뷰도 함께
chain = RunnableParallel(
    analysis=analysis_chain,
    original_review=RunnablePassthrough()
)
```

#### 3. RunnableLambda — 일반 함수를 Runnable로

Python 함수를 Runnable로 변환한다. **사용자 정의 로직**을 체인에 끼워넣을 때 사용.

```python
def to_upper(x):
    return x.upper()

upper_runnable = RunnableLambda(to_upper)
```

