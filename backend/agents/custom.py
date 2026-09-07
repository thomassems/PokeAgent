import anthropic
from llm.tools.registry import TOOLS, TOOL_FUNCTIONS, get_move, get_pokemon, get_type_matchups, web_search
from agents.prompts import SYSTEM_PROMPT
import json

NUM_ITERS=3
MAX_RESULT=5

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
    print(message.content)
    return message

# start with empty message list
messages = []
user_message="Give me stats for the move body slam"
# user_message="What is a good team to beat Cynthia with in gen4 Diamond"
# USER MESSAGE WILL JUST BE WHATEVER USER INPUTS
def call_agent(messages, user_message):
    # Add the initial user question
    add_user_message(messages, user_message)

    iteration = 1
    while iteration <= NUM_ITERS:
        print({len(messages)})
        print(f"This is iteration: #{iteration}")

        answer = chat(messages)
        print(f'this is the {answer}')
        add_assistant_message(messages, answer.content)

        if answer.stop_reason == "tool_use":
            tool_results = []
            for b in answer.content:
                if b.type == "tool_use":
                    tool_input = b.input          
                    if b.name == 'get_pokemon':
                        print('get_pokemon tool called')
                        res = get_pokemon(tool_input['pokemon'])
                    if b.name == 'get_move':
                        print('get_move tool called')
                        res = get_move(tool_input['moves'])
                    if b.name == 'get_type_matchups':
                        print('get_type_matchups called')
                        res = get_type_matchups(tool_input['pokemon'], tool_input['direction'])
                    if b.name == 'web_search':
                        print('web_search called')
                        res = web_search(tool_input['query'], tool_input.get('max_results', MAX_RESULT))
                    if b.name not in TOOL_FUNCTIONS:
                        raise ValueError(
                            f"Unknown tool '{b.name}'. Available: {', '.join(TOOL_FUNCTIONS)}"
                        )
                    print(f"Tool result: {res}")
                    if res:
                        tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": json.dumps(res),
                        })
            # INTERESTING - tool results count as user message, since the API must alternate between
            # user and assistant
            if tool_results:
                add_user_message(messages, tool_results)

        if answer.stop_reason == "end_turn":
            print(f"Agent stopped on iteration: {iteration}")
            text = "".join(b.text for b in answer.content if b.type == "text")
            print(f"Final answer{text}")
            break
        iteration+=1


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
    
