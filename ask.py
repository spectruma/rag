import ollama, sys, chromadb
from utilities import getconfig

embedmodel = getconfig()["embedmodel"]
mainmodel = getconfig()["mainmodel"]
chroma = chromadb.HttpClient(host="localhost", port=8000)
collection = chroma.get_or_create_collection("ma-rag-embeddings")

query = " ".join(sys.argv[1:])
if query == "":
  #query = "What are the possibilities a GDA650 ?"
  query = "Who won the most recent payling prize award in Oviedo?"
queryembed = ollama.embeddings(model=embedmodel, prompt=query)['embedding']

relevantdocs = collection.query(query_embeddings=[queryembed], n_results=1)["documents"][0]
docs = "\n\n".join(relevantdocs)
modelquery = f"{query} - Answer that question using the following text as a resource: {docs}"

stream = ollama.generate(model=mainmodel, prompt=modelquery, stream=True)

for chunk in stream:
  if chunk["response"]:
    print(chunk['response'], end='', flush=True)