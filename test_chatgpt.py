from openai import OpenAI

# Initialize the OpenAI client with your API key
client = OpenAI(api_key="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")


def check_truth_statement(statement):
    # Prompt to be sent to the API
    prompt = f"Is this true or false? {statement}"

    try:
        # Send the prompt to OpenAI's ChatGPT model
        completion = client.chat.completions.create(
            model="gpt-4",  # or use another available model like "gpt-4-turbo" or "gpt-3.5-turbo"
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers whether statements are true or false."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,  # Limit response length
            temperature=0.5  # Lower temperature for more factual responses
        )

        print(completion.choices[0].message.content)

        # Extract and return the response content
        answer = completion.choices[0].message.content
        return answer

    except Exception as e:
        print("Error calling OpenAI API:", e)
        return "Unable to determine truthfulness due to an API error."

# Test the function with "The earth is flat" as the statement
statement = "The earth is flat"
result = check_truth_statement(statement)
print("Response from ChatGPT:", result)
