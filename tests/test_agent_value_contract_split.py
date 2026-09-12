from agent_dev_kit import agent_value, agent_value_contracts


def test_legacy_agent_value_validation_exports_are_stable() -> None:
    assert agent_value.CONTRACT_SCHEMA_VERSION == agent_value_contracts.CONTRACT_SCHEMA_VERSION
    assert agent_value.RECEIPT_SCHEMA_VERSION == agent_value_contracts.RECEIPT_SCHEMA_VERSION
    assert agent_value.MEASUREMENT_SCHEMA_VERSION == agent_value_contracts.MEASUREMENT_SCHEMA_VERSION
    assert agent_value.load_contract is agent_value_contracts.load_contract
    assert agent_value.validate_contract is agent_value_contracts.validate_contract
    assert agent_value.validate_receipt is agent_value_contracts.validate_receipt
