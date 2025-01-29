from secret import OPENAI_API_KEY
from openai import OpenAI
import search_faiss # Make sure this import points to your actual FAISS module
import re

client = OpenAI(api_key=OPENAI_API_KEY)

def call_api(system_instructions, user_prompt):
    # 4. Call the OpenAI Chat Completion API
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Or whichever model you are using
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.7
        )
        answer = completion.choices[0].message.content.strip()

    except Exception as e:
        print("Error calling OpenAI API:", e)
        return "Unable to determine truthfulness due to an API error."

    return answer


def parse_llm_response(chatgpt_answer):
    """
    Parses the LLM response to extract probability values
    and determine a boolean flag for truthfulness.
    """
    # Regular expressions to extract probabilities
    true_match = re.search(r"Probability True:\s*(\d+)%", chatgpt_answer)
    false_match = re.search(r"Probability False:\s*(\d+)%", chatgpt_answer)
    undecided_match = re.search(r"Probability Undecided:\s*(\d+)%", chatgpt_answer)

    # Convert matches to integers
    prob_true = int(true_match.group(1)) if true_match else 0
    prob_false = int(false_match.group(1)) if false_match else 0
    prob_undecided = int(undecided_match.group(1)) if undecided_match else 100  # Default to undecided if not found

    # Determine the boolean flag
    if prob_true > 50:
        is_likely_true = True
    elif prob_false > 50:
        is_likely_true = False
    else:
        is_likely_true = None  # Indicates "Undecided"

    return {
        "probability_true": prob_true,
        "probability_false": prob_false,
        "probability_undecided": prob_undecided,
        "is_likely_true": is_likely_true
    }

def check_truth_with_chatgpt(
    extracted_text: str,
    faiss_index,
    embedding_model,
    all_chunks,
    metadata,
    normalise=True,
    alpha=0.05,
    selected_types=None,
    max_sources: int = 5
):
    """
    1. Searches the FAISS index with the user's text (extracted_text).
    2. Passes the user statement and top matching snippets to ChatGPT.
    3. Returns a short response deciding if the statement is true or false,
       with corrections if false, and citing the sources used.

    Parameters:
    -----------
    extracted_text : str
        The user’s statement (or text) to be verified.
    faiss_index : FAISS object
        The FAISS index you have already initialized.
    embedding_model : Any
        Your loaded embedding model (e.g., SentenceTransformer, etc.).
    all_chunks : list
        The list of all text chunks used to build the FAISS index.
    metadata : pd.DataFrame or list[dict]
        The metadata corresponding to your chunks. Must contain columns
        or keys for 'title'/'url' if you want ChatGPT to cite sources.
    normalise : bool
        Indicates whether embeddings are normalized or not.
    alpha : float
        Date decay factor or any additional weighting factor used in search.
    selected_types : list or None
        If not None, the search function will filter results by these types.
    max_sources : int
        Maximum number of sources/snippets to pass to ChatGPT.

    Returns:
    --------
    str
        A short response from ChatGPT indicating truthfulness and citing sources.
    """

    # 1. Use FAISS to retrieve top matching snippets
    results = search_faiss.search_pdfs(
        query=extracted_text,
        index=faiss_index,
        model=embedding_model,
        chunks=all_chunks,
        metadata=metadata,
        normalise=normalise,
        alpha=alpha,
        publication_types=selected_types if selected_types else []
    )

    if not results:
        return (
            "No relevant information found to verify this statement. "
            "Unable to determine truthfulness."
        )

    # If you only want to pass top-N results to the LLM:
    top_results = results[:max_sources]


    # 2. Build a context string with snippet text + sources
    #    Adjust the format as you prefer:
    source_map = {}  # Maps source # to (title, url)
    snippet_blocks = []

    for i, r in enumerate(top_results, start=1):
        source_map[f"#{i}"] = (r["title"], r["url"])  # Store for later lookup
        snippet_blocks.append(
            f"Source #{i}\n"
            f"Title: {r['title']}\n"
            f"URL: {r['url']}\n"
            f"Snippet: {r['snippet']}\n"
        )

    combined_context = "\n\n".join(snippet_blocks)

    # 3. Construct the prompt that tells ChatGPT how to respond
    #    We explicitly ask for references/citations at the end.
    system_instructions = (
        "You are a helpful AI that decides if a statement is true or false, "
        "and if false, corrects it using the provided sources. Cite sources clearly."
    )

    user_prompt = (
        "Determine if the following statement is true or false. If false, rewrite it truthfully.\n\n"
        "User Statement:\n"
        f"{extracted_text}\n\n"
        "Here are some relevant document snippets:\n"
        f"{combined_context}\n\n"
        "Based on the provided sources, please respond as follows:\n"
        "- Is the statement true or false?\n"
        "- If false, provide a corrected statement.\n"
        "- Cite the source(s) used in your reasoning, using their Source #.\n"
    )
    print(user_prompt)


    answer_1 = call_api(system_instructions, user_prompt)

    user_prompt_2 = (
        "You previously assessed the following statement and provided an answer.\n\n"
        "### User Statement:\n"
        f"{extracted_text}\n\n"
        "### Relevant Document Snippets:\n"
        f"{combined_context}\n\n"
        "### Your Previous Conclusion:\n"
        f"{answer_1}\n\n"
        "**Now, assign probabilities to the following categories (0% to 100%):**\n"
        "- Probability that the statement is **true**.\n"
        "- Probability that the statement is **false**.\n"
        "- Probability that the statement is **undecided** (i.e., the sources do not provide enough evidence).\n\n"
        "**Format your response exactly like this:**\n"
        "- Probability True: XX%\n"
        "- Probability False: XX%\n"
        "- Probability Undecided: XX%\n"
    )


    answer_2 = call_api(system_instructions, user_prompt_2)

    # Parse probabilities
    parsed_result = parse_llm_response(answer_2)

    # Replace source numbers with actual titles & URLs in the first response
    for source_key, (title, url) in source_map.items():
        answer_1 = answer_1.replace("Source " + source_key, f"[{title}]({url})")
        answer_1 = answer_1.replace("Source" + source_key, f"[{title}]({url})")
        answer_1 = answer_1.replace(source_key, f"[{title}]({url})")

    # Return the full structured response
    return {
        "statement_analysis": answer_1,
        "sources": source_map,
        "probability_true": parsed_result["probability_true"],
        "probability_false": parsed_result["probability_false"],
        "probability_undecided": parsed_result["probability_undecided"],
        "is_likely_true": parsed_result["is_likely_true"]
    }