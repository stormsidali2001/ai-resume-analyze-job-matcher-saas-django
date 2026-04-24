"""
infrastructure/search/indices.py

Index names and mapping definitions for jobs and resumes.
"""

JOBS_INDEX = "resumeai_jobs"
RESUMES_INDEX = "resumeai_resumes"
EMBEDDING_DIMS = 3072  # gemini-embedding-001 output size

JOBS_MAPPING = {
    "mappings": {
        "properties": {
            "job_id":                     {"type": "keyword"},
            "title":                      {"type": "text", "analyzer": "english"},
            "company":                    {"type": "keyword"},
            "description":                {"type": "text", "analyzer": "english"},
            "skills":                     {"type": "keyword"},
            "location":                   {"type": "text"},
            "employment_type":            {"type": "keyword"},
            "required_experience_months": {"type": "integer"},
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMS,
                "index": True,
                "similarity": "cosine",
            },
        }
    }
}

RESUMES_MAPPING = {
    "mappings": {
        "properties": {
            "resume_id":               {"type": "keyword"},
            "candidate_id":            {"type": "keyword"},
            "raw_text":                {"type": "text", "analyzer": "english"},
            "skills":                  {"type": "keyword"},
            "location":                {"type": "text"},
            "total_experience_months": {"type": "integer"},
            "embedding": {
                "type": "dense_vector",
                "dims": EMBEDDING_DIMS,
                "index": True,
                "similarity": "cosine",
            },
        }
    }
}
