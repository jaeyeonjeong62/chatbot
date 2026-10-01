## LangChain이란 무엇인가

### 정의

**LLM 애플리케이션을 만들 때 자주 쓰는 패턴들을 모아놓은 도구 상자**

### LangChain이 해결하는 4가지 문제

**문제1: 프롬프트가 코드 곳곳에 박혀 있음**

$\rightarrow$ `ChatPromptTemplate`로 프롬프트를 템플릿화. 변수만 바꿔 재사용 가능.

**문제2: 다단계 작업 시 코드가 복잡해짐**

$\rightarrow$ `|` 파이프 연산자로 단계를 자연스럽게 연결.

**문제3: 모델 교체 시 코드 전체를 바꿔야 함**

$\rightarrow$ 모든 모델이 같은 인터페이스. import 한 줄과 클래스 이름만 바꾸면 됨.

**문제4: Tool, 메모리, RAG 같은 고급 기능 직접 구현**

$\rightarrow$ `@tool` 데코레이터, `Memory`, `RAG` 모두 표준화된 방식으로 제공.

### LangChain을 쓰는 이유

- **코드 재사용성**: 같은 패턴을 여러 번 짜지 않음
- **유지보수**: 프롬프트만 별도로 수정 가능
- **유연성**: 모델/도구/메모리 자유롭게 교체
- **생태계**: 수백 개의 통합 도구(Pinecone, Chroma, Tavily 등) 즉시 사용

### LangChain 패키지 구조

```
langchain-core          # 인터페이스/추상 클래스 (가장 가벼움)
langchain-openai        # OpenAI 전용 통합
langchain-anthropic     # Claude 전용 통합
langchain-community     # Chroma, Tavily 등 커뮤니티 통합
langchain               # 위 패키지를 묶은 메타 패키지
```

### 왜 분리되어 있나?

**의존성 충돌 방지**

OpenAI만 쓰는 프로젝트에 Anthropic 패키지가 따라오면 무겁고 충돌 가능성이 커짐

## LangChain의 4대 추상화

### 4대 추상화 한눈에 보기

|추상화|역할|예시 클래스|
|---|---|---|
|**Models**|LLM과 통신하는 인터페이스|`ChatOpenAI`, `ChatAnthropic`|
|**Prompts**|프롬프트를 템플릿화|`ChatPromptTemplate`|
|**Chains**|여러 단계를 연결|LCEL `prompt \| llm \| parser`|
|**Agents**|LLM이 자율 판단|`AgentExecutor`|

### Models: 모델 통합 추상화

**다양한 LLM을 같은 인터페이스로 다룰 수 있게 해줌**

#### OpenAI SDK vs LangChain 비교

**OpenAI SDK 직접 호출**:

```python
from openai import OpenAI
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "안녕"}]
)
print(response.choices[0].message.content)
```

**LangChain 사용**:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")
response = llm.invoke("안녕")
print(response.content)
```

- `messages=[{"role": ..., "content": ...}]` 구조 → **단순 문자열로도 OK**
- `response.choices[0].message.content` (3단 깊이) → **`response.content`** (1단)
- 모델 함수가 `chat.completions.create` → **그냥 `invoke`**

#### 모델 교체의 위력

```python
# OpenAI
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini")

# Claude로 변경
from langchain_anthropic import ChatAnthropic
llm = ChatAnthropic(model="claude-sonnet-4")

# 나머지 코드는 동일!
response = llm.invoke("안녕")
print(response.content)
```

### Prompts: 프롬프트 템플릿화

**프롬프트를 재사용 가능한 템플릿으로 만드는 추상화**

#### 직접 작성 vs 템플릿화

**직접 작성 (반복 코드)**:

```python
question = "이상치 탐지 방법은?"
role = "데이터 분석가"

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": f"당신은 {role}입니다."},
        {"role": "user", "content": question}
    ]
)
```

**ChatPromptTemplate 사용**:

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 {role}입니다."),
    ("human", "{question}")
])

# 변수만 바꿔서 재사용
result = prompt.invoke({"role": "데이터 분석가", "question": "이상치 탐지 방법은?"})
```

