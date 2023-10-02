from flair.models import TextClassifier, SequenceTagger
from flair.data import Sentence

# Load the trained models
classifier = TextClassifier.load('./best-model.pt')
slot_tagger = SequenceTagger.load(
    './best-model.pt')  # Make sure to use different paths if storing in the same directory


def predict_intent_and_slots(text):
    sentence = Sentence(text)

    # Predict intent
    classifier.predict(sentence)
    intent = sentence.labels[0].value

    # Predict slots
    slot_tagger.predict(sentence)
    slots = [(entity.text, entity.tag) for entity in sentence.get_spans('slot')]

    return intent, slots


# Simple app interface
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        break
    intent, slots = predict_intent_and_slots(user_input)
    print(f"Predicted Intent: {intent}")
    print("Slots:")
    for slot in slots:
        print(f"- {slot[0]}: {slot[1]}")
