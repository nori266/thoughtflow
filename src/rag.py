import logging
import re
from typing import List, Dict, Union

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma
import pandas as pd

from db_action_handler import DBActionHandler

LOGGER = logging.getLogger("rag")
LOGGER.setLevel(logging.INFO)


class RAG:
    def __init__(self):
        self.model_name = "orca2:13b"  # orca2 is best
        self.llm = Ollama(model=self.model_name)  # TODO switch to deepinfra llama. Is there orca in deepinfra?
        embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  # TODO experiment with other embeddings
        self.db_action_handler = DBActionHandler()

        # Load data and categories
        self.data = self.db_action_handler.get_all_notes()  # TODO just store data in vectors
        with open("data/category_paths.csv") as f:
            categories = pd.read_csv('data/category_paths.csv').show_category.tolist()

        self.examples = [
            {
                'input': row.note_text,
                'output': row.label,
            } for row in self.data
        ]
        self.prompt = PromptTemplate(
            input_variables=["input", "output"],
            template="Example input: {input},\nExample output: {output}"
        )
        self.example_selector = SemanticSimilarityExampleSelector.from_examples(
            self.examples,
            embeddings=embedding_function,
            vectorstore_cls=Chroma,
            k=5
        )
        # TODO check if db exists
        # self.db = Chroma.from_texts(categories, embedding_function, persist_directory="./chroma_categories")

        # load from disk
        self.db = Chroma(persist_directory="./chroma_categories", embedding_function=embedding_function)

        prefix = (
            "I want you to categorize my todo notes according to high-level goals and corresponding activities. "
            "If the input note is not a todo, assign it a category 'Note'. If there's no suitable category you can "
            "create a new one or use a higher-level category going up in the tree. Answer with the category ONLY, the "
            "most suitable one.\n"
            "Here are some candidate categories:\n{candidate_categories}\n\n"
            "Here are some examples:"
        )

        self.similar_prompt = FewShotPromptTemplate(
            example_selector=self.example_selector,
            example_prompt=self.prompt,
            prefix=prefix,
            suffix="Input: {note}\n",
            input_variables=["note", "candidate_categories"]
        )

    def predict(self, message: str) -> Dict[str, Union[str, float]]:
        # TODO why are there duplicates in sim search results?
        candidate_categories = {doc.page_content for doc in self.db.similarity_search(message, k=20)}
        candidate_categories_text = "\n".join(candidate_categories)
        whole_prompt = self.similar_prompt.format(note=message, candidate_categories=candidate_categories_text)
        LOGGER.info(whole_prompt)
        llm_output = self.llm(whole_prompt)
        LOGGER.info(f"llm output: {llm_output}")
        return self.post_process_prediction(llm_output, message)

    def post_process_prediction(self, prediction_text: str, message: str) -> Dict[str, Union[str, float]]:
        if self.model_name.startswith("orca"):
            output_markers = ["### Final answer:", "Output:"]
        else:  # Llama2
            output_markers = [message]
        return {
            "category": extract_trigger_phrases(prediction_text, output_markers),
        }


def extract_trigger_phrases(text: str, triggers: List[str]) -> str:
    trigger_regex = '|'.join(map(re.escape, triggers))
    pattern = rf'({trigger_regex})(.*?)(?:\n|\.|$)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        return matches[-1][1].strip()
    return text
