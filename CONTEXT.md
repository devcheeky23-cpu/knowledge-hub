# Knowledge Hub — Domain Glossary

## Terms

### Knowledge Hub
The system. A RAG-based Q&A tool where developers upload project documents and ask questions in natural language. Every answer is grounded in uploaded Documents and carries a Citation. The system never draws on the model's general knowledge.

### Document
A file that has been uploaded to the Knowledge Hub and ingested — its content is chunked, embedded, and stored in the vector store. A Document has a name (`source_file`) and is made up of one or more Chunks. Calling it a "file" is acceptable only when referring to the upload action; once inside the system it is a Document.

### Chunk
A contiguous slice of a Document's text, produced by the chunker during ingestion. Each Chunk is embedded independently and stored in the vector store with metadata: `source_file`, `section_heading`, and `chunk_index`. The unit of retrieval — a Query returns Chunks, not whole Documents.

### Re-ingest
A full rebuild of the vector store: all existing Chunks are deleted, then every stored source file is run through the Ingestion pipeline from scratch. Triggered manually via a UI button. Needed because HF Spaces disk is ephemeral — the vector store is lost on cold start and must be rebuilt from committed source files.

### Section Heading
The heading of the section within a Document that a Chunk belongs to. Extracted from Markdown headings (`#`, `##`, etc.) during Ingestion. Stored as an empty string `""` when no heading exists (plain-text Documents, PDF pages without headings). The UI renders an empty Section Heading as "(no section)" — storage and display are separate concerns.

### Document Manager
The module responsible for listing, deleting, and retrieving the full text of Documents. Deleting a Document removes both its Chunks from the vector store and its original source file from storage — the Document is gone from the system entirely, not merely hidden from search. Retrieving full text lets a Citation resolve back to the whole source Document, not just the retrieved Chunk (PDF text is re-extracted on demand via the Ingestion parser).

### LLM Client
A thin, provider-agnostic module with one concern: send a prompt string, receive a response string. No knowledge of Chunks, Citations, Answer modes, or any domain concept. Provider and model are selected via config (env vars) — no code changes required to swap. The Answer Engine calls the LLM Client; the LLM Client knows nothing about the Answer Engine.

### Answer Engine
The module that orchestrates a full Question → Answer cycle: receives a Question, retrieves top-k Chunks via similarity search, assembles a prompt enforcing the answer contract, calls the LLM, and returns a structured Answer. Not a search engine (doesn't return raw results) — it returns a grounded Answer with Citations.

### Ingestion
The pipeline that takes a Document (file) and produces Chunks stored in the vector store. Steps: parse by file type → split into Chunks → embed each Chunk → store with metadata. "Ingest" (verb) means running this pipeline — distinct from "upload" which is just the file transfer step before Ingestion begins.

### Answer
The structured response the system returns for a Question. Always has a `mode` (Found / Abstain / Conflict), an `answer_text`, and a list of Citations. Never draws on the LLM's general knowledge — content is grounded in retrieved Chunks only.

### Found
An Answer mode. The retrieved Chunks contain sufficient information to answer the Question. Answer includes at least one Citation.

### Abstain
An Answer mode. The LLM judges that the retrieved Chunks do not contain enough information to answer the Question — either the topic is absent entirely, or the information is too incomplete to answer with confidence. The system states this explicitly rather than guessing. Citation list is empty. Abstention is the LLM's judgement from prompt instruction, not a similarity-score cutoff.

### Conflict
An Answer mode. Two or more retrieved Chunks address the same Question with contradictory information. The system presents both sides with their respective Citations and declines to choose between them. Conflict detection is limited to the retrieved top-k Chunks for the current Question — corpus-wide scanning is out of scope.

### Citation
A reference attached to an Answer pointing to the Chunk(s) used. Contains: `source_file`, `section_heading`, `chunk_text`. Enables the developer to verify the answer against the original Document.

### Question
The natural-language text a developer types into the chat UI. The raw input before any processing.

### Query
The text sent to the vector store for embedding similarity search. In the current implementation the Query is identical to the Question, but the distinction matters: future preprocessing (translation, reformulation) would transform a Question into a Query without changing the UI contract.
