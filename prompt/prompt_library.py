# Prepare prompt templates for various tasks

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

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

PROMPT_REGISTRY = {
    "document_analysis": document_analysis_prompt,
    "document_comparison": document_comparison_prompt
}