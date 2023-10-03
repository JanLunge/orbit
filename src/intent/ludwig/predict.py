# Intercept commands here
text = 'test'
def extract_slot_values(text, slots):
    slot_value = {}
    for slot in slots:
        slot_value[slot['slot_name']] = text[slot['start_pos']:slot['end_pos']]
    return slot_value
from ludwig.api import LudwigModel

# Load the trained model
model = LudwigModel.load("ludwig/results/experiment_run_26/model")

# Make predictions
data_to_predict = {
    'utterance': [text],
}
predictions = model.predict(data_to_predict)

print(predictions)

predictions_df = predictions[0]
intent_predictions = predictions_df['intent_predictions'].tolist()
slots_predictions = predictions_df['slots_predictions'].tolist()

for text, intent, slots in zip(data_to_predict['utterance'], intent_predictions, slots_predictions):
    slot_value = extract_slot_values(text, slots)
    print(f"Text: {text}\nIntent: {intent}\nSlot Value: {slot_value}\n")
