from dataclasses import dataclass

from autocana.data.config import load_user_config


@dataclass
class PrivateConfig:
    # only from 'config.yaml#private'
    address: str
    billing_address: str
    bank_account: str
    contract_number: str
    dev_contract: str
    email: str
    full_name: str
    phone_number: str
    vat: str

    @classmethod
    def load(cls, cfg_dict: dict | None = None) -> "PrivateConfig":
        private_cfg = cfg_dict if cfg_dict is not None else load_user_config()["private"]
        return cls(
            address=private_cfg["address"],
            billing_address=private_cfg.get("billing_address", private_cfg["address"]),
            bank_account=private_cfg["account"],
            contract_number=private_cfg["contract_number"],
            dev_contract=private_cfg["dev_contract"],
            email=private_cfg["email"],
            full_name=private_cfg["full_name"],
            phone_number=private_cfg["phone_number"],
            vat=private_cfg["vat"],
        )
