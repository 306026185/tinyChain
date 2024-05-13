# tinyChain
## 概述(introdution)
参考 langchain API 来实现一个精简版的 agent 框架，主要根据实际应用场景提供更多解决方案，例如如何基于 tinyChain 搭建 agentOS 


## 特点(features)
- 注重应用落地，提供丰富的实际落地的案例
- 完备的文档，不仅仅是一个 agent 框架，也是学习基于 llm 的 agent 如何设计和实现的必备的知识手册
- 提供了多个语种版本，包括 c/c++ golang 和 rust 版本

## 安装(Install)
```
python setup.py install
```

## 快速上手(quick start)
```python
from tinychain.llm import ChatbotAI

llm = ChatbotAI(model_name="llama2")
rsp = llm.invoke("how can langsmith help with testing?")
```

## core
- prompts
- llms
- output parsers
- chat models


## engine
- tools
- agents
- chains

## extension
- graph
- cv models
- nlp models

## solutions
- llmOS
- agentOS
- RAG


## TODO
- 模块化
- 基础设施搭建

## examples

### 链式调用
```python 
from tinychain.prompt.chat_prompt import ChatPromptTemplate
from tinychain.llm.ollama_chat_model import OllamaChatbotAI

from tinychain.runnable.runnable_manager import RunableManager


prompt = ChatPromptTemplate.from_template("tell me a joke about {topic}")

runable_manager = RunableManager()
runable_manager.head = prompt
prompt.next = OllamaChatbotAI()
runable_manager.invoke({"topic": "bears"})
print(runable_manager.context)
```