- 프롬프트 구조가 **별도로 정의**됨 (코드와 분리)
- `{role}`, `{question}` 같은 **변수**로 바뀔 부분만 표시
- 호출할 때 **변수만 채워넣으면** 됨

#### ChatPromptTemplate의 메시지 역할

|OpenAI 표기|LangChain 표기|의미|
|---|---|---|
|`"role": "system"`|`("system", "...")`|AI에게 주는 지시|
|`"role": "user"`|`("human", "...")`|사용자 메시지|
|`"role": "assistant"`|`("ai", "...")`|AI 답변|

### Chains: 단계 연결

**여러 작업을 연결하는 추상화**

```python
chain = prompt | llm
result = chain.invoke({"role": "분석가", "question": "이상치란?"})
```

### Agents: 자율 판단

**LLM이 스스로 도구를 선택해 사용하는 추상화**

---

## LCEL과 파이프 연산자

### LCEL이란?

**LangChain Expression Language**

LangChain의 새로운 표준 표현 방식

### 파이프 연산자의 직관적 이해

#### 리눅스 파이프

```bash
ls -la | grep "py" | head -5
```

#### LangChain 파이프

```python
chain = prompt | llm | parser
```

### 왜 파이프 방식이 좋은가

#### 가독성이 뛰어남

```python
# 일반 방식 (변수 받아서 넘기기)
formatted = prompt.invoke({"role": "분석가", "question": "..."})
response = llm.invoke(formatted)
result = parser.invoke(response)

# LCEL 방식
chain = prompt | llm | parser
result = chain.invoke({"role": "분석가", "question": "..."})
```

#### 자동으로 따라오는 4가지 혜택

**1. 비동기 자동 지원** (`ainvoke`, `astream`)

```python
result = await chain.ainvoke({"role": "분석가", "question": "..."})
```

**2. 스트리밍 자동 지원** (토큰 단위 출력)

```python
for chunk in chain.stream({"role": "분석가", "question": "..."}):
    print(chunk.content, end="")
```

**3. 배치 처리 자동 지원** (여러 입력 동시 처리)

```python
results = chain.batch([
    {"role": "분석가", "question": "..."},
    {"role": "마케터", "question": "..."}
])
```

**4. LangSmith 추적 자동 지원** (디버깅·모니터링)

### Runnable 인터페이스

`prompt`, `llm`, `parser`가 모두 `|`로 연결될 수 있는 이유는 **공통 인터페이스**를 따르기 때문

이 공통 인터페이스를 **Runnable**이라고 함

| 메서드 | 설명 |
| --- | --- |
| `invoke(input)` | 단일 입력 처리 |
| `stream(input)` | 토큰 단위 스트리밍 |
| `batch([inputs])` | 여러 입력 병렬 처리 |
| `ainvoke`, `astream` | 비동기 버전 |

prompt도 Runnable, llm도 Runnable, parser도 Runnable. 그래서 `|`로 연결할 수 있어요.

체인 자체도 Runnable이라서 다른 체인과 또 연결할 수 있습니다.

```python
sub_chain = prompt | llm
big_chain = sub_chain | parser  # 이것도 가능!
```

## ChatPromptTemplate 깊이 이해하기

### 기본 구조

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 {role}입니다. 한국어로 답변하세요."),
    ("human", "{question}")
])
```

- `from_messages([...])`: 메시지 리스트로 템플릿 생성
- 각 항목은 `(역할, 텍스트)` 튜플
- `{변수}` 중괄호는 채워질 자리

### 변수 채우기

`invoke()`에 딕셔너리를 넘기면 변수가 채워진다.

```python
# 변수 채우기 (LLM 없이도 가능)
formatted = prompt.invoke({
    "role": "데이터 분석가",
    "question": "이상치 탐지 방법은?"
})
print(formatted)
```

결과는 변수가 채워진 **메시지 객체 리스트**가 나온다.

```python
[
  SystemMessage(content="당신은 데이터 분석가입니다. 한국어로 답변하세요."),
  HumanMessage(content="이상치 탐지 방법은?")
]
```

이걸 LLM에 넘기면 답변이 나온다.



