import logging
from pathlib import Path
import re
from typing import List, Dict, Union

from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama, DeepInfra
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.prompts.example_selector import SemanticSimilarityExampleSelector
from langchain.vectorstores import Chroma

from db_action_handler import DBActionHandler

LOGGER = logging.getLogger("rag")
LOGGER.setLevel(logging.INFO)


class RAG:
    def __init__(self):
        self.model_name = "mistral"  # orca2 is best
        # self.llm = Ollama(model=self.model_name)
        self.llm = DeepInfra(model_id="mistralai/Mixtral-8x22B-Instruct-v0.1")
        self.llm.model_kwargs = {
            "temperature": 0.5,
            "repetition_penalty": 1.2,
            "max_new_tokens": 250,
            "top_p": 0.9,
        }
        embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")  # TODO experiment with other embeddings
        self.db_action_handler = DBActionHandler()

        # Load data and categories
        self.data = self.db_action_handler.get_all_notes()  # TODO just store data in vectors
        categories = self.db_action_handler.get_all_categories()

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
        # Load the vector store
        db_directory = Path("./chroma_categories")
        if db_directory.exists():
            self.db = Chroma(persist_directory=str(db_directory), embedding_function=embedding_function)
        else:
            db_directory.mkdir(parents=True, exist_ok=True)
            self.db = Chroma.from_texts(categories, embedding_function, persist_directory=str(db_directory))

        prefix_categorize = (
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
            prefix=prefix_categorize,
            suffix="Input: {note}\n",
            input_variables=["note", "candidate_categories"]
        )

    def predict(self, message: str) -> Dict[str, Union[str, float]]:
        # Returns twice the same category, that's why there's a set: if k=40, it returns 20
        candidate_categories = deduplicate_with_order_preservation(
            [doc.page_content for doc in self.db.similarity_search(message, k=40)]
        )
        candidate_categories_text = "\n".join(candidate_categories)
        whole_prompt = self.similar_prompt.format(note=message, candidate_categories=candidate_categories_text)
        LOGGER.info(whole_prompt)
        llm_output = self.llm(whole_prompt)
        LOGGER.info(f"llm output: {llm_output}")
        llm_output_post_processed = self.post_process_prediction(llm_output, message)
        LOGGER.info(f"llm output post processed: {llm_output_post_processed}")
        most_similar_existing_categories = [
            doc.page_content for doc in self.db.similarity_search(llm_output_post_processed, k=3)
        ]
        most_similar_existing_category = most_similar_existing_categories[0]
        LOGGER.info(f"Most similar existing category: {most_similar_existing_category}")
        # Combine the most similar existing category with the candidate categories
        # to manage two sources of possible errors
        categories_for_user_selection = self.get_categories_for_user_selection(
            most_similar_existing_categories, candidate_categories, llm_output_post_processed
        )

        print("most_similar_existing_categories: ", most_similar_existing_categories)
        print("categories_for_user_selection: ", categories_for_user_selection)
        return {
            "category": most_similar_existing_category,
            "categories_for_user_selection": categories_for_user_selection,
        }

    def get_categories_for_user_selection(
            self, most_similar_existing_categories,
            candidate_categories,
            llm_output_post_processed
    ) -> set:
        categories_for_user_selection = set(
            most_similar_existing_categories + candidate_categories[:3] + ["Note", llm_output_post_processed]
        )
        return categories_for_user_selection

    def post_process_prediction(self, prediction_text: str, message: str) -> str:
        if self.model_name.startswith("orca"):
            output_markers = ["### Final answer:", "Output:"]
            return extract_category_from_orca_output(prediction_text, output_markers)
        else:  # Llama2 or Mistral
            output_markers = ["Category:", "Output:"]
            return extract_category_from_llm_output(prediction_text, output_markers)

    def perform_arbitrary_query(self, query):
        """
        TODO:
        - try with deepinfra
        - (output a fixed amount of notes)
        - get ids of the notes and output notes with buttons
        - this should have access to categories, as some notes make sense only for me, and categories might contain some
        feedback from me
        - keep the comment from the LLM
        :param query:
        :return:
        """
        last_days = 60
        recent_thoughts = self.db_action_handler.get_recent_notes(time_frame=last_days)
        if not recent_thoughts:
            return "No notes found in the last {} days.".format(last_days)
        concat_recent_thoughts = "\n".join([
            f"Note: '{thought.note_text}', Category: '{thought.label}'" for thought in recent_thoughts
        ])
        arbitrary_query_prompt = (
            "Please review the following notes and respond with the most relevant ones to the provided query, "
            "preserving the original formatting of the notes. "
            "If there are no relevant notes, simply respond with 'No relevant notes'. "
            "Respond only with the relevant notes. Here's the query: '{}'\n\n"
            "Notes provided:\n{}\n\n"
        ).format(query, concat_recent_thoughts)
        LOGGER.debug(arbitrary_query_prompt)
        llm_output = self.llm(arbitrary_query_prompt)
        return llm_output


def extract_category_from_orca_output(text: str, triggers: List[str]) -> str:
    trigger_regex = '|'.join(map(re.escape, triggers))
    pattern = rf'({trigger_regex})(.*?)(?:\n|\.|$)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    if matches:
        return matches[-1][1].strip()
    return text


def extract_category_from_llm_output(text: str, triggers: List[str]) -> str:
    trigger_regex = '|'.join(map(re.escape, triggers))
    pattern = re.compile(rf'({trigger_regex})?\s*(.+?)(?:^[A-Za-z\s>,-]+|$)')
    if pattern.match(text.strip()):
        return pattern.match(text.strip()).group(2).strip()
    return text


def deduplicate_with_order_preservation(seq):
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]
