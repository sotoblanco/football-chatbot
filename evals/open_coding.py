# open coding

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.utils import get_agent_response

import pandas as pd 
from pathlib import Path
from typing import List, Dict

def get_open_coding_messages(df: pd.DataFrame) -> list:
    """
    Generate messages for open coding based on the provided DataFrame.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data to be processed.
        
    Returns:
        list: A list of message dictionaries formatted for the LLM.
    """
    messages = []
    for index, row in df.iterrows():
        messages.append({
            "role": "user",
            "content": f"Open code this data: {row.to_dict()}"
        })
    return messages

def open_coding(messages):
    response = get_agent_response(messages)
    return response

def open_coding_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform open coding on the provided DataFrame and return the results.
    
    Args:
        df (pd.DataFrame): DataFrame containing the data to be processed.
        
    Returns:
        pd.DataFrame: DataFrame with queries and open coding results.
    """
    results = []
    
    for index, row in df.iterrows():
        # Create message for this specific query
        messages = [{
            "role": "user",
            "content": f"Open code this football scouting query data: {row.to_dict()}"
        }]
        
        try:
            response = get_agent_response(messages)
            
            # Extract the assistant's response
            assistant_response = ""
            if isinstance(response, list):
                for res in response:
                    if res.get('role') == 'assistant':
                        assistant_response = res.get('content', '')
                        break
            elif isinstance(response, str):
                assistant_response = response
            
            # Store both query and response
            results.append({
                'query_id': row.get('id', f'Query_{index+1}'),
                'original_query': row.get('query', ''),
                'dimension_tuple_json': row.get('dimension_tuple_json', ''),
                'open_coding_response': assistant_response
            })
            
        except Exception as e:
            print(f"Error processing query {index+1}: {e}")
            results.append({
                'query_id': row.get('id', f'Query_{index+1}'),
                'original_query': row.get('query', ''),
                'dimension_tuple_json': row.get('dimension_tuple_json', ''),
                'open_coding_response': f"Error: {str(e)}"
            })
    
    return pd.DataFrame(results)

def open_coding_from_csv(file_path: str) -> pd.DataFrame:
    """
    Perform open coding on a CSV file and return the results as a DataFrame.
    
    Args:
        file_path (str): Path to the CSV file.
        
    Returns:
        pd.DataFrame: DataFrame with queries and open coding results.
    """
    df = pd.read_csv(file_path)
    return open_coding_df(df)

def main():
    # Example usage - use the synthetic queries CSV
    INPUT_CSV_PATH = Path(__file__).parent / "synthetic_queries_for_analysis.csv"
    OUTPUT_CSV_PATH = Path(__file__).parent / "open_coding_results.csv"

    # Check if input file exists
    if not INPUT_CSV_PATH.exists():
        print(f"Error: Input file not found at {INPUT_CSV_PATH}")
        print("Please run generate_synthetic_queries.py first to create the input data.")
        return

    print(f"Processing {INPUT_CSV_PATH}...")
    results_df = open_coding_from_csv(str(INPUT_CSV_PATH))
    
    # Display sample results
    print("\nSample Open Coding Results:")
    for idx, row in results_df.head(3).iterrows():
        print(f"\n--- Query {row['query_id']} ---")
        print(f"Original Query: {row['original_query']}")
        print(f"Open Coding Response: {row['open_coding_response'][:200]}...")
    
    # Save to CSV
    results_df.to_csv(OUTPUT_CSV_PATH, index=False)
    print(f"\nResults saved to {OUTPUT_CSV_PATH}")
    print(f"Total rows processed: {len(results_df)}")
    print(f"Columns in output: {list(results_df.columns)}")

if __name__ == "__main__":
    main()
