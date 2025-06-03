import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd
from litellm import completion
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from tqdm import tqdm

load_dotenv()

# --- Pydantic Models for Structured Output ---

class DimensionTuple(BaseModel):
    Country: str
    PlayerSkills: str
    Scenario: str

class QueryWithDimensions(BaseModel):
    id: str
    query: str
    dimension_tuple: DimensionTuple
    is_realistic_and_kept: int = 1
    notes_for_filtering: str = ""

class DimensionTupleList(BaseModel):
    tuples: List[DimensionTuple]

class QueriesList(BaseModel):
    queries: List[str]

# --- Configuration ---
MODEL_NAME = "anthropic/claude-3-haiku-20240307"
NUM_TUPLES_TO_GENERATE = 10  # Generate more tuples than needed to ensure diversity
NUM_QUERIES_PER_TUPLE = 5    # Generate multiple queries per tuple
OUTPUT_CSV_PATH = Path(__file__).parent / "synthetic_queries_for_analysis.csv"
MAX_WORKERS = 5  # Number of parallel LLM calls

def call_llm(messages: List[Dict[str, str]], response_format: Any) -> Any:
    """Call the LLM with the provided messages and return the response."""
    max_retries = 1
    for attempt in range(max_retries):
        try:
            response = completion(
                model=MODEL_NAME,
                messages=messages,
                response_format=response_format,
                stream=False
            )
            content = response.choices[0].message.content
            if content is None or content.strip() == "":
                raise ValueError("Received empty response from LLM.")
            return response_format(**json.loads(content))
        
        except Exception as e:
            if attempt == max_retries:
                raise e
            time.sleep(1) # wait before retry

def generate_dimension_tuples() -> List[DimensionTuple]:

    prompt = f"""Generate {NUM_TUPLES_TO_GENERATE} random combinations of (country, player skills, scenario) for a football scouting assistant.
The dimensions are:
Country: the players nationality. Possible values: Argentina, Brazil, Spain, Venezuela...
Player skills: specific skills for each player, that includes compare players with other current or past players. Possible values: A player similar to messi, A player with a good awarness, Strong defensive players in off-side systems
Scenario: how well-formed or challenging the query is.
Possible values:
• exact match (clearly specified and feasible),
• ambiguous request (unclear or underspecified),
• shouldn't be handled (invalid or out-of-scope).

Output each tuple in the format: (country, player skills, scenario)
Avoid duplicates. Vary values across dimensions. The goal is to create a diverse set of queries for our assistant.

Generate {NUM_TUPLES_TO_GENERATE} unique dimension tuples following these patterns. Remember to maintain balanced diversity across all dimensions.
"""
    messages = [{"role": "user", "content": prompt}]

    try:
        print("Generating dimension tuples in parallel...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for _ in range(5):
                futures.append(executor.submit(call_llm, messages, DimensionTupleList))
            
            # Wait for all to complete and collect results
            responses = []
            for future in futures:
                responses.append(future.result())
            
        # combine tuple and remove duplicates
        all_tuples = []
        for response in responses:
            print(response.tuples)
            all_tuples.extend(response.tuples)
        unique_tuples = []
        seen = set()

        for tup in all_tuples:
            tuple_str = tup.model_dump_json()
            if tuple_str not in seen:
                seen.add(tuple_str)
                unique_tuples.append(tup)

        print(f"Generated {len(unique_tuples)} unique dimension tuples.")
        return unique_tuples
    except Exception as e:
        print(f"Error generating dimension tuples: {e}")
        return []

def generate_queries_for_tuple(dimension_tuple: DimensionTuple) -> List[QueryWithDimensions]:

    prompt = f"""Generate {NUM_QUERIES_PER_TUPLE} realistic football scouting queries based on the following dimension tuple:{dimension_tuple.model_dump_json(indent=2)}
The queries should:
1. Sound like real users asking for scouting players
2. Naturally incorporate all the dimension values
3. Vary in style and detail level
4. Be realistic and practical
5. Include natural variations in typing style, such as:
   - Some queries in all lowercase
   - Some with random capitalization
   - Some with common typos
   - Some with missing punctuation
   - Some with extra spaces or missing spaces
   - Some with emojis or text speak

Generate {NUM_QUERIES_PER_TUPLE} unique queries that match the given dimensions, varying the text style naturally."""

    messages = [{"role": "user", "content": prompt}]
    
    try:
        response = call_llm(messages, QueriesList)
        return response.queries
    except Exception as e:
        print(f"Error generating queries for tuple: {e}")
        return []

def generate_queries_parallel(dimension_tuples: List[DimensionTuple]) -> List[QueryWithDimensions]:

    all_queries = []

    query_id = 1

    print(f"Generating {NUM_QUERIES_PER_TUPLE} queries each for {len(dimension_tuples)} dimension tuples in parallel...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_tuple = {
            executor.submit(generate_queries_for_tuple, dim_tuple): i
            for i, dim_tuple in enumerate(dimension_tuples)
        }

    # process complete generation as they finish
    with tqdm(total=len(dimension_tuples), desc="Generating Queries") as pbar:
        for future in as_completed(future_to_tuple):
            tuple_idx = future_to_tuple[future]
            try:
                queries = future.result()
                if queries:
                    for query_text in queries:
                        all_queries.append(QueryWithDimensions(
                                id=f"SYN{query_id:03d}",
                                query=query_text,
                                dimension_tuple=dimension_tuples[tuple_idx]
                            ))
                        query_id += 1
                pbar.update(1)
            except Exception as e:
                print(f"Tuple {tuple_idx + 1} generated an exception: {e}")
                pbar.update(1)
    return all_queries

def save_queries_to_csv(queries: List[QueryWithDimensions]):
    """Save generated queries to CSV using pandas."""
    if not queries:
        print("No queries to save.")
        return

    # Convert to DataFrame
    df = pd.DataFrame([
        {
            'id': q.id,
            'query': q.query,
            'dimension_tuple_json': q.dimension_tuple.model_dump_json(),
            'is_realistic_and_kept': q.is_realistic_and_kept,
            'notes_for_filtering': q.notes_for_filtering
        }
        for q in queries
    ])
    
    # Save to CSV
    df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"Saved {len(queries)} queries to {OUTPUT_CSV_PATH}")

def main():
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("Please set the ANTHROPIC_API_KEY environment variable.")
        return

    start_time = time.time()

    # Step 1: Generate dimension tuples
    print("Generating dimension tuples...")
    dimension_tuples = generate_dimension_tuples()
    if not dimension_tuples:
        print("No dimension tuples generated. Exiting.")
        return
    print(f"Generated {len(dimension_tuples)} dimension tuples.")

    # Step 2: Generate queries for each tuple in parallel
    print("Generating queries for each dimension tuple...")
    queries = generate_queries_parallel(dimension_tuples)

    if queries:
        save_queries_to_csv(queries)
        elapsed_time = time.time() - start_time
        print(f"Generated {len(queries)} queries in {elapsed_time:.2f} seconds.")
    else:
        print("failed to generate any queries")
if __name__ == "__main__":
    main()
            
