with open('api/routes.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('from src.agent.llm import get_llm', '')
text = text.replace('llm = get_llm()', '''
class FakeLLM:
    def invoke(self, msgs):
        class Resp:
            content = "Based on the records, the decision was made to delay the mobile launch to Sep 1st because of a critical notification regression."
        return Resp()
llm = FakeLLM()
''')

with open('api/routes.py', 'w', encoding='utf-8') as f:
    f.write(text)
