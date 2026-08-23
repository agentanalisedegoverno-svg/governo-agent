"""Contrato estruturado entre o governador e o modelo de IA."""

ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "overall_risk": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low", "none"],
        },
        "decision": {
            "type": "string",
            "enum": ["pass", "pass_with_recommendations", "changes_required"],
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": [
                            "software_engineering",
                            "architecture",
                            "ai",
                            "cloud_infrastructure",
                            "security",
                            "data_governance",
                            "privacy",
                            "availability",
                            "cost",
                            "maintainability",
                            "compliance",
                        ],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["critical", "high", "medium", "low", "info"],
                    },
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "medium", "low"],
                    },
                    "evidence": {"type": "string"},
                    "impact": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "affected_files": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": [
                    "id",
                    "title",
                    "category",
                    "severity",
                    "confidence",
                    "evidence",
                    "impact",
                    "recommendation",
                    "affected_files",
                ],
            },
        },
        "architecture_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["proposed", "accepted", "deprecated", "superseded"],
                    },
                    "context": {"type": "string"},
                    "decision": {"type": "string"},
                    "consequences": {"type": "string"},
                },
                "required": ["title", "status", "context", "decision", "consequences"],
            },
        },
        "knowledge_updates": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "current_rule": {"type": "string"},
                    "external_change": {"type": "string"},
                    "impact": {"type": "string"},
                    "sources": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "recommended_policy_file": {"type": "string"},
                },
                "required": [
                    "title",
                    "current_rule",
                    "external_change",
                    "impact",
                    "sources",
                    "recommended_policy_file",
                ],
            },
        },
        "proposed_patches": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "title": {"type": "string"},
                    "rationale": {"type": "string"},
                    "unified_diff": {"type": "string"},
                },
                "required": ["title", "rationale", "unified_diff"],
            },
        },
    },
    "required": [
        "summary",
        "overall_risk",
        "decision",
        "findings",
        "architecture_decisions",
        "knowledge_updates",
        "proposed_patches",
    ],
}
