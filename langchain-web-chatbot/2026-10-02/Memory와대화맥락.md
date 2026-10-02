## LLM이 왜 대화를 기억하지 못하나

```
ChatGPT 사이트의 동작:
1. 사용자가 1차 질문
2. ChatGPT 서버에 메시지 저장
3. LLM 호출 (1차 메시지만 보냄)
4. 답변 받아서 사용자에게 표시 + 서버에 저장

5. 사용자가 2차 질문
6. ChatGPT 서버에 추가 저장
7. LLM 호출 (1차 메시지 + 1차 답변 + 2차 메시지 모두 보냄!)  ← 여기!
8. 답변 받아서 표시 + 저장
```

### Stateless의 장점

#### 장점 1: 확장성

서버 한 대에 모든 사용자의 대화를 저장하면 그 서버가 다운될 때 전부 망가진다. Stateless면 어떤 서버든 같은 입력에 같은 결과를 내니까, 수천 대의 서버로 분산 처리 가능하다.

#### 장점 2: 단순성

LLM 자체는 매우 단순한 구조가 된다. 어떤 메시지를 받느냐만 신경 쓰면 된다.

#### 장점 3: 유연성

대화 맥락을 어떻게 관리할지를 **개발자가 자유롭게 결정**할 수 있다. 토큰 절약, 사용자 격리, 영속화 등 필요에 맞게 구현 가능하다.

## 메모리의 3가지 종류

### 종류 1: Buffer Memory (버퍼 메모리)

#### 동작 방식

**모든 메시지를 그대로 저장**

```
대화 1: "안녕"          → AI: "안녕하세요"
대화 2: "이름이 뭐야"    → AI: "AI입니다"
대화 3: "Python 알려줘" → AI: "Python은..."

저장된 메모리:
  [System, "안녕", "안녕하세요", "이름이 뭐야", "AI입니다", "Python 알려줘", "Python은..."]
  (전부 다)
```

#### 장점

- 가장 정확한 대화 맥락 유지
- 이전 정보를 잃지 않음

#### 단점

- 대화가 길어질수록 토큰 비용 폭증
- 컨텍스트 한도 도달 시 에러

#### 사용처

- 짧은 대화 (10-20턴 이하)
- 정확한 정보 유지가 중요한 경우 (의료 상담, 법률 자문 등)

### 종류 2: Window Memory (윈도우 메모리)

#### 동작 방식

**최근 N개의 메시지만 저장**

```
window_size = 4 (최근 4개만 유지)

대화 진행:
  ["안녕", "안녕하세요", "이름이 뭐야", "AI입니다"]

대화 5턴: "Python 알려줘"
  → ["이름이 뭐야", "AI입니다", "Python 알려줘", "Python은..."]
  ↑ "안녕", "안녕하세요"는 잘림!
```

#### 장점

- 토큰 비용 통제 가능
- 컨텍스트 한도 걱정 없음
- 메모리 사용량 일정

#### 단점

- 오래된 정보 손실
- "내 이름은 진환이야" 같은 초기 정보가 잊혀짐

#### 사용처

- 중간 길이 대화 (20-50턴)
- 최근 맥락만 중요한 경우 (FAQ 봇, 검색 도우미)

### 종류 3: Summary Memory (요약 메모리)

#### 동작 방식

**대화가 길어지면 LLM이 요약**

```
대화 1-10: 일반 메시지 그대로 저장
대화 11-20: 1-10을 요약해서 1줄로 압축

저장된 메모리:
  [System, "이전 대화 요약: 사용자는 진환이고 Python을 배우고 싶어함",
   대화 11-20 메시지들]
```

#### 장점

- 매우 긴 대화도 처리 가능
- 토큰 절약

#### 단점

- 요약 과정에서 정보 손실
- 추가 LLM 호출로 비용 증가
- 구현 복잡

#### 사용처

- 매우 긴 대화 (50턴+)
- 장기 기억이 필요한 챗봇 (개인 비서 등)

### 메모리 선택 가이드

| 상황 | 추천 메모리 |
| --- | --- |
| 짧은 대화 (10턴 이하) | **Buffer** |
| 중간 대화 (20-50턴) | **Window (k=10)** |
| 긴 대화 (50턴+) | **Summary** 또는 **Summary + Window** |
| 처음 배울 때 | **Buffer** (가장 단순) |

## 예전 방식 vs 현재(표준) 방식

