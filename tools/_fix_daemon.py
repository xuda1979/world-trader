import sys

path = sys.argv[1]
with open(path, "r") as f:
    content = f.read()

old_marker = "function scheduleBootRetry() {"
func_start = content.find(old_marker)
if func_start < 0:
    print("scheduleBootRetry not found")
    sys.exit(1)

timeout_start = content.find("setTimeout(async () => {", func_start)
if timeout_start < 0:
    print("setTimeout not found")
    sys.exit(1)

close_marker = "    }, delay);"
close_pos = content.find(close_marker, timeout_start)
if close_pos < 0:
    print("delay); not found")
    sys.exit(1)

inner_start = timeout_start + len("setTimeout(async () => {")
inner_end = close_pos
inner_content = content[inner_start:inner_end]

if "repairProfileAndReboot" in inner_content:
    print("repairProfileAndReboot already present")
    sys.exit(0)

search = "console.error(""[daemon:"" + args.env + """" Background auth retry"
repair_block = (
    "if (bootAttemptCount >= 2) {
"
    "          console.error(""[daemon:"" + args.env + """" Multiple auth failures, running profile repair..."""");
"
    "          await repairProfileAndReboot();
"
    "        }
"
    "        console.error(""[daemon:"" + args.env + """" Background auth retry"
)

new_inner = inner_content.replace(search, repair_block)
if new_inner == inner_content:
    print("Could not find pattern to insert before")
    sys.exit(1)

content = content[:inner_start] + new_inner + content[inner_end:]
with open(path, "w") as f:
    f.write(content)
print("Updated scheduleBootRetry with repair call")
