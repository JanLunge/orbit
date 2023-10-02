import random

# Define slot values
duration_values = ["1", "2", "3", "4", "5", "10", "15", "20", "25", "30"]
unit_values = ["second", "minute", "hour"]


# Template to actual data
def expand_template(template, intent):
    expanded_data = []
    for duration in duration_values:
        for unit in unit_values:
            # Generate the sentence
            sentence = template.replace("{duration}", duration).replace("{unit}", unit)

            # Generate the slot tags
            slots = []
            for word in sentence.split():
                if word == duration:
                    slots.append("B-duration")
                elif word == unit:
                    slots.append("B-unit")
                else:
                    slots.append("O")
            expanded_data.append((sentence, intent, " ".join(slots)))
    return expanded_data


# loop through each line in the intents.txt file
with open("intents.txt", "r") as f:
    for line in f:
        # Split the line into template and intent
        template, intent = line.strip().split("->")
# Generate expanded data
data = expand_template(template, intent)

# Save to CSV
with open("sequence_tags.csv", "w") as f:
    f.write("text,intent,slots\n")
    for item in data:
        f.write(f"{item[0]},{item[1]},{item[2]}\n")

print(f"Generated {len(data)} training samples in sequence_tags.csv!")
