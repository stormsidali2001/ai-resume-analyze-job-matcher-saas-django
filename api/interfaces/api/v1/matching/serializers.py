"""
interfaces/api/v1/matching/serializers.py

Serializers for the matching resource.
"""

from rest_framework import serializers


# ── Response serializers ───────────────────────────────────────────────────

class GapSerializer(serializers.Serializer):
    gap_type = serializers.CharField()
    description = serializers.CharField()


class SuggestionSerializer(serializers.Serializer):
    text = serializers.CharField()
    priority = serializers.CharField()
    category = serializers.CharField()


class MatchResultDTOSerializer(serializers.Serializer):
    match_id = serializers.CharField()
    resume_id = serializers.CharField()
    job_id = serializers.CharField()
    score = serializers.IntegerField()
    score_label = serializers.CharField()
    gaps = GapSerializer(many=True)
    suggestions = SuggestionSerializer(many=True)
    calculated_at = serializers.DateTimeField()


# ── Request serializers ────────────────────────────────────────────────────

class MatchRequestSerializer(serializers.Serializer):
    resume_id = serializers.CharField()
    job_id = serializers.CharField()
