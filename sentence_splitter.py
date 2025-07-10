#!/usr/bin/env python3
import json
import re

def split_text_to_sentences(text):
    """
    Split text on periods and format as JSON with line numbers
    """
    # Split on periods and clean up each sentence
    sentences = text.split('.')
    
    # Clean up sentences - remove extra whitespace and empty strings
    cleaned_sentences = []
    for sentence in sentences:
        cleaned = sentence.strip()
        if cleaned:  # Only add non-empty sentences
            cleaned_sentences.append(cleaned)
    
    # Format as JSON with line numbers
    result = {
        "sentences": []
    }
    
    for i, sentence in enumerate(cleaned_sentences, 1):
        result["sentences"].append({
            "line": i,
            "text": sentence
        })
    
    return result

def main():
    # Read the raw transcript
    with open('Raw_transcript.json', 'r') as f:
        raw_text = f.read().strip()
    
    # Split into sentences
    sentences_json = split_text_to_sentences(raw_text)
    
    # Write to output file
    with open('Formatted_transcript.json', 'w') as f:
        json.dump(sentences_json, f, indent=2)
    
    print(f"✅ Processed {len(sentences_json['sentences'])} sentences")
    print("📄 Output saved to: Formatted_transcript.json")

if __name__ == "__main__":
    main()