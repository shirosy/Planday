
import os
import random
import re
from datetime import datetime

from unsloth import FastLanguageModel
import datasets
import swanlab
from trl import GRPOConfig, GRPOTrainer


# To run this script, you first need to install the dependencies.
# You can do this by running the following command in your terminal:
# pip install unsloth==2025.7.8 vllm wandb typing_extensions datasets huggingface_hub swanlab

# Clean up previous runs
os.system("rm -rf outputs completion_samples")

# --- Load the original model ---
print("Loading the model...")
max_seq_length = 2048  # Can increase for longer reasoning traces
lora_rank = 32  # Larger rank = smarter, but slower

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="/root/autodl-tmp/model",  # 使用本地模型路径
    max_seq_length=max_seq_length,
    load_in_4bit=True,  # False for LoRA 16bit
    fast_inference=True,  # Enable vLLM fast inference
    max_lora_rank=lora_rank,
    gpu_memory_utilization=0.85,  # Reduce if out of memory
)

model = FastLanguageModel.get_peft_model(
    model,
    r=lora_rank,  # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],  # Remove QKVO if out of memory
    lora_alpha=lora_rank,
    use_gradient_checkpointing="unsloth",  # Enable long context finetuning
    random_state=3407,
)
print("Model loaded.")

# --- Dataset preparation ---
print("Preparing the dataset...")
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

ds = datasets.load_dataset("dataset_generation/generated_dataset", split="train")

ds = ds.map(
    lambda x: {
        "prompt": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT + x["prompt"]},
        ]
    }
)
print("Dataset prepared.")
print("Sample from dataset:", ds[0])


# --- Reward functions ---
# We use 3 reward functions:
# 1. Format reward: ensure the output is in the correct format. (10 points)
# 2. Sorted events reward: ensure the events are sorted in chronological order. (20 points)
# 3. Score reward: ratio between the total weighted duration of the events and the optimal score computed with dynamic programming. (70 points)

def minutes_to_time(minutes):
    """Convert minutes since midnight to time string."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"

def time_to_minutes(time_str):
    """Convert time string to minutes since midnight."""
    hours, mins = map(int, time_str.split(":"))
    return hours * 60 + mins



overall_pattern = r"<think>.+</think>.*<schedule>.*(<event>.*<name>.+</name>.*<start>\d{2}:\d{2}</start>.*<end>\d{2}:\d{2}</end>.*</event>)+.*</schedule>"
overall_regex = re.compile(overall_pattern, re.DOTALL)

capture_pattern = r"""
    <event>\s*
        <name>([^<]+)</name>\s*
        <start>(\d{2}:\d{2})</start>\s*
        <end>(\d{2}:\d{2})</end>\s*
    </event>
