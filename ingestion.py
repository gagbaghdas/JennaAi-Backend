import os
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from fpdf import FPDF
from pypdf import PdfReader


def get_summary() -> None:
    if os.path.isfile("pdfs/summary.pdf"):
        reader = PdfReader("pdfs/summary.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    pdf_path = "pdfs/"
    loader = PyPDFDirectoryLoader(path=pdf_path)
    documents = loader.load()
    print(len(documents))

    llm = ChatOpenAI(temperature=0, model_name="gpt-4")
    chain = load_summarize_chain(llm, chain_type="refine", verbose=True)

    resutl = chain.run(documents)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=15)
    pdf.multi_cell(0, 10, resutl)
    pdf.output("pdfs/summary.pdf")

    return resutl
