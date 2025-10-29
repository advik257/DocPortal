# Prepare prompt templates for various tasks

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate,MessagesPlaceholder

document_analysis_prompt = ChatPromptTemplate.from_template("""
                                          your highly intelligent AI assistant helps trained to analyze and summarize documents.
                                          return only valid json matching the exact schema provided.
                                          
                                          {format_instructions}
                                          
                                          Analyze this document
                                          
                                          {document_text}
                                          
                                          """)

document_comparison_prompt = ChatPromptTemplate.from_messages([
    
    
    SystemMessagePromptTemplate.from_template(
        """You are a professional document comparison expert. Your task is to analyze and compare documents, 
        providing output in a specific JSON format. Always ensure your response is valid JSON."""
    ),
    
    HumanMessagePromptTemplate.from_template(
        """Compare these documents and provide a detailed analysis:

{combined_documents}

Provide your analysis in the following JSON format:
{format_instructions}

Important:
1. Response must be ONLY valid JSON
2. Use double quotes for strings
3. Ensure all fields are present
4. Use proper array syntax for lists
5. Make sure the JSON is properly formatted and can be parsed"""
    )
])

# Prompt for answering based on context
context_qa_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are an assistant designed to answer questions using the provided context. Rely only on the retrieved "
        "information to form your response. If the answer is not found in the context, respond with 'I don't know.' "
        "Keep your answer concise and no longer than three sentences.\n\n{context}"
    )),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


# Prompt for contextual question rewriting
contextualize_question_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "Given a conversation history and the most recent user query, rewrite the query as a standalone question "
        "that makes sense without relying on the previous context. Do not provide an answer—only reformulate the "
        "question if necessary; otherwise, return it unchanged."
    )),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])




# central dictionries to register prompt types
PROMPT_REGISTRY = {
    "document_analysis": document_analysis_prompt,
    "document_comparison": document_comparison_prompt,
    "contextulize_question" : contextualize_question_prompt,
    "context_qa" : context_qa_prompt
}


