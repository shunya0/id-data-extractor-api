import spacy
from flask import current_app

model_path = current_app.config['NER_MODEL_PATH']

# Load your custom spaCy NER model
# nlp = spacy.load(model_path)

# def ExtractEntities(accumulated_text):
#     # Use spaCy NER to identify entities
#     doc = nlp(accumulated_text.strip())
#     entities = []
#     for entity in doc.ents:
#         entities.append({"text": entity.text, "label": entity.label_})
#     print(entities)
#     return entities
