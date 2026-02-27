import os

file_path = 'tools/populate_real_menu.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(', "Normal"', '')
content = content.replace('"Normal", ', '')
content = content.replace('["Normal"]', '[]')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
