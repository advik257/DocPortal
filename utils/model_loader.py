import os
import sys
import json
from dotenv import load_dotenv
#load_dotenv()
from utils.config_loader import load_config
from logger.custom_logger import CustomLogger
from exception.custom_exception_archive import DocumentPortalException

#from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
#from langchain.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI


# intialize the logger
log = CustomLogger().get_logger(__file__)

class ApiKeyManager:
    REQUIRED_KEYS = ["GROQ_API_KEY", "GEMINI_API_KEY"]

    def __init__(self):
        self.api_keys = {}
        raw = os.getenv("API_KEYS")

        if raw:
            try:
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise ValueError("API_KEYS is not a valid JSON object")
                self.api_keys = parsed
                log.info("Loaded API_KEYS from ECS secret")
            except Exception as e:
                log.warning("Failed to parse API_KEYS as JSON", error=str(e))

        # Fallback to individual env vars
        for key in self.REQUIRED_KEYS:
            if not self.api_keys.get(key):
                env_val = os.getenv(key)
                if env_val:
                    self.api_keys[key] = env_val
                    log.info(f"Loaded {key} from individual env var")

        # Final check
        missing = [k for k in self.REQUIRED_KEYS if not self.api_keys.get(k)]
        if missing:
            log.error("Missing required API keys", missing_keys=missing)
            raise DocumentPortalException("Missing API keys", sys)

        log.info("API keys loaded", keys={k: v[:6] + "..." for k, v in self.api_keys.items()})


    def get(self, key: str) -> str:
        val = self.api_keys.get(key)
        if not val:
            raise KeyError(f"API key for {key} is missing")
        return val




class ModelLoader:
    """Class to load and manage models and embeddings."""
    
    def __init__(self):
        if os.getenv("ENV", "local").lower() != "production":
            load_dotenv()
            log.info("Running in LOCAL mode: .env loaded")
        else:
            log.info("Running in PRODUCTION mode")
        
        self.api_key_mgr = ApiKeyManager()
        self.config = load_config()
        log.info("YAML config loaded", config_keys=list(self.config.keys()))

        # load_dotenv()
        # self._validate_env()
        # self.config = load_config()
        # log.info("Configuration loaded successfully.", config_keys=list(self.config.keys()))
    
    # def _validate_env(self):
    #     """Validate required environment variables.Ensure API keys are exists."""
    #     required_vars = ["GROQ_API_KEY","GEMINI_API_KEY"]
    #     self.api_keys = {key: os.getenv(key) for key in required_vars}
    #     missing = [key for key, value in self.api_keys.items() if not value]
    #     if missing:
    #         log.error(f"Missing required environment variables: {missing}")
    #         raise DocumentPortalException(f"Missing required environment variables: {missing}")
    #     log.info("Environment variables validated successfully.", available_keys=[key for key in self.api_keys if self.api_keys[key]])
        
    def load_embeddings(self):
        """Load and return the embeddings model."""
        try:
            log.info("Loading embeddings model...")
            model_name =self.config["embedding_model"]["embedding_model_name"]
            log.info("Loading embeddings model returning...")
            return HuggingFaceEmbeddings(model_name=model_name)
             
        
        except Exception as e:
            log.error("Error loading embeddings model:", error = str(e))
            raise DocumentPortalException("Failed to Load Embedding model",sys)
        
    
    def load_llm(self):
         """Load the LLM Model. Load the LLM model based on the configuration dynamically."""
         llm_block = self.config["llm"]
         provider_key = os.getenv("LLM_PROVIDER","groq") # default to groq if not set
         
         if provider_key not in llm_block:
             log.error(f"Provider '{provider_key}' not found in configuration.")
             raise ValueError(f"Provider '{provider_key}' not found in configuration.")
         
         llm_config = llm_block[provider_key]
         provider = llm_config.get("provider")
         model_name = llm_config.get("model_name")
         temperature = llm_config.get("temperature", 0.2)
         max_tokens = llm_config.get("max_tokens", 2048)
         
         log.info(f"Loading LLM model from provider: {provider}, model: {model_name}" ,temperature=temperature, max_tokens=max_tokens)
         
         if provider == "groq":
             llm = ChatGroq(
                 model=model_name,
                 api_key=self.api_key_mgr.get("GROQ_API_KEY"),
                 temperature=temperature,
                 max_tokens=max_tokens
             )
             
             return llm
         
         elif provider == "gemini":
             llm = ChatGoogleGenerativeAI(
                 model=model_name,
                 api_key=self.api_key_mgr.get("GEMINI_API_KEY"),
                 temperature=temperature,
                 max_tokens=max_tokens
             )
             return llm
         
         else :
             log.error(f"Unsupported provider: {provider}")
             raise ValueError(f"Unsupported provider: {provider}")
        
        

if __name__ == "__main__":
    model_loader = ModelLoader()
    print("ModelLoader initialized successfully.")
       
    # Test loading embeddings
    embeddings = model_loader.load_embeddings()
    print(f"Embeddings model loaded:", embeddings)
    embedresult = embeddings.embed_query("Hello, how are you?")
    print(f"Embeddings result:", embedresult)
    
    #Test Model loading
    llm = model_loader.load_llm()
    print(f"LLM model loaded:",llm)
    result = llm.invoke("Hello, how are you?")
    print(f"LLM response:", result)