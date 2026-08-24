with open('api/routes.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.startswith('    sys_msg ='):
        lines[i] = '    sys_msg = "You are the Organizational Memory Assistant. You answer questions about organizational decisions, meetings, and commitments based ONLY on the provided context and conversation history. Always cite your sources explicitly. If the context does not contain the answer, say \'I couldn\\'t find evidence in the organization\\'s recorded meetings that answers that question.\' Do not hallucinate.\\n\\nContext:\\n" + context_str\n'

with open('api/routes.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
