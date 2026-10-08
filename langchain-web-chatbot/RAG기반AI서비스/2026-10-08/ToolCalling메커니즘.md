## Tool Calling이 뭔가?

**"LLM이 자기가 직접 답하지 못하는 일을 외부 함수에 넘기는 메커니즘"**

영어로는 Function Calling이라고도 한다.

### Tool Calling의 핵심 흐름

```
1. 사용자 질문 도착
        ↓
2. LLM이 판단:
   - "이건 내가 직접 답할 수 있어" → 일반 답변
   - "이건 도구 써야겠다" → 도구 호출 요청
        ↓
3. 시스템이 도구 실행
        ↓
4. 도구 결과를 다시 LLM에게
        ↓
5. LLM이 도구 결과 보고 최종 답변
```

## @tool 데코레이터로 도구 만들기

### 가장 단순한 도구

```python
from langchain_core.tools import tool

@tool
def add_numbers(a: int, b: int) -> int:
    """두 정수를 더합니다."""
    return a + b
```

### 도구의 4가지 핵심 요소

#### 1. 함수명 (Name)

```python
@tool
def get_weather(...):
    ...
```

#### 2. 독스트링 (Description)

```python
@tool
def get_weather(city: str) -> dict:
    """도시의 현재 날씨를 조회합니다.

    Args:
        city: 조회할 도시 이름 (한글 또는 영어)

    Returns:
        날씨 정보 딕셔너리 (온도, 습도, 상태)
    """
    ...
```

#### 3. 타입 힌트 (Type Hints)

```python
@tool
def get_weather(city: str) -> dict:
    ...
```

#### 4. 반환값 (Return)

함수가 반환하는 값.

### 도구 정보 확인하기

```python
print(add_numbers.name)         # 'add_numbers'
print(add_numbers.description)  # '두 정수를 더한 결과를...'
print(add_numbers.args)         # {'a': {'type': 'integer'}, 'b': {'type': 'integer'}}
```

## LLM에 도구 바인딩

### bind_tools 메서드

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini")

# 도구를 LLM에 바인딩
llm_with_tools = llm.bind_tools([add_numbers])
```

### 여러 도구 바인딩

```python
# 여러 도구 정의
@tool
def add_numbers(a: int, b: int) -> int:
    """두 수를 더합니다."""
    return a + b

@tool
def multiply_numbers(a: int, b: int) -> int:
    """두 수를 곱합니다."""
    return a * b

@tool
def get_weather(city: str) -> dict:
    """날씨를 조회합니다."""
    return {"temp": 22, "status": "sunny"}

# 모두 바인딩
llm_with_tools = llm.bind_tools([
    add_numbers,
    multiply_numbers,
    get_weather
])
```

### bind_tools 호출 결과

```python
response = llm_with_tools.invoke("3 + 5는 얼마?")
print(response.content)         # '' (비어있음!)
print(response.tool_calls)       # [{'name': 'add_numbers', 'args': {'a': 3, 'b': 5}, ...}]
```

- `response.content`: 비어있다.
- `response.tool_calls`: **도구를 어떻게 호출해야 하는지 정보**가 있다.

### tool_calls의 구조

`tool_calls`는 리스트이다.

```python
{
    "name": "add_numbers",          # 어떤 도구를 호출하는지
    "args": {"a": 3, "b": 5},       # 어떤 인자로
    "id": "call_abc123",            # 호출 ID (응답 연결용)
    "type": "tool_call"
}
```

## 전체 흐름 — 도구 호출 → 결과 처리 → 최종 답변

### 4단계 흐름

```
[1단계] 사용자 질문
        ↓
[2단계] LLM 1차 호출
   → "도구를 어떻게 써야 할지" 결정
        ↓
[3단계] 도구 실행 (Python 코드가 실행)
        ↓
[4단계] LLM 2차 호출
   → 도구 결과를 보고 최종 답변
```

### 코드로 구현(수동)

```python
from langchain_core.messages import HumanMessage, ToolMessage

# 1단계: 사용자 질문
question = "3 + 5는 얼마?"
messages = [HumanMessage(content=question)]

# 2단계: LLM 1차 호출 → 도구 호출 결정
response = llm_with_tools.invoke(messages)
messages.append(response)  # 응답을 메시지에 추가

print(f"도구 호출 정보: {response.tool_calls}")
# [{'name': 'add_numbers', 'args': {'a': 3, 'b': 5}, 'id': 'call_abc'}]

# 3단계: 도구 실행
for tool_call in response.tool_calls:
    tool_name = tool_call['name']
    tool_args = tool_call['args']
    tool_id = tool_call['id']

    # 도구 직접 호출
    if tool_name == "add_numbers":
        result = add_numbers.invoke(tool_args)

    # 결과를 ToolMessage로 추가
    messages.append(ToolMessage(
        content=str(result),
        tool_call_id=tool_id
    ))

# 4단계: LLM 2차 호출 → 최종 답변
final_response = llm_with_tools.invoke(messages)
print(final_response.content)
# "3 + 5는 8입니다."
```

### 메시지 흐름 시각화

```
1차 호출 전:
messages = [
    HumanMessage("3 + 5는?")
]

1차 호출 후:
messages = [
    HumanMessage("3 + 5는?"),
    AIMessage("", tool_calls=[{...add_numbers...}])  # 도구 호출 요청
]

도구 실행 후:
messages = [
    HumanMessage("3 + 5는?"),
    AIMessage("", tool_calls=[...]),
    ToolMessage("8", tool_call_id="call_abc")  # 도구 결과
]

2차 호출 후:
messages = [
    HumanMessage("3 + 5는?"),
    AIMessage("", tool_calls=[...]),
    ToolMessage("8", ...),
    AIMessage("3 + 5는 8입니다.")  # 최종 답변
]
```

### ToolMessage란?

`ToolMessage`는 LangChain의 새 메시지 종류이다.

```python
ToolMessage(
    content="8",                # 도구 실행 결과
    tool_call_id="call_abc123"  # 어떤 호출에 대한 응답인지
)
```

`tool_call_id`로 "이건 그 도구 호출 요청에 대한 답이야"를 표시한다. LLM이 이걸 보고 결과를 활용한다.

