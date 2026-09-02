


while :

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