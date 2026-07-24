from pdf_chatbot.core import KnowledgeBase, chunk_text


def test_chunk_text_preserves_content_and_overlaps():
    text = "Sentence one. " * 100
    chunks = chunk_text(text, chunk_size=120, overlap=20)
    assert len(chunks) > 2
    assert all(chunk for chunk in chunks)


def test_search_ranks_relevant_source_first():
    knowledge_base = KnowledgeBase()
    knowledge_base.add_text("Saturn has prominent rings made of ice and rock.", "space.pdf", 3)
    knowledge_base.add_text("Pasta is commonly made from wheat flour and water.", "food.pdf", 7)
    result = knowledge_base.search("What are Saturn's rings made of?")[0]
    assert result.source == "space.pdf"
    assert result.page == 3


def test_answer_refuses_when_nothing_matches():
    knowledge_base = KnowledgeBase()
    knowledge_base.add_text("A document entirely about gardening and soil.")
    assert knowledge_base.answer("quantum chromodynamics")["citations"] == []

