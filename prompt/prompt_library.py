# Prepare prompt templates for various tasks

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

prompt = ChatPromptTemplate.from_template("""
                                          your highly intelligent AI assistant helps trained to analyze and summarize documents.
                                          return only valid json matching the exact schema provided.
                                          
                                          {fromat_instructions}
                                          
                                          Analyze this document
                                          
                                          {document_text}
                                          
                                          """)