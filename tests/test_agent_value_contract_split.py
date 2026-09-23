from agent_dev_kit import agent_value, agent_value_contracts, agent_value_receipts


def test_agent_value_authorities_are_not_reexported() -> None:
    contract_names = (
        "CONTRACT_SCHEMA_VERSION",
        "MEASUREMENT_SCHEMA_VERSION",
        "load_contract",
        "validate_contract",
    )
    receipt_names = (
        "RECEIPT_SCHEMA_VERSION",
        "EvidenceVerifier",
        "validate_receipt",
    )

    for name in contract_names:
        assert hasattr(agent_value_contracts, name), name
        assert not hasattr(agent_value_receipts, name), name
        assert not hasattr(agent_value, name), name

    for name in receipt_names:
        assert hasattr(agent_value_receipts, name), name
        assert not hasattr(agent_value_contracts, name), name
        assert not hasattr(agent_value, name), name