### 예전 방식 (Deprecated, 사용 X)

```python
# 옛날 LangChain 코드
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory)

conversation.predict(input="안녕")
```

**LangChain 0.1 시절**

- `ConversationBufferMemory`
- `ConversationBufferWindowMemory`
- `ConversationSummaryMemory`
- `LLMChain`
- `ConversationChain`

**모두 deprecated 예정**

### 현재 표준 방식

```python
# 현재 표준
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# 체인을 메모리로 감싸기
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history"
)
```

핵심 클래스 두 가지:

- **`RunnableWithMessageHistory`**: 체인에 메모리를 자동으로 추가하는 wrapper
- **`InMemoryChatMessageHistory`**: 메시지 저장소 (Python 메모리에 보관)

### 왜 바뀌었나?

기존 방식의 문제점:

1. **LCEL과 호환성 부족**: `prompt | llm` 같은 우아한 방식과 잘 안 맞음
2. **비동기 지원 부족**: `ainvoke`, `astream` 사용 어려움
3. **타입 추론 약함**: 어떤 입력·출력인지 알기 어려움

새 방식의 장점:

1. **LCEL 완벽 호환**: 기존 체인을 그대로 감싸기만 하면 됨
2. **모든 Runnable 기능 사용 가능**: 비동기, 스트리밍, 배치 모두 OK
3. **세션 분리 표준**: `session_id`로 깔끔하게 사용자별 격리

## RunnableWithMessageHistory 깊이 이해

### 핵심 구성 요소

#### 1. ChatPromptTemplate에 MessagesPlaceholder

프롬프트 템플릿에 **이전 메시지가 들어갈 자리**를 미리 만들어두어야 한다.

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 친절한 AI 어시스턴트입니다."),
    MessagesPlaceholder("history"),    # ← 이전 메시지 자리!
    ("human", "{question}")
])
```

`MessagesPlaceholder("history")`는 "여기에 이전 대화 메시지들이 들어갈 거야"라고 미리 표시하는 것이다.

#### 2. 세션 저장소 함수

```python
from langchain_core.chat_history import InMemoryChatMessageHistory

# 메모리 저장소 (Python 사전)
store = {}

def get_session_history(session_id: str):
    """session_id로 히스토리를 찾거나 새로 만들기"""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]
```

- `store`: 모든 사용자의 히스토리를 담는 사전
- `get_session_history(session_id)`: 특정 사용자의 히스토리 반환
- 처음 보는 session_id면 빈 히스토리 새로 만들기

#### 3. 체인을 메모리로 감싸기

```python
from langchain_core.runnables.history import RunnableWithMessageHistory

# 기본 체인
chain = prompt | llm

# 메모리 추가
chain_with_memory = RunnableWithMessageHistory(
    chain,                              # 감쌀 체인
    get_session_history,                # 히스토리 가져오는 함수
    input_messages_key="question",      # 사용자 입력 변수 이름
    history_messages_key="history"      # MessagesPlaceholder 이름
)
```

이제 `chain_with_memory`는 호출할 때마다 자동으로:

1. 해당 session의 이전 히스토리 가져옴
2. 프롬프트의 `MessagesPlaceholder("history")` 자리에 끼워넣음
3. LLM 호출
4. 사용자 메시지·AI 답변을 자동으로 히스토리에 추가

#### 4. session_id와 함께 호출

```python
config = {"configurable": {"session_id": "user_001"}}

# 1차 호출
chain_with_memory.invoke(
    {"question": "내 이름은 진환이야"},
    config=config
)

# 2차 호출 (같은 session_id)
chain_with_memory.invoke(
    {"question": "내 이름이 뭐였지?"},
    config=config
)
# → "진환"으로 답변! 자동으로 기억함
```

### 다른 사용자는 다른 session_id

```python
# 사용자 A
chain_with_memory.invoke(
    {"question": "내 이름은 진환이야"},
    config={"configurable": {"session_id": "user_001"}}
)

# 사용자 B (다른 session_id!)
chain_with_memory.invoke(
    {"question": "내 이름이 뭐였지?"},
    config={"configurable": {"session_id": "user_002"}}
)
# → "알 수 없습니다" (사용자 B는 처음이니까)
```

**자동 사용자 격리**

### 동작 흐름 그림

```
[사용자] "내 이름이 뭐였지?" + session_id="user_001"
     ↓
[chain_with_memory.invoke()]
     ↓
