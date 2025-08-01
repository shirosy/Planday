
import os
import re
import datasets
from unsloth import FastLanguageModel
from tqdm import tqdm
import torch

# --- Configuration ---
# This time, we point to the original base model, not the LoRA adapter.
BASE_MODEL_PATH = "/root/autodl-tmp/model" 
TEST_DATASET_PATH = "dataset_generation/generated_dataset"
MAX_SEQ_LENGTH = 2048

# --- Prompt Templates (copied from train_grpo.py) ---
SYSTEM_PROMPT = """You are a precise event scheduler.
1. First, reason through the problem inside <think> and </think> tags. Here you can create drafts, compare alternatives, and check for mistakes.
2. When confident, output the final schedule inside <schedule> and </schedule> tags. Your schedule must strictly follow the rules provided by the user."""

USER_PROMPT = """Task: create an optimized schedule based on the given events.
Rules:
- The schedule MUST be in strict chronological order. Do NOT place priority events earlier unless their actual start time is earlier.
- Event start and end times are ABSOLUTE. NEVER change, shorten, adjust, or split them.
- Priority events (weight = 2) carry more weight than normal events (weight = 1), but they MUST still respect chronological order.
- Maximize the sum of weighted event durations.
- No overlaps allowed. In conflicts, include the event with the higher weighted time.
- Some events may be excluded if needed to meet these rules.
You must use this format:  
<think>...</think>
<schedule>
<event>
<name>...</name>
<start>...</start>
<end>...</end>
</event>
...
</schedule>
---
"""

# --- Reward and Validation Functions (copied from train_grpo.py) ---
def time_to_minutes(time_str):
    hours, mins = map(int, time_str.split(":"))
    return hours * 60 + mins

overall_pattern = r"<think>.+</think>.*<schedule>.*(<event>.*<name>.+</name>.*<start>\d{2}:\d{2}</start>.*<end>\d{2}:\d{2}</end>.*</event>)+.*</schedule>"
overall_regex = re.compile(overall_pattern, re.DOTALL)
capture_pattern = r"<event>\s*<name>([^<]+)</name>\s*<start>(\d{2}:\d{2})</start>\s*<end>(\d{2}:\d{2})</end>\s*</event>"
capture_regex = re.compile(capture_pattern, re.VERBOSE)

def get_events(content):
    return [(m.group(1).strip(), m.group(2), m.group(3)) for m in capture_regex.finditer(content)]

def is_schedule_valid(completion, original_events):
    """
    Checks if a generated schedule is valid based on the user's criteria.
    """
    if not overall_regex.match(completion):
        return False, "format_invalid"

    scheduled_events = get_events(completion)
    
    if len(scheduled_events) < 2:
        return False, "too_few_events"

    original_event_set = {tuple(map(str.strip, e)) for e in original_events}
    scheduled_event_tuples = {tuple(map(str.strip, e)) for e in scheduled_events}
    if not scheduled_event_tuples.issubset(original_event_set):
        return False, "event_not_in_original_list"

    try:
        events_in_minutes = [(name, time_to_minutes(start), time_to_minutes(end)) for name, start, end in scheduled_events]
    except (ValueError, IndexError):
        return False, "time_format_error"

    for i in range(len(events_in_minutes) - 1):
        if events_in_minutes[i][1] >= events_in_minutes[i+1][1]:
            return False, "not_sorted"
    
    for i in range(len(events_in_minutes)):
        for j in range(i + 1, len(events_in_minutes)):
            if events_in_minutes[i][2] > events_in_minutes[j][1]:
                return False, "overlapping_events"
    
    return True, "valid"

def calculate_final_score(completion, original_events, priority_events, optimal_score):
    """
    Calculates the final score based on the new, stricter evaluation criteria.
    """
    is_valid, reason = is_schedule_valid(completion, original_events)
    
    if not is_valid:
        return 0.0

    # If valid, calculate the weighted duration
    scheduled_events = get_events(completion)
    events_in_minutes = [(name, time_to_minutes(start), time_to_minutes(end)) for name, start, end in scheduled_events]
    
    current_weighted_duration = sum(
        2 * (end - start) if name in priority_events else (end - start)
        for name, start, end in events_in_minutes
    )
    
    if optimal_score > 0:
        return (current_weighted_duration / optimal_score) * 100
    
    return 0.0

def main():
    print("Loading ORIGINAL BASE model...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL_PATH,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)
    print("Base model loaded.")

    print("Loading test dataset...")
    ds = datasets.load_dataset(TEST_DATASET_PATH, split="test")
    print(f"Test dataset loaded with {len(ds)} samples.")

    total_valid_schedules = 0
    total_score = 0.0
    
    print("Starting evaluation on BASE model...")
    for item in tqdm(ds, desc="Evaluating Base Model"):
        prompt_text = USER_PROMPT + item['prompt']
        full_prompt = tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt_text}],
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = tokenizer([full_prompt], return_tensors="pt").to("cuda")
        outputs = model.generate(**inputs, max_new_tokens=1500)
        completion = tokenizer.decode(outputs[0], skip_special_tokens=True).rpartition("assistant\n")[-1].strip()

        # Evaluate the completion
        score = calculate_final_score(completion, item['events'], item['priority_events'], item['optimal_score'])
        total_score += score
        
        if score > 0:
            total_valid_schedules += 1

    num_samples = len(ds)
    valid_schedules_percentage = (total_valid_schedules / num_samples) * 100 if num_samples > 0 else 0
    average_score = total_score / num_samples if num_samples > 0 else 0

    print("\n--- BASE MODEL Evaluation Results ---")
    print(f"Total samples evaluated: {num_samples}")
    print(f"Valid schedules (score > 0): {total_valid_schedules} ({valid_schedules_percentage:.2f}%)")
    print(f"Average Score: {average_score:.4f}")
    print("-----------------------------------")

if __name__ == "__main__":
    main()