"""
capture_regex = re.compile(capture_pattern, re.VERBOSE)

def get_events(content):
    """Extract event information from XML-like content."""
    return [
        (match.group(1), match.group(2), match.group(3))
        for match in capture_regex.finditer(content)
    ]

def format_reward(prompts, completions, **kwargs):
    responses = [completion[0]["content"] for completion in completions]
    return [
        0.0 if not overall_regex.match(response) else 10.0 for response in responses
    ]

def score_reward(
    prompts, completions, events, priority_events, optimal_score, **kwargs
):
    scores = []
    responses = [completion[0]["content"] for completion in completions]

    for content, valid_events, priorities, opt_score in zip(
        responses, events, priority_events, optimal_score
    ):
        scheduled_events = get_events(content)
        existing_events = {
            ev for ev in scheduled_events if [ev[0], ev[1], ev[2]] in valid_events
        }

        if len(existing_events) < len(scheduled_events) or len(existing_events) < 2:
            scores.append(0.0)
            continue

        existing_events_minutes = [
            (ev[0], time_to_minutes(ev[1]), time_to_minutes(ev[2]))
            for ev in existing_events
        ]

        overlapping_events = set()
        for j in range(len(existing_events_minutes)):
            for k in range(j + 1, len(existing_events_minutes)):
                if (
                    existing_events_minutes[j][1] <= existing_events_minutes[k][2]
                    and existing_events_minutes[j][2] >= existing_events_minutes[k][1]
                ):
                    overlapping_events.add(existing_events_minutes[j])
                    overlapping_events.add(existing_events_minutes[k])
        if overlapping_events:
            scores.append(0.0)
            continue
        existing_events_minutes = [
            ev for ev in existing_events_minutes if ev not in overlapping_events
        ]

        score = sum(
            2 * (ev[2] - ev[1]) if ev[0] in priorities else ev[2] - ev[1]
            for ev in existing_events_minutes
        )
        scores.append((score / opt_score) * 70)

    if any(score > 0 for score in scores) and random.random() < 0.10:
        os.makedirs("completion_samples", exist_ok=True)
        log_file = os.path.join("completion_samples", "completion_samples.txt")
        with open(log_file, "a") as f:
            f.write("\\n\\n==============\\n")
            f.write(f"\\n{datetime.now().time()}\\n")
            f.write(f"{prompts[0]}\\n")
            f.write(f"{scores}\\n")
            f.write(f"{completions}")

    return scores

def sorted_events_reward(completions, **kwargs):
    scores = []
    responses = [completion[0]["content"] for completion in completions]

    for response in responses:
        scheduled_events = get_events(response)
        if len(scheduled_events) < 2:
            scores.append(0.0)
            continue

        scheduled_events_minutes = [
            (ev[0], time_to_minutes(ev[1]), time_to_minutes(ev[2]))
            for ev in scheduled_events
        ]

        if all(
            scheduled_events_minutes[i][1] < scheduled_events_minutes[i + 1][1]
            for i in range(len(scheduled_events_minutes) - 1)
        ):
            scores.append(20.0)
        else:
            scores.append(0)

    return scores

# --- Training configuration ---
print("Configuring training...")
tokenized_prompts = [
    tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True)
    for prompt in ds["prompt"]
]
exact_max_prompt_length = max(
    [len(tokenized_prompt) for tokenized_prompt in tokenized_prompts]
)

max_prompt_length = 448
new_model_id = "local-qwen-scheduler-7b-grpo"

training_args = GRPOConfig(
    learning_rate=8e-6,
    adam_beta1=0.9,
    adam_beta2=0.99,
    weight_decay=0.1,
    warmup_ratio=0.01,
    lr_scheduler_type="cosine",
    optim="paged_adamw_8bit",
    logging_steps=1,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=1,
    num_generations=8,
    max_prompt_length=max_prompt_length,
    max_completion_length=max_seq_length - max_prompt_length,
    max_grad_norm=0.1,
    report_to="none",
    output_dir="outputs",
    overwrite_output_dir=True,
    push_to_hub=False,
    save_strategy="steps",
    save_steps=50,
    save_total_limit=1,
    num_train_epochs=3,
)
print("Training configured.")

# Initialize SwanLab
# In a non-interactive script, you might need to log in beforehand
# or set environment variables for automatic authentication.
# For this conversion, we assume it can run non-interactively.
print("Initializing SwanLab...")
try:
    swanlab.init(
        project="GRPO-reboost",
        experiment_name="Qwen-Scheduler-GRPO",
        description="训练Qwen模型使用GRPO优化事件调度能力",
        config={
            "model": "Qwen2.5-Coder-7B-Instruct",
            "optimizer": "Adam",
            "learning_rate": 8e-6,
            "batch_size": 8,
            "num_epochs": 3
        }
    )
    print("SwanLab initialized.")
except Exception as e:
    print(f"Could not initialize SwanLab: {e}")
    print("Check if you are logged in or have networking issues.")


# --- Training! ---
print("Starting training...")
trainer = GRPOTrainer(
    model=model,
    processing_class=tokenizer,
    reward_funcs=[
        format_reward,
        sorted_events_reward,
        score_reward,
    ],
    args=training_args,
    train_dataset=ds,
)
trainer.train()

print("Training finished.")

# For more details on the training run, see the generated report:
# [Weights & Biases report](https://wandb.ai/stefanofiorucci/GRPO-reboost/reports/Qwen-Scheduler-GRPO--VmlldzoxMjI1MTA4MA?accessToken=p9whiiwc1ourpt1ae5hcs84un0ri117ty84m3c56kogvkm5drp5hnk9tanvlvrsn) 