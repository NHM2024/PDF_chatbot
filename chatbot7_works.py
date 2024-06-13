# -*- coding: utf-8 -*-
"""chatbot7_works.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1rMwnvgiChxxBEimy2cuYVZw5ZqW9z2MV
"""



import streamlit as st
import time
from typing import List, Optional
from openai import OpenAI

class PDFAssistant:
    """
    A class to interact with the OpenAI API to create an assistant for answering questions based on a PDF file.

    Attributes:
        client (OpenAI): Client for interacting with OpenAI API.
        assistant_id (Optional[str]): ID of the created assistant. None until an assistant is created.
    """
    def __init__(self, api_key: str) -> None:
        """
        Initializes the PDFAssistant with the provided API key.

        Args:
            api_key (str): OpenAI API key.
        """
        self.client = OpenAI(api_key=api_key)
        self.assistant_id: Optional[str] = None

    def upload_file(self, filename: str, model: str) -> None:
        """
        Uploads a file to the OpenAI API and creates an assistant related to that file.

        Args:
            filename (str): The path to the file to be uploaded.
            model (str): The name of the OpenAI model to use for the assistant.
        """
        file = self.client.files.create(
            file=open(filename, 'rb'),
            purpose="assistants"
        )

        assistant = self.client.beta.assistants.create(
            name="PDF Helper",
            instructions="You are my assistant who can answer questions from the given pdf. Provide equations where relevant. Provide the page number where the answer is taken from.",
            tools=[{"type": "retrieval"}],
            model=model,
            file_ids=[file.id]
        )
        self.assistant_id = assistant.id

    def get_answers(self, question: str) -> List[str]:
        """
        Asks a question to the assistant and retrieves the answers.

        Args:
            question (str): The question to be asked to the assistant.

        Returns:
            List[str]: A list of answers from the assistant.

        Raises:
            ValueError: If the assistant has not been created yet.
        """
        if self.assistant_id is None:
            raise ValueError("Assistant not created. Please upload a file first.")

        thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant_id
        )

        while True:
            run_status = self.client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            time.sleep(5)  # Reduce sleep time to 5 seconds
            if run_status.status == 'completed':
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                break
            else:
                time.sleep(2)

        return [message.content[0].text.value for message in messages.data if message.role == "assistant"]

# Function to prompt user for OpenAI API key
def prompt_for_api_key() -> str:
    api_key = st.text_input("Enter your OpenAI API key:", type="password")
    return api_key

# Function to upload PDF files
def upload_pdf_files() -> List[str]:
    uploaded_files = st.file_uploader("Upload PDF files", accept_multiple_files=True, type="pdf")
    if uploaded_files:
        filenames = []
        for file in uploaded_files:
            with open(file.name, "wb") as f:
                f.write(file.getvalue())
            filenames.append(file.name)
        return filenames
    else:
        return []

# Function to chat with assistant
def chat_with_assistant(client: PDFAssistant):
    filenames = upload_pdf_files()
    if not filenames:
        st.write("No PDF files uploaded. Please upload a PDF file.")
        return

    model = "gpt-3.5-turbo-1106"  # Use the 'davinci' model
    for filename in filenames:
        client.upload_file(filename, model)

    while True:
        question = st.text_input("Enter your question (or type 'exit' to quit):", key="question_input")
        if question.lower() in ['exit', 'quit']:
            break

        answers = client.get_answers(question)
        for answer in answers:
            st.write("Answer:", answer)

        break  # Terminate the loop after producing an output

# Main function
def main():
    st.title("PDF Assistant with OpenAI by NHM")

    # Prompt user for API key
    api_key = prompt_for_api_key()

    # Initialize PDFAssistant with the API key
    client = PDFAssistant(api_key)

    # Chat with assistant
    chat_with_assistant(client)

if __name__ == "__main__":
    main()