import logging
import re
import pandas as pd
from typing import List, Dict, Union

from langchain.embeddings import OllamaEmbeddings
from langchain.llms import Ollama
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma

LOGGER = logging.getLogger("rag")
LOGGER.setLevel(logging.INFO)


class RAG:
    def __init__(self):
        self.llm = Ollama(model="orca2:13b")  # TODO switch to deepinfra llama
        self.embedding_function = OllamaEmbeddings()  # TODO experiment with other embeddings

        # Load data and categories
        self.data = pd.read_csv("data/todos_with_categories.csv")  # TODO read from DB
        with open("data/category_paths.csv") as f:
            self.categories = f.read()  # TODO use only most similar categories

        self.examples = [
            {
                'input': row.todo,
                'output': row.category,
            } for _, row in self.data.iterrows()
        ]

        self.prompt = PromptTemplate(
            input_variables=["input", "output"],
            template="Example input: {input},\nExample output: {output}"
        )

        self.example_selector = SemanticSimilarityExampleSelector.from_examples(
            self.examples,
            embeddings=self.embedding_function,
            vectorstore_cls=Chroma,
            k=5
        )

        self.prefix = (
            "I want you to categorize my todo notes according to high-level goals and corresponding activities. "
            "If the input note is not a todo, assign it a category 'Note'. If there's no suitable category you can "
            "create a new one or use a higher-level category going up in the tree. Answer with the only one, most "
            "suitable category (write the whole tree path)."
        )

        self.similar_prompt = FewShotPromptTemplate(
            example_selector=self.example_selector,
            example_prompt=self.prompt,
            prefix=self.prefix,
            suffix="Input: {note}\n",
            input_variables=["note"]
        )

    def predict(self, message: str) -> Dict[str, Union[str, float]]:
        whole_prompt = self.similar_prompt.format(note=message)
        LOGGER.info(whole_prompt)
        llm_output = self.llm(whole_prompt)
        return self.post_process_prediction(llm_output)

    @staticmethod
    def post_process_prediction(prediction_text: str) -> Dict[str, Union[str, float]]:
        orca_output_markers = ["### Final answer:", "Output:"]
        return {
            "category": extract_trigger_phrases(prediction_text, orca_output_markers),
        }


def extract_trigger_phrases(text: str, triggers: List[str]) -> str:
    trigger_regex = '|'.join(map(re.escape, triggers))
    pattern = rf'({trigger_regex})(.*?)(?:\n|\.|$)'
    matches = re.findall(pattern, text)
    return matches[-1][1].strip()
