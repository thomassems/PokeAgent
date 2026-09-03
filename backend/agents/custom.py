import anthropic
from llm.tools.registry import TOOLS, get_move, get_pokemon, get_type_matchups
from agents.prompts import SYSTEM_PROMPT

client = anthropic.Anthropic()


def add_user_message(messages, text):
    user_message = {"role": "user", "content": text}
    messages.append(user_message)

def add_assistant_message(messages, text):
    assistant_message = {"role": "assistant", "content": text}
    messages.append(assistant_message)

def chat(messages):
    message = client.messages.create(
        model="deepseek-v4-flash",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=messages,
        tools=TOOLS,
    )
    if message.stop_reason == "tool_use":
        tool_block = next(b for b in message.content if b.type == "tool_use")
        tool_input = tool_block.input
        if tool_block.name == 'get_pokemon':
            print('get_pokemon tool called')
            res = get_pokemon(tool_input['pokemon'])
        if tool_block.name == 'get_move':
            print('get_move tool called')
            res = get_move(tool_input['moves'])
        if tool_block.name == 'get_type_matchups':
            print('get_type_matchups called')
            res = get_type_matchups(tool_input['pokemon'], tool_input['directoin'])
        print(f"Tool result: {res}")
        return res if res else 'invalid tool called'
    
    print(message.content)
    return next(block.text for block in message.content if block.type=="text")

# start with empty message list
messages = []
user_message="Give me stats for the move body slam"
def call_agent(messages, user_message):
    while True:
        # Add the initial user question
        add_user_message(messages, user_message)

        # Get Claude's response
        answer = chat(messages)
        
        print("this is the answer")
        print(answer)

        # NEED TO GET THIS ACTUAL LOOP WORKING
        # also will need to look at the result and see if it's tool call res
        # cuz if it is then need to call agent again

        # Add Claude's response to the conversation history
        add_assistant_message(messages, answer)
        break


call_agent(messages, user_message)
# while :

    # first get whatever the user's prompt is
    # don't treat it as literal data and run an input guard on it
    # then rewrite whatever query was given
    # then pass in the additional context (conversation history, system prompt (should highlight
    # tools and such), ...)
    # then call the model, if it says it requires a tool check for this in output
    # then call that tool, and send it back the data, with the previous context
    # then let it keep running the loop until it finishes
    # also should store results or something so they can be redisplayed
    # as well as for training so the agent can actually learn
    
