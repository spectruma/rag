#demonstration of how to import a collection of embeddings into a Chroma db collection
#with RAG retrieval augmented generation, the embeddings are used to retrieve relevant documents
#chroma db is used to store the embeddings and the documents and their metadata
#the embeddings are generated using the ollama library
#the documents are read from a list of filenames in a text file
#the embeddings are generated in chunks of 7 sentences from the documents (feel free to change this)
#start the chroma db server before running this script
#chroma run --host localhost --port 8000 --path ../vectordb-stores/chromadb
#if you want to use a different model, change the embedmodel variable -> see config.ini
#the embeddings are stored in the collection ma-rag-embeddings and will always be created on startup
#if your data files are growing, you should consider preserving the collection and only adding new embeddings


import ollama, chromadb, time, glob, os
from utilities import readtext, getconfig
from mattsollamatools import chunk_text_by_sentences


def make_embeds(text, filename, collection, embedmodel):
  chunks = chunk_text_by_sentences(source_text=text, sentences_per_chunk=7, overlap=0 )
  print(f"with {len(chunks)} chunks")
  for index, chunk in enumerate(chunks):
    # here we decide using ollama to generate the embeddings or use the built-in model
    # of chroma db
    if embedmodel == "internal":
      collection.add([filename+str(index)], documents=[chunk], metadatas={"source": filename})
      print(".", end="", flush=True)      
    else:
      embed = ollama.embeddings(model=embedmodel, prompt=chunk)['embedding']
      print(".", end="", flush=True)
      collection.add([filename+str(index)], [embed], documents=[chunk], metadatas={"source": filename})
 

collectionname="ma-rag-embeddings"

chroma = chromadb.HttpClient(host="localhost", port=8000)
print(chroma.list_collections())
if any(collection.name == collectionname for collection in chroma.list_collections()):
  # ask the user if they want to delete the collection
  if input("collection already exists, do you want to delete it? (yes/no)") == "yes":
    print('deleting collection')  
    chroma.delete_collection(collectionname)
  else:
    print('update the collection')
      
collection = chroma.get_or_create_collection(name=collectionname, metadata={"hnsw:space": "cosine"})

embedmodel = getconfig()["embedmodel"]
starttime = time.time()
with open('sourcedocs-2.txt') as f:
  lines = f.readlines()
  for filename in lines:
    # remove trailing whitespace and newline characters
    filename = filename.replace(' \n', '')
    filename = filename.replace('\n', '')
    filename = filename.replace('%0A', '')
    # check if path is a comment or empty (comment is a line starting with #)
    if filename.startswith('#') or filename == "":
      continue
    
    # next, check if we have file wildcards and if yes, expand them
    # and read in the files that match the wildcards
    if filename.find('*') > -1:
      files = glob.glob(filename, recursive=True)
      print(f"Files: {list(files)}")
      for file in files:
        print(f"processing {file}")
        text = readtext(file)
        if text == "":
          continue
        make_embeds(text, file, collection, embedmodel)
    else:
      print(f"processing {filename}")  
      text = readtext(filename)
      if text == "":
        continue
      make_embeds(text, filename, collection, embedmodel)
        
    
print("--- %s seconds ---" % (time.time() - starttime))

