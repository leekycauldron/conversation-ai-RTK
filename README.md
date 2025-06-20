# Conversation AI Real-Time Knowledge (RTK) - Memory

Give CAI a brain to remember facts.

## Endpoints

`/save-fact` `[POST]` Save a fact to memory.

```json
{
    "fact": "I like cheese."
}
```

## Setup tool calling in Conversational AI

Add a webhook tool, put in details for the URL, make it a POST request, pass in JSON like
the example above, instead of a string literal for the fact-value input it as a `LLM prompt` type parameter. Give a description of how the agent should use the tool (e.g. "when user asks you to remember something")

`#TODO: Add example descriptions.`
