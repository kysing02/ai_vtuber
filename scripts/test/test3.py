import re

# Input strings
input1 = "{!ENTER_DISCORD} {!ENTER_DISCORD_VOICE_CHAT}"
input2 = "{!NEW_ACTION 家に行く} {!NEW_ACTION 友達と遊ぶ}"

# Function to extract and process commands
def process_commands(input_string):
    # Regular expression to match commands
    command_pattern = re.compile(r'\{!(.*?)\}')
    
    # Find all commands in the input string
    commands = command_pattern.findall(input_string)
    
    # List to store the final result as (command, description)
    result = []
    
    for command in commands:
        # Split the command into name and description (if any)
        if " " in command:
            # Split into command name and description
            command_name, description = command.split(maxsplit=1)
            result.append((f"!{command_name}", description))
        else:
            # If no description, set description to empty string
            result.append((f"!{command}", ""))
    
    return result

# Process the input strings
output1 = process_commands(input1)
output2 = process_commands(input2)

print(output1)  # Output: [('!ENTER_DISCORD', ''), ('!ENTER_DISCORD_VOICE_CHAT', '')]
print(output2)  # Output: [('!NEW_ACTION', '家に行く'), ('!NEW_ACTION', '友達と遊ぶ')]