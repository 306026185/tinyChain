# 

completions


计算 token 数量

### Memory unit

### Record 
这个类的设计，我们指导 memory 存储到 dataset 对应的数据结构就是 `Record`,这里不看看出 Record 的 id 就是对应于数据记录的 id
关于 `Record` 


`list_persona_files` 的方法来后去 persona 列表，然后选择一个要加载的 persona 的描述文本

```python
def retry_with_exponential_backoff(
    func,
    initial_delay: float = 1,
    exponential_base: float = 2,
    jitter: bool = True,
    max_retries: int = 20,
    error_codes: tuple = (429,),
):
```


```python
def create(
    agent_state: AgentState,
    messages,
    functions=None,
    functions_python=None,
    function_call="auto",
    # hint
    first_message=False,
    # use tool naming?
    # if false, will use deprecated 'functions' style
    use_tool_naming=True,
) -> ChatCompletionResponse:
```