from agent_dev_kit import agent_value, agent_value_contracts


def test_agent_value_contract_authority_is_not_reexported() -> None:
    for name in (
        "CONTRACT_SCHEMA_VERSION",
        "RECEIPT_SCHEMA_VERSION",
        "MEASUREMENT_SCHEMA_VERSION",
        "EvidenceVerifier",
        "load_contract",
        "validate_contract",
        "validate_receipt",
    ):
        assert hasattr(agent_value_contracts, name), name
        assert not hasattr(agent_value, name), name
