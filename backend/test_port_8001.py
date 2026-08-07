import requests
import uuid
import os

BASE_URL = "http://localhost:8001/api/v1"
EMAIL = f"test_gen_{uuid.uuid4().hex[:8]}@example.com"
PASSWORD = "password123"

def check(label, res):
    if res.status_code == 200:
        print(f"  [PASS] {label}: 200 OK")
    else:
        print(f"  [FAIL] {label}: {res.status_code}")
        try:
            print(f"     {res.json()}")
        except Exception:
            print(f"     {res.text[:200]}")

def main():
    print(f"\n=== NEXUS EDU API TEST ===")
    print(f"Registering user: {EMAIL}")
    res = requests.post(f"{BASE_URL}/auth/register", json={
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": "Test Tester"
    })
    res.raise_for_status()

    print("Logging in...")
    res = requests.post(f"{BASE_URL}/auth/login", data={
        "username": EMAIL,
        "password": PASSWORD,
        "grant_type": "password"
    })
    res.raise_for_status()
    token = res.json()['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    print("Creating course...")
    res = requests.post(f"{BASE_URL}/courses", headers=headers, json={
        "name": "Genetics 101",
        "subject_area": "Biology",
        "academic_level": "Undergraduate"
    })
    res.raise_for_status()
    course_id = res.json()['data']['id']
    headers_ws = {**headers, "X-Workspace-ID": course_id}
    print(f"  Course ID: {course_id}")

    print("\nUploading genetics document...")
    file_path = "dummy_genetics.txt"
    with open(file_path, "rb") as f:
        res = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers_ws,
            files={"file": (os.path.basename(file_path), f, "text/plain")}
        )
    check("Document Upload", res)
    if res.status_code != 200:
        print("Upload failed. Stopping.")
        return
    print(f"  Chunks indexed: {res.json()['data'].get('chunks_indexed')}")

    print("\n--- Generation Endpoints ---")

    print("\n[1] Lecture Generation - DNA Replication")
    res = requests.post(f"{BASE_URL}/generate/lecture", headers=headers_ws, json={
        "topic": "DNA Replication",
        "additional_instructions": "Focus on the semiconservative model and template strand concept"
    })
    check("Lecture", res)

    print("\n[2] Summary Generation - Genetics Fundamentals")
    res = requests.post(f"{BASE_URL}/generate/summary", headers=headers_ws, json={
        "topic": "Fundamentals of Genetics and Heredity",
        "additional_instructions": "Highlight Mendel's contribution and gene function"
    })
    check("Summary", res)

    print("\n[3] Question Paper - Genetics (50 marks, mixed types)")
    res = requests.post(f"{BASE_URL}/generate/question-paper", headers=headers_ws, json={
        "topic": "Genetics: Heredity, DNA Replication, and Protein Synthesis",
        "additional_instructions": (
            "Generate a 50-mark paper with 3 sections: "
            "Section A (MCQs, 10 marks), "
            "Section B (Short Answer, 20 marks), "
            "Section C (Long Answer, 20 marks). "
            "Include questions on Mendel, DNA replication, and amino acid synthesis."
        )
    })
    check("Question Paper (50 marks)", res)
    if res.status_code == 200:
        paper = res.json()['data']
        print(f"  Total Marks: {paper.get('total_marks')}")
        print(f"  Sections: {[s['section_label'] for s in paper.get('sections', [])]}")

    print("\n[4] Presentation - Introduction to Genetics")
    res = requests.post(f"{BASE_URL}/generate/presentation", headers=headers_ws, json={
        "topic": "Introduction to Genetics and DNA",
        "additional_instructions": (
            "Create 6 slides covering: What is Genetics, Mendel's Laws, "
            "Gene Structure, DNA Replication, Protein Synthesis, and Summary. "
            "Use 'academic' theme."
        )
    })
    check("Presentation", res)
    if res.status_code == 200:
        ppt = res.json()['data']
        print(f"  Slide count: {ppt.get('slide_count')}")
        print(f"  Theme: {ppt.get('theme_suggestion')}")

    print("\n=== ALL TESTS COMPLETE ===\n")

if __name__ == "__main__":
    main()
