# backend/reset_db.py
import os
import shutil

print("🔄 Resetting all trace data...")

# Delete ChromaDB folder
chroma_path = "chroma_data"
if os.path.exists(chroma_path):
    shutil.rmtree(chroma_path)
    print(f"✓ Deleted {chroma_path}")

# Delete SQLite database files
for file in os.listdir("."):
    if file.endswith(".db"):
        os.remove(file)
        print(f"✓ Deleted {file}")

print("\n✅ All trace data cleared! Ready for demo.")
print("👉 Now restart your backend: python backend/app.py")
