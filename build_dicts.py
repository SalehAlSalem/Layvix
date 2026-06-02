"""Build compressed frequency dictionaries from raw frequency files."""
import json
import gzip
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def build_dict(raw_file, out_file, max_words=None):
    """Parse a 'word frequency' file and save as compressed JSON.gz."""
    freq_dict = {}
    count = 0
    
    with open(os.path.join(BASE_DIR, raw_file), "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                word = parts[0].strip()
                try:
                    freq = int(parts[1])
                except ValueError:
                    continue
                if word and freq > 0:
                    freq_dict[word] = freq
                    count += 1
                    if max_words and count >= max_words:
                        break
            elif len(parts) == 1 and parts[0].strip():
                freq_dict[parts[0].strip()] = 1
                count += 1
    
    out_path = os.path.join(BASE_DIR, out_file)
    start = time.time()
    with gzip.open(out_path, "wt", encoding="utf-8") as f:
        json.dump(freq_dict, f, ensure_ascii=False)
    elapsed = time.time() - start
    
    size_kb = os.path.getsize(out_path) // 1024
    print(f"  {out_file}: {len(freq_dict):,} words -> {size_kb:,} KB (compressed in {elapsed:.1f}s)")
    return freq_dict


def main():
    print("Building English frequency dictionary...")
    # All 333K words from Peter Norvig (Google Trillion Word Corpus)
    build_dict("en_freq_raw.txt", "en_freq.json.gz")
    
    print("Building Arabic frequency dictionary...")
    # Top 500K Arabic words from Wikipedia (2.5M is overkill for our use case)
    build_dict("ar_freq_raw.txt", "ar_freq.json.gz", max_words=500000)
    
    print("\nDone! Frequency dictionaries ready.")
    
    # Test loading speed
    print("\nTesting load speed...")
    start = time.time()
    with gzip.open(os.path.join(BASE_DIR, "en_freq.json.gz"), "rt", encoding="utf-8") as f:
        en = json.load(f)
    t1 = time.time() - start
    
    start = time.time()
    with gzip.open(os.path.join(BASE_DIR, "ar_freq.json.gz"), "rt", encoding="utf-8") as f:
        ar = json.load(f)
    t2 = time.time() - start
    
    print(f"  English: {len(en):,} words loaded in {t1:.2f}s")
    print(f"  Arabic: {len(ar):,} words loaded in {t2:.2f}s")
    print(f"  Lookup 'hello': {en.get('hello', 0):,}")
    print(f"  Lookup 'hi': {en.get('hi', 0):,}")
    print(f"  Lookup 'مرحبا': {ar.get('مرحبا', 0):,}")
    print(f"  Lookup 'السلام': {ar.get('السلام', 0):,}")


if __name__ == "__main__":
    main()