[get_session_history("user_001")] ──→ 이전 히스토리 가져옴
     ↓                                  ["내 이름은 진환이야", "안녕 진환님"]
[프롬프트 조립]
     ↓
SystemMessage("당신은 AI입니다")
HumanMessage("내 이름은 진환이야")        ← MessagesPlaceholder 자리에 자동 삽입
AIMessage("안녕 진환님")
HumanMessage("내 이름이 뭐였지?")         ← 새 입력
     ↓
[LLM 호출]
     ↓
"진환님이라고 하셨습니다."
     ↓
[히스토리 자동 업데이트]
     ↓
사용자에게 답변 반환
```

## 메모리 영속화

### InMemoryChatMessageHistory의 한계

지금까지 본 `InMemoryChatMessageHistory`는 **Python 프로세스가 끝나면 사라진다**. 노트북을 다시 시작하거나 서버를 재시작하면 모든 대화가 날아간다.

실제 서비스에서는 외부 저장소가 필요하다.

### 영속 저장소 옵션

#### Redis (가장 흔함)

```python
from langchain_redis import RedisChatMessageHistory

def get_session_history(session_id):
    return RedisChatMessageHistory(
        session_id=session_id,
        redis_url="redis://localhost:6379"
    )
```

- 빠른 메모리 기반 DB
- 대규모 채팅 서비스에 적합

#### MongoDB

```python
from langchain_community.chat_message_histories import MongoDBChatMessageHistory

def get_session_history(session_id):
    return MongoDBChatMessageHistory(
        session_id=session_id,
        connection_string="mongodb://localhost:27017",
        database_name="chatbot",
        collection_name="messages"
    )
```

- 도큐먼트 DB
- 메타데이터 저장에 유리

#### PostgreSQL

```python
from langchain_postgres import PostgresChatMessageHistory

def get_session_history(session_id):
    return PostgresChatMessageHistory(
        session_id=session_id,
        connection_string="postgresql://..."
    )
```

- 관계형 DB
- 기존 시스템과 통합 좋음

### 핵심 포인트: 비즈니스 로직 변동이 없다

**저장소만 바꾸면 된다**.

```python
# InMemory → Redis로 변경
def get_session_history(session_id):
    # 이 함수만 바꾸면 끝!
    return RedisChatMessageHistory(
        session_id=session_id,
        redis_url="redis://localhost:6379"
    )

# 나머지 코드는 동일!
chain_with_memory = RunnableWithMessageHistory(...)
```

**함수 한 줄만 바꿔서** 영속 메모리로 전환한다.

## 토큰 비용 폭발 방지

### 해결: trim_messages로 자동 압축

```python
from langchain_core.messages import trim_messages

trimmer = trim_messages(
    max_tokens=2000,        # 2000 토큰 안에 유지
    strategy="last",        # 최근 메시지 우선
    token_counter=llm,      # 토큰 카운터로 LLM 사용
    include_system=True     # 시스템 메시지는 유지
)

# 체인에 통합
chain = prompt | trimmer | llm
```

`trim_messages`가 매 호출마다 메시지가 너무 많으면 오래된 것부터 잘라낸다. 컨텍스트 한도 초과·비용 폭증을 자동으로 막아준다.

## 정리

### 개념

- LLM의 **Stateless** 특성과 그 의미
- ChatGPT가 어떻게 대화를 기억하는 것처럼 보이는지
- 메모리의 3가지 종류 (Buffer, Window, Summary)
- 기존 방식(deprecated) vs 현재 방식(`RunnableWithMessageHistory`)

### 현재(표준) 방식의 4가지 구성 요소

1. **MessagesPlaceholder("history")**: 이전 메시지 들어갈 자리
2. **get_session_history 함수**: 세션별 히스토리 저장소
3. **RunnableWithMessageHistory**: 체인에 메모리 추가하는 wrapper
4. **session_id**: 사용자별 격리

### 핵심 코드 패턴

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

# 1. 프롬프트 (history 자리 만들기)
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 친절한 AI입니다."),
    MessagesPlaceholder("history"),
    ("human", "{question}")
])

# 2. 세션 저장소
store = {}
def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# 3. 체인을 메모리로 감싸기
chain = prompt | llm
chain_with_memory = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="question",
    history_messages_key="history"
)

# 4. session_id와 함께 호출
chain_with_memory.invoke(
    {"question": "..."},
    config={"configurable": {"session_id": "user_001"}}
)
```
