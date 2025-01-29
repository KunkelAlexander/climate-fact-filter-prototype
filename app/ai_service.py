# ai_service.py

from openai import OpenAI

client = OpenAI()

def check_truth_with_chatgpt(extracted_text):
    """
    Queries the OpenAI API (ChatGPT) to check if the extracted text is true or false.
    Returns a short response from ChatGPT.
    """
    prompt = (
        "Is this a true or false statement about global warming? "
        "If it is false, please rewrite the key false statement as a truthful statement. "
        f"{extracted_text}"
    )

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # or the model you choose
            messages=[
                {"role": "system", "content": "Keep your answer very short."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=100,
            temperature=0.7
        )
        chatgpt_answer = completion.choices[0].message.content
        return chatgpt_answer
    except Exception as e:
        print("Error calling OpenAI API:", e)
        return "Unable to determine truthfulness due to an API error."
