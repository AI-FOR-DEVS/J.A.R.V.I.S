from groq import Groq

client = Groq()


def execute(prompt):
    completion = client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "system",
                "content": """
                    Strict adherence to these guidelines is crucial. Answer with maximal 1-2 sentences. 
                    When a request involves email-related tasks, you must invoke the 'fetch_emails' function.  
                    Don't invoke the methods if emails are already provided.
                    This action should be performed by returning the following structured command:
                    {
                        \"tool_calls\": [{\"name\": \"fetch_emails\"}]
                    }
                    Ensure that your response consists solely of this function call format, 
                    without any additional content, to facilitate accurate interpretation and execution.
                """
            },
        ],
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    response = ''
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""

    print(chunk.choices[0].delta.content or "")
    return response


if __name__ == "__main__":
    print(execute("Tell a joke"))
