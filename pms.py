import re

input_path = input('input: ')
output_path = input('output: ')

with open(input_path, 'r', encoding='utf-8') as file:
    matches = file.read().splitlines()

print(matches)
pattern_line = r"(\d+):(\d+)(.*) - (.*) -:-"
compiled = re.compile(pattern_line)

new_lines = []

for match in matches:
    m = compiled.match(match)
    print(m)
    if not m:
        continue
    line = "{} - {} (typujemy do 24.07 do godziny {}:{})".format(m.group(3), m.group(4),
                                                                 m.group(1), m.group(2))
    print(line)
    new_lines.append(line)

with open(output_path, 'w', encoding='utf-8') as wfile:
    for line in new_lines:
        wfile.write(line)
        wfile.write('\n')
# KONIEC


