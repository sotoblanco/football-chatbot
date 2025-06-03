import gradio as gr
import pandas as pd
import json
from datetime import datetime

# Global variables
current_data = None
current_index = 0
annotations = {}

def load_data():
    """Load the open_coding results.csv file"""
    global current_data
    try:
        current_data = pd.read_csv('/home/pastor/projects/football_chatbot/evals/open_coding_results.csv')
        return f"✅ Loaded {len(current_data)} records successfully!"
    except FileNotFoundError:
        return "❌ File 'open_coding_results.csv' not found."
    except Exception as e:
        return f"❌ Error loading file: {str(e)}"

def get_current_record():
    """Get the current record to display"""
    global current_data, current_index
    if current_data is None or len(current_data) == 0:
        return "No data loaded", "", "", "", 0, 1
    
    if current_index >= len(current_data):
        current_index = len(current_data) - 1
    elif current_index < 0:
        current_index = 0
    
    record = current_data.iloc[current_index]
    
    # Get data from CSV columns
    query_id = record.get('query_id', 'N/A')
    original_query = record.get('original_query', 'N/A')
    dimension_tuple = record.get('dimension_tuple_json', '{}')
    response = record.get('open_coding_response', 'N/A')
    
    # Parse dimensions if it's JSON
    try:
        dimensions = json.loads(dimension_tuple)
        dimension_text = "\n".join([f"**{k}:** {v}" for k, v in dimensions.items()])
    except:
        dimension_text = dimension_tuple
    
    # Get existing annotation
    existing_annotation = annotations.get(current_index, "")
    
    # Create info text
    info_text = f"**Query ID:** {query_id}\n\n**Dimensions:**\n{dimension_text}"
    
    progress_percent = (current_index + 1) / len(current_data) * 100
    
    return original_query, response, info_text, existing_annotation, progress_percent, current_index + 1

def next_record():
    """Go to next record"""
    global current_index, current_data
    if current_data is not None and current_index < len(current_data) - 1:
        current_index += 1
    return get_current_record()

def prev_record():
    """Go to previous record"""
    global current_index
    if current_index > 0:
        current_index -= 1
    return get_current_record()

def jump_to_record(record_num):
    """Jump to specific record"""
    global current_index, current_data
    if current_data is None:
        return get_current_record()
    
    try:
        new_index = int(record_num) - 1
        if 0 <= new_index < len(current_data):
            current_index = new_index
    except:
        pass
    return get_current_record()

def save_annotation(annotation_text):
    """Save annotation for current record"""
    global current_index, annotations
    annotations[current_index] = annotation_text
    return f"💾 Saved annotation for record {current_index + 1}"

def export_annotations():
    """Export all annotations to CSV"""
    global current_data, annotations
    if current_data is None:
        return "❌ No data to export"
    
    # Add annotations to data
    export_data = current_data.copy()
    annotation_list = []
    for i in range(len(export_data)):
        annotation_list.append(annotations.get(i, ""))
    
    export_data['annotations'] = annotation_list
    export_data['annotation_timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"annotated_results_{timestamp}.csv"
    filepath = f"/home/pastor/projects/football_chatbot/evals/{filename}"
    
    try:
        export_data.to_csv(filepath, index=False)
        return f"✅ Exported to: {filename}"
    except Exception as e:
        return f"❌ Export failed: {str(e)}"

def get_stats():
    """Get annotation statistics"""
    global current_data, annotations
    if current_data is None:
        return "No data loaded"
    
    total = len(current_data)
    annotated = len([a for a in annotations.values() if a.strip()])
    progress = (annotated / total) * 100 if total > 0 else 0
    
    return f"📊 **Progress:** {annotated}/{total} ({progress:.1f}%)"

# Create Gradio interface
with gr.Blocks(title="Open Coding Annotation Tool") as app:
    
    gr.Markdown("# 🏈 Open Coding Annotation Tool")
    
    # Load section
    with gr.Row():
        load_btn = gr.Button("📁 Load Data", variant="primary")
        load_status = gr.Textbox(label="Status", interactive=False)
    
    # Navigation
    with gr.Row():
        with gr.Column(scale=2):
            progress_bar = gr.Slider(0, 100, value=0, label="Progress (%)", interactive=False)
        with gr.Column(scale=1):
            record_num = gr.Number(label="Record #", value=1, minimum=1)
            jump_btn = gr.Button("Go")
    
    with gr.Row():
        prev_btn = gr.Button("⬅️ Previous")
        next_btn = gr.Button("➡️ Next")
        stats_btn = gr.Button("📊 Stats")
    
    # Main content
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 🤔 Original Query")
            query_text = gr.Textbox(label="Query", lines=3, interactive=False)
            
            gr.Markdown("### 💬 Response")
            response_text = gr.Textbox(label="Response", lines=8, interactive=False)
            
            gr.Markdown("### 📋 Info")
            info_text = gr.Markdown("")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📝 Your Notes")
            annotation_box = gr.Textbox(
                label="Annotations", 
                lines=12,
                placeholder="Add your thoughts here...\n\n• Key themes\n• Quality assessment\n• Improvements needed\n• Notable patterns"
            )
            
            save_btn = gr.Button("💾 Save", variant="primary")
            save_status = gr.Textbox(label="Save Status", interactive=False, lines=1)
            
            stats_display = gr.Markdown("")
    
    # Export section
    with gr.Row():
        export_btn = gr.Button("📤 Export All Annotations", variant="primary")
        export_status = gr.Textbox(label="Export Status", interactive=False)
    
    # Event handlers
    load_btn.click(
        load_data,
        outputs=[load_status]
    ).then(
        get_current_record,
        outputs=[query_text, response_text, info_text, annotation_box, progress_bar, record_num]
    )
    
    next_btn.click(
        next_record,
        outputs=[query_text, response_text, info_text, annotation_box, progress_bar, record_num]
    )
    
    prev_btn.click(
        prev_record,
        outputs=[query_text, response_text, info_text, annotation_box, progress_bar, record_num]
    )
    
    jump_btn.click(
        jump_to_record,
        inputs=[record_num],
        outputs=[query_text, response_text, info_text, annotation_box, progress_bar, record_num]
    )
    
    save_btn.click(
        save_annotation,
        inputs=[annotation_box],
        outputs=[save_status]
    )
    
    stats_btn.click(
        get_stats,
        outputs=[stats_display]
    )
    
    export_btn.click(
        export_annotations,
        outputs=[export_status]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